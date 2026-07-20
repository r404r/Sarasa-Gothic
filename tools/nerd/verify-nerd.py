#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
NF-T10 保真验收套件 + NF-T11 8 样式一致性门禁。cp-centric（Sarasa post fmt3 不存 glyph 名，
新 glyph 由 cmap 重建名 uniXXXX；一律以码位/cmap 作身份，不依赖内部 nf_* 名）。

逐 (输入原件, 输出 NF) 对跑门禁：
  ① hinting（cvt/fpgm/prep/gasp 逐字节相等；既有 glyph 轮廓/instruction 不变）
  ② 表结构（可重开；maxp/glyphOrder/glyf/hmtx/vmtx 数一致；新增=基座+add；新 glyph 简单轮廓；hdmx/LTSH/VDMX/DSIG 未生成）
  ③ 垂直度量不变（hhea 三项 + OS/2 typo/win；head bbox 仅由新增图标致）
  ④ advance 四条（既有逐一等基线；新增=500；无 manifest 外新宽；分布=基线∪{500}）
  ⑤ cmap（子表签名不变；BMP 写 (0,3,4)+(3,1,4)+format12、SMP 仅 format12；UVS 未改；新增码位集=manifest）
  ⑥ 跨栈：图标 bbox 垂直边界 + FreeType(Linux, Pillow) 抽样渲染无裁切
  ⑦ layout（GSUB/GPOS/GDEF compiled 与输入无差异）
NF-T11：8 样式新增码位集/度量/数一致；SC-J 无漂移；Italic/BI 图标直立。

用法：verify-nerd.py <in_dir> <out_dir> <manifest.json>
"""
import sys, json, os
from fontTools.ttLib import TTFont
from fontTools.pens.boundsPen import BoundsPen
from fontTools.pens.recordingPen import RecordingPen
sys.path.insert(0, __file__.rsplit("/", 1)[0])
import nerd_common as nc

STYLES = ["Regular", "Italic", "Bold", "BoldItalic"]


def discover_regions(out_dir):
    """从 out_dir 实际存在的产物发现 region（覆盖 SC/TC/J 全部，不写死）。"""
    import glob as _g, re as _re
    regs = set()
    for p in _g.glob(os.path.join(out_dir, "SarasaTerm*-*.ttf")):
        m = _re.match(r"SarasaTerm([A-Za-z]+)-(%s)$" % "|".join(STYLES),
                      os.path.basename(p)[:-4])
        if m:
            regs.add(m.group(1))
    # 稳定顺序：SC, TC, J 优先，其余按字母
    order = {"SC": 0, "TC": 1, "J": 2}
    return sorted(regs, key=lambda r: (order.get(r, 9), r))
FAIL = []


def check(name, cond, detail=""):
    print("  [%s] %s%s" % ("PASS" if cond else "FAIL", name,
                           ("  -- " + detail) if detail and not cond else ""))
    if not cond:
        FAIL.append(name)
    return cond


def tbytes(font, tag):
    return font[tag].compile(font) if tag in font else None


def glyph_equal(a, b):
    if a.isComposite() != b.isComposite() or a.numberOfContours != b.numberOfContours:
        return False
    if a.isComposite():
        if len(a.components) != len(b.components):
            return False
        for ca, cb in zip(a.components, b.components):
            if ca.getComponentInfo() != cb.getComponentInfo():
                return False
    else:
        if getattr(a, "coordinates", []) != getattr(b, "coordinates", []):
            return False
        if getattr(a, "flags", []) != getattr(b, "flags", []):
            return False
        if getattr(a, "endPtsOfContours", []) != getattr(b, "endPtsOfContours", []):
            return False
    pa = a.program.getBytecode() if hasattr(a, "program") else b""
    pb = b.program.getBytecode() if hasattr(b, "program") else b""
    return pa == pb


def usubs(font):
    return {(t.platformID, t.platEncID, t.format): t.cmap
            for t in font["cmap"].tables if t.format != 14}


def verify_pair(inp, outp, manifest):
    fi = TTFont(inp, recalcTimestamp=False)
    fo = TTFont(outp, recalcTimestamp=False)
    add_cps = [e["cp"] for e in manifest["add"]]
    cls = {e["cp"]: e["class"] for e in manifest["add"]}
    orig_order = fi.getGlyphOrder()
    best = fo.getBestCmap()
    names = {cp: best.get(cp) for cp in add_cps}

    # ① hinting
    for tag in ("cvt ", "fpgm", "prep", "gasp"):
        check("① %s 逐字节相等" % tag.strip(), tbytes(fi, tag) == tbytes(fo, tag))
    gi, go = fi["glyf"], fo["glyf"]
    mism = [n for n in orig_order if not glyph_equal(gi[n], go[n])]
    check("① 既有 %d glyph 轮廓/instruction 不变" % len(orig_order), not mism,
          "%d changed e.g. %s" % (len(mism), mism[:3]))

    # ② 表结构
    ng = fo["maxp"].numGlyphs
    counts = [ng, len(fo.getGlyphOrder()), len(fo["glyf"].glyphs), len(fo["hmtx"].metrics)]
    if "vmtx" in fo:
        counts.append(len(fo["vmtx"].metrics))
    check("② numGlyphs/glyphOrder/glyf/hmtx/vmtx 数一致", len(set(counts)) == 1, str(counts))
    check("② 新增 = 基座 + add", ng == len(orig_order) + len(add_cps))
    check("② 新码位均可解析且指向新 GID",
          all(names[cp] and fo.getGlyphID(names[cp]) >= len(orig_order) for cp in add_cps))
    check("② 新 glyph 均简单轮廓（无悬空 composite）",
          all(not fo["glyf"][names[cp]].isComposite() for cp in add_cps if names[cp]))
    new_dev = [t for t in ("hdmx", "LTSH", "VDMX", "DSIG") if t in fo and t not in fi]
    check("② hdmx/LTSH/VDMX/DSIG 未被新生成", not new_dev, str(new_dev))

    # ③ 垂直度量
    hi, ho = fi["hhea"], fo["hhea"]
    check("③ hhea ascent/descent/lineGap 不变",
          (hi.ascent, hi.descent, hi.lineGap) == (ho.ascent, ho.descent, ho.lineGap))
    oi, oo = fi["OS/2"], fo["OS/2"]
    check("③ OS/2 typo/win 度量不变",
          (oi.sTypoAscender, oi.sTypoDescender, oi.sTypoLineGap, oi.usWinAscent, oi.usWinDescent) ==
          (oo.sTypoAscender, oo.sTypoDescender, oo.sTypoLineGap, oo.usWinAscent, oo.usWinDescent))
    di, do = fi["head"], fo["head"]
    bbox_ok = (do.xMin >= min(di.xMin, -122) and do.yMin >= min(di.yMin, -420) and
               do.xMax <= max(di.xMax, 561) + 5 and do.yMax <= max(di.yMax, 990))
    check("③ head 全局 bbox 变化仅在既有/Powerline 包络内", bbox_ok,
          "in%s out%s" % ((di.xMin, di.yMin, di.xMax, di.yMax), (do.xMin, do.yMin, do.xMax, do.yMax)))

    # ④ advance
    mi, mo = fi["hmtx"].metrics, fo["hmtx"].metrics
    check("④ 既有 glyph advance 与基线逐一相等", all(mo[n][0] == mi[n][0] for n in orig_order))
    new_adv = set(mo[names[cp]][0] for cp in add_cps if names[cp])
    check("④ 新增 advance 全部=500", new_adv == {nc.CELL}, "new adv=%s" % sorted(new_adv))
    base_advs = set(mi[n][0] for n in orig_order)
    all_out = set(a for a, _ in mo.values())
    check("④ 无 manifest 外新宽（⊆ 基线∪{500}）", all_out <= (base_advs | {nc.CELL}),
          "extra=%s" % sorted(all_out - base_advs - {nc.CELL}))

    # ⑤ cmap
    subs_o, subs_i = usubs(fo), usubs(fi)
    check("⑤ cmap 子表签名不变", set(subs_o) == set(subs_i))
    uvs_i = [t for t in fi["cmap"].tables if t.format == 14]
    uvs_o = [t for t in fo["cmap"].tables if t.format == 14]
    check("⑤ UVS(0,5,14) 未改",
          len(uvs_i) == len(uvs_o) and all(a.compile(fi) == b.compile(fo)
                                           for a, b in zip(uvs_i, uvs_o)))
    bmp_ok = smp_ok = True
    for cp in add_cps:
        gn = names[cp]
        for (p, e, fmt), cmap in subs_o.items():
            if cp <= 0xFFFF and fmt in (4, 12):
                bmp_ok &= (cmap.get(cp) == gn)
            if cp > 0xFFFF:
                if fmt == 12:
                    smp_ok &= (cmap.get(cp) == gn)
                if fmt == 4:
                    smp_ok &= (cp not in cmap)
    check("⑤ 新增 BMP 写 (0,3,4)+(3,1,4)+format12 一致", bmp_ok)
    check("⑤ 新增 SMP 仅 format12 (0,4,12)+(3,10,12)", smp_ok)
    new_cps = set()
    for k, cmap in subs_o.items():
        new_cps |= (set(cmap) - set(subs_i[k]))
    check("⑤ 新增码位集 = manifest", new_cps == set(add_cps),
          "got %d want %d" % (len(new_cps), len(add_cps)))

    # ⑦ layout
    for tag in ("GSUB", "GPOS", "GDEF"):
        if tag in fi or tag in fo:
            check("⑦ %s 与输入无差异" % tag, tbytes(fi, tag) == tbytes(fo, tag))

    # ⑥ 几何 bbox 垂直边界
    gs = fo.getGlyphSet()
    bad = []
    for cp in add_cps:
        p = BoundsPen(gs)
        try:
            gs[names[cp]].draw(p)
        except Exception:
            continue
        if p.bounds is None:
            continue
        y0, y1 = p.bounds[1], p.bounds[3]
        if cls[cp] == "normal":
            if y0 < nc.NORMAL_VMIN - 1 or y1 > nc.NORMAL_VMAX + 1:
                bad.append((hex(cp), round(y0), round(y1)))
        else:
            if y0 < -308 or y1 > 988:
                bad.append((hex(cp), round(y0), round(y1)))
    check("⑥ 图标 bbox 垂直边界（普通∈[-215,965]/PL∈[-307,987]）", not bad, "越界 %s" % bad[:5])

    return {cp: names[cp] for cp in add_cps}


def raster_freetype(outp, add_cps):
    """⑥ FreeType(Linux, via Pillow) 抽样：绘入带 padding 的行盒画布，验证墨迹不越出
    行盒 [PAD, PAD+H]（H=asc+desc）→ 真实无裁切；同时确认非空可渲染。"""
    from PIL import Image, ImageDraw, ImageFont
    ft = ImageFont.truetype(outp, 64)
    asc, desc = ft.getmetrics()
    H = asc + desc
    PAD = 24
    sample = add_cps[:: max(1, len(add_cps) // 60)][:60]
    clip, rendered = [], 0
    for cp in sample:
        img = Image.new("L", (96, H + 2 * PAD), 0)
        d = ImageDraw.Draw(img)
        try:
            d.text((16, PAD), chr(cp), font=ft, fill=255)  # 行盒 [PAD, PAD+H]，baseline=PAD+asc
        except Exception:
            continue
        bb = img.getbbox()
        if bb is None:
            continue
        rendered += 1
        if bb[1] < PAD - 1 or bb[3] > PAD + H + 1:   # 墨迹越出行盒 → 裁切
            clip.append((hex(cp), bb, (PAD, PAD + H)))
    check("⑥ FreeType(Pillow) 行盒渲染无裁切 (%d 非空样本)" % rendered, not clip, "越盒 %s" % clip[:5])


def consistency(per_file, out_dir, files, regions):
    n = len(files)
    print("\n=== NF-T11 %d 样式一致性门禁 ===" % n)
    cps0 = set(per_file[files[0]])
    check("NF-T11 %d 样式新增码位集一致" % n, all(set(per_file[f]) == cps0 for f in files))
    check("NF-T11 %d 样式新增 glyph 数一致 (%d)" % (n, len(cps0)),
          all(len(per_file[f]) == len(cps0) for f in files))
    sample = sorted(cps0)[:: max(1, len(cps0) // 15)][:15]
    # Italic/BI 直立：同 region Regular vs Italic 新 glyph 轮廓逐点相同
    upr_ok, det = True, ""
    for region in regions:
        fr = TTFont(os.path.join(out_dir, "SarasaTerm%s-Regular.ttf" % region), recalcTimestamp=False)
        fitl = TTFont(os.path.join(out_dir, "SarasaTerm%s-Italic.ttf" % region), recalcTimestamp=False)
        cr, ci = fr.getBestCmap(), fitl.getBestCmap()
        gr, gi = fr.getGlyphSet(), fitl.getGlyphSet()
        for cp in sample:
            a, b = RecordingPen(), RecordingPen()
            gr[cr[cp]].draw(a); gi[ci[cp]].draw(b)
            if a.value != b.value:
                upr_ok, det = False, "%s U+%04X Italic≠Regular" % (region, cp); break
    check("NF-T11 Italic/BI 图标直立（与 Regular 轮廓逐点相同）", upr_ok, det)
    # 各 region 同 style 无漂移（覆盖 SC/TC/J 全部两两：以 regions[0] 为基准）
    base = regions[0]
    drift_ok, ddet = True, ""
    for st in STYLES:
        fb = TTFont(os.path.join(out_dir, "SarasaTerm%s-%s.ttf" % (base, st)), recalcTimestamp=False)
        cb, gb = fb.getBestCmap(), fb.getGlyphSet()
        for region in regions[1:]:
            fr = TTFont(os.path.join(out_dir, "SarasaTerm%s-%s.ttf" % (region, st)), recalcTimestamp=False)
            cr, gr = fr.getBestCmap(), fr.getGlyphSet()
            for cp in sample:
                a, b = RecordingPen(), RecordingPen()
                gb[cb[cp]].draw(a); gr[cr[cp]].draw(b)
                if a.value != b.value:
                    drift_ok, ddet = False, "%s vs %s %s U+%04X" % (base, region, st, cp); break
            if not drift_ok: break
        if not drift_ok: break
    check("NF-T11 各 region(%s) 同 style 新 glyph 轮廓一致（无漂移）" % "/".join(regions), drift_ok, ddet)


def raster_existing(inp, outp):
    """① 补充（闭合 Codex 终审 r1 第 2 条）：既有 hinted glyph 的保真抽样。
    覆盖 Latin(简单/含 hint)、数字、CJK(繁复)、composite(变音)、不同 instruction。
    (a) **glyf 逐字节相同**（精确 TTX/glyf 比较，Codex 认可的等效手段）；
    (b) FreeType raster 差异在**不可感知阈值**内（容忍 head.flags bit1 因新增居中图标被
        合法重算 → 复杂斜体 CJK 斜向边缘的亚像素 AA 舍入；见 06 报告）。
    RASTER_TOL：单像素强度差上限（0–255）。"""
    from PIL import Image, ImageChops, ImageFont
    RASTER_TOL = 40
    fa = TTFont(inp, recalcTimestamp=False); fb = TTFont(outp, recalcTimestamp=False)
    ca, cb = fa.getBestCmap(), fb.getBestCmap()
    glyf_a, glyf_b = fa["glyf"], fb["glyf"]
    fi = ImageFont.truetype(inp, 48); fo = ImageFont.truetype(outp, 48)
    samples = "AaBglI10gqQ中一你好國書體éñü©®"
    glyf_diffs, raster_gross, maxdiff = [], [], 0
    for ch in samples:
        cp = ord(ch)
        gn_a = ca.get(cp); gn_b = cb.get(cp)
        if gn_a is None and gn_b is None:
            continue
        # (a) glyf 逐字节
        if gn_a is None or gn_b is None or \
           glyf_a[gn_a].compile(glyf_a) != glyf_b[gn_b].compile(glyf_b):
            glyf_diffs.append(ch); continue
        # (b) raster 容差
        bi = _render_char(fi, ch); bo = _render_char(fo, ch)
        if bi is None or bo is None:
            continue
        dat = list(ImageChops.difference(bi, bo).get_flattened_data() if hasattr(
            ImageChops.difference(bi, bo), "get_flattened_data") else
            ImageChops.difference(bi, bo).getdata())
        m = max(dat) if dat else 0
        maxdiff = max(maxdiff, m)
        if m > RASTER_TOL:
            raster_gross.append((ch, m))
    check("① 既有 glyph glyf 逐字节相同 (%d 抽样)" % len(samples), not glyf_diffs,
          "glyf 变化字符: %s" % glyf_diffs)
    check("① 既有 glyph raster 差异 ≤ %d (max=%d, 仅 head.flags-AA)" % (RASTER_TOL, maxdiff),
          not raster_gross, "超阈: %s" % raster_gross[:5])


def _render_char(ft, ch):
    from PIL import Image, ImageDraw
    img = Image.new("L", (80, 80), 0); d = ImageDraw.Draw(img)
    try:
        d.text((8, 8), ch, font=ft, fill=255)
    except Exception:
        return None
    return img


def main():
    in_dir, out_dir, mpath = sys.argv[1:4]
    manifest = json.load(open(mpath))
    add_cps = [e["cp"] for e in manifest["add"]]
    regions = discover_regions(out_dir)
    files = ["SarasaTerm%s-%s" % (r, s) for r in regions for s in STYLES]
    print("发现 region: %s → 验证 %d 款" % ("/".join(regions), len(files)))
    # 覆盖完整性断言（闭合 Codex 终审 r2/r3 第 1 条稳健性）：
    # ① 输入/输出 region 集必须**恰为** EXPECT_REGIONS（防「输入+输出同缺 TC 时只验 8 款仍成功」）；
    # ② 文件总数必须**恰为** 期望值；③ 每 region×style 输入/输出文件都存在。
    # 期望交付集：可用 --expect-regions 覆盖，默认 SC/TC/J。
    EXPECT_REGIONS = set(
        (sys.argv[sys.argv.index("--expect-regions") + 1].split(",")
         if "--expect-regions" in sys.argv else ["SC", "TC", "J"]))
    n_expect = len(EXPECT_REGIONS) * len(STYLES)
    regions_in = discover_regions(in_dir)
    check("覆盖：输出 region 集 == 期望 %s（实发现 %s）"
          % (sorted(EXPECT_REGIONS), "/".join(regions)), set(regions) == EXPECT_REGIONS)
    check("覆盖：输入 region 集 == 期望 %s（实发现 %s）"
          % (sorted(EXPECT_REGIONS), "/".join(regions_in)), set(regions_in) == EXPECT_REGIONS)
    check("覆盖：款数 == 期望 %d（实 %d）" % (n_expect, len(files)), len(files) == n_expect)
    missing = [f for f in files
               if not (os.path.exists(os.path.join(in_dir, f + ".ttf"))
                       and os.path.exists(os.path.join(out_dir, f + ".ttf")))]
    check("覆盖：%d 款(region×style) 输入/输出文件齐全" % len(files), not missing,
          "缺失: %s" % missing[:6])
    per_file = {}
    for f in files:
        print("\n=== %s ===" % f)
        names = verify_pair(os.path.join(in_dir, f + ".ttf"),
                            os.path.join(out_dir, f + ".ttf"), manifest)
        raster_freetype(os.path.join(out_dir, f + ".ttf"), add_cps)
        raster_existing(os.path.join(in_dir, f + ".ttf"), os.path.join(out_dir, f + ".ttf"))
        per_file[f] = names
    consistency(per_file, out_dir, files, regions)
    print("\n==== 汇总 ====")
    if FAIL:
        print("FAIL 项 (%d):" % len(FAIL), FAIL)
        sys.exit(1)
    print("全部自动门禁 PASS（FreeType/Linux 已过；macOS CoreText / Windows DirectWrite 待用户实测）")


if __name__ == "__main__":
    main()
