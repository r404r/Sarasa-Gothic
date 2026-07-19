#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
NF-T9 主 merge 脚本（含 NF-T7 几何 / NF-T8 composite / NF-T11 命名）。

从未 patch 的 hinted 成品 + 固定图标源 + manifest，逐码位补入 Nerd 图标：
  - 几何适配（nerd_common.affine_for），advance=500；
  - 写 glyf（新增 nf_* glyph，唯一名，简单轮廓——源 0 composite，经 glyphSet 绘制自然分解）；
  - hmtx=(500,lsb)、maxp.numGlyphs、hhea.numberOfHMetrics（编译期自动）同步；
  - cmap 多子表：format4 BMP 写、format12 全码位写、UVS(14) 不动、无 symbol cmap；
  - 不改既有 glyph 轮廓/instruction、不改 cvt/fpgm/prep/gasp；
  - 命名加 "NF"（family/full/PS/uniqueID/typo-family），version 追加 Nerd 标记，禁用保留名。
从原件重生成到独立输出目录（不改输入）。recalcTimestamp=False 以利幂等。

用法：merge-nerd-icons.py <输入成品.ttf> <图标源.ttf> <manifest.json> <输出.ttf>
"""
import sys, json
from fontTools.ttLib import TTFont
from fontTools.pens.ttGlyphPen import TTGlyphPen
from fontTools.pens.transformPen import TransformPen
from fontTools.pens.boundsPen import BoundsPen
sys.path.insert(0, __file__.rsplit("/", 1)[0])
import nerd_common as nc

RESERVED = ("Source", "Font Awesome", "Pomicons")   # 禁用保留名（RFN）
NF_TAG = "NF"


def apply_naming(font):
    name = font["name"]
    fam = None
    for rec in name.names:
        if rec.nameID == 1:
            fam = rec.toUnicode(); break
    assert fam, "no family name"
    newfam = "%s %s" % (fam, NF_TAG)                 # "Sarasa Term SC" -> "Sarasa Term SC NF"
    psbase = fam.replace(" ", "-")                   # "Sarasa-Term-SC"
    newpsbase = newfam.replace(" ", "-")             # "Sarasa-Term-SC-NF"
    for rec in list(name.names):
        s = rec.toUnicode(); nid = rec.nameID
        ns = None
        if nid in (1, 16):                           # family / typographic family
            ns = s.replace(fam, newfam) if fam in s else (s + " " + NF_TAG)
        elif nid in (3, 4):                          # unique id / full name（family 为前缀）
            ns = s.replace(fam, newfam, 1)
        elif nid == 6:                               # PostScript
            ns = s.replace(psbase, newpsbase, 1)
        elif nid == 5:                               # version：追加 Nerd 标记，保留版本号
            ns = s + "; Nerd Font v3.4.0"
        if ns is None or ns == s:
            continue
        name.setName(ns, nid, rec.platformID, rec.platEncID, rec.langID)
    # 断言不含保留名
    for rec in name.names:
        if rec.nameID in (1, 3, 4, 6, 16):
            s = rec.toUnicode()
            for rn in RESERVED:
                assert rn not in s, "命名含保留名 %s: %s" % (rn, s)


def add_to_cmap(font, cp, gname):
    for tbl in font["cmap"].tables:
        fmt = tbl.format
        if fmt == 14:            # UVS，不动
            continue
        if fmt == 4:             # BMP-only
            if cp <= 0xFFFF:
                tbl.cmap[cp] = gname
        elif fmt in (12, 13, 6, 0):   # 全码位/其它 unicode 子表
            tbl.cmap[cp] = gname
        else:
            tbl.cmap[cp] = gname


def main():
    in_path, src_path, manifest_path, out_path = sys.argv[1:5]
    font = TTFont(in_path, recalcTimestamp=False)
    src = TTFont(src_path)
    sgs = src.getGlyphSet()
    glyf = font["glyf"]
    hmtx = font["hmtx"]
    vmtx = font["vmtx"] if "vmtx" in font else None   # CJK 竖排度量：须逐 glyph 补
    vorg_default = font["VORG"].defaultVertOriginY if "VORG" in font else font["head"].unitsPerEm
    vadv = font["head"].unitsPerEm                     # 竖排 advanceHeight = em (1000)
    order = list(font.getGlyphOrder())   # 复制，避免与 glyf 内部 glyphOrder 共享引用致重复 append
    existing = set(order)
    manifest = json.load(open(manifest_path))

    # 目标已占码位（防静默覆盖）
    occupied_cps = set()
    for tbl in font["cmap"].tables:
        if tbl.format != 14:
            occupied_cps |= set(tbl.cmap.keys())

    added = 0
    for e in manifest["add"]:
        cp = e["cp"]; srcname = e["src_glyph"]; newname = e["new_glyph"]
        assert newname not in existing, "glyph 名冲突: %s" % newname
        assert cp not in occupied_cps, "拒绝覆盖既有码位 U+%04X" % cp
        bp = BoundsPen(sgs)
        try:
            sgs[srcname].draw(bp)
        except KeyError:
            raise SystemExit("源缺 glyph %s (cp %s)" % (srcname, e["hex"]))
        bounds = bp.bounds
        sx, sy, dx, dy, adv = nc.affine_for(cp, bounds)
        pen = TTGlyphPen(glyphSet=None)              # 源无 composite；glyphSet 绘制得简单轮廓
        sgs[srcname].draw(TransformPen(pen, (sx, 0.0, 0.0, sy, dx, dy)))
        glyph = pen.glyph()
        glyph.recalcBounds(glyf)
        lsb = getattr(glyph, "xMin", 0)
        glyf[newname] = glyph
        hmtx[newname] = (int(adv), int(lsb))
        if vmtx is not None:                          # 竖排：advanceHeight=em，tsb 依 VORG 默认原点
            yMax = getattr(glyph, "yMax", 0)
            vmtx[newname] = (int(vadv), int(round(vorg_default - yMax)))
        order.append(newname)
        existing.add(newname)
        add_to_cmap(font, cp, newname)
        added += 1

    font.setGlyphOrder(order)
    glyf.glyphOrder = order          # 同步 glyf 表内部 glyphOrder（否则 len 断言失败）
    font["maxp"].numGlyphs = len(order)
    apply_naming(font)
    font.save(out_path)
    print("%s: +%d glyphs -> %s" % (in_path.rsplit('/', 1)[-1], added, out_path))


if __name__ == "__main__":
    main()
