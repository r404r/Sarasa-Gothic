#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
NF-T6 逐码位 manifest 生成（确定性）。

补入 = 放行集(NF-T5) 里 源存在 且 成品未占 的码位；
保留/跳过 = 成品已占（Powerline 核心/EE00-0B/F880-9F/IEC/box/braille/U+2630 等）或显式排除(Progress/Font Logos)。
断言：补入集 ⊆ 放行集。8 样式共用同一 manifest（占用参照取一个成品即可，SC/J 同 style 占用一致）。

用法：
  build_manifest.py <SymbolsNerdFontMono.ttf> <参照成品.ttf> <out_manifest.json> <out_readme.md> [--budget N]

--budget N：TrueType glyf 上限 numGlyphs≤65535。若 基座+补入 超限，须限定补入数≤N。
  超出时从**最大集**（MDI）的高码位端确定性裁剪至 N（保留低码位，保留 SMP 覆盖）。
  这是**技术约束下的临时裁剪**，最终子集须由产品决策定案（见报告）。
"""
import sys, json, datetime
from collections import Counter
from fontTools.ttLib import TTFont
sys.path.insert(0, __file__.rsplit("/", 1)[0])
import nerd_common as nc


def main():
    src_path, prod_path, out_json, out_md = sys.argv[1:5]
    src = TTFont(src_path)
    prod = TTFont(prod_path)
    scmap = src.getBestCmap()
    occupied = set(prod.getBestCmap().keys())

    add = []
    keep_occupied = []   # 放行范围内但成品已占 → 保留既有，不补
    for cp in sorted(scmap.keys()):
        setname = nc.allowed_set_of(cp)
        if setname is None:
            continue  # 不在放行范围（Progress/Font Logos/其它）
        if cp in occupied:
            keep_occupied.append((cp, setname))
            continue
        add.append({
            "cp": cp, "hex": "U+%04X" % cp,
            "src_glyph": scmap[cp],
            "new_glyph": nc.new_glyph_name(cp),
            "set": setname,
            "class": nc.classify(cp),
        })

    # 预算裁剪（TrueType numGlyphs≤65535 硬限）
    budget = None
    trimmed = {"applied": False}
    if "--budget" in sys.argv:
        budget = int(sys.argv[sys.argv.index("--budget") + 1])
    if budget is not None and len(add) > budget:
        over = len(add) - budget
        big = Counter(a["set"] for a in add).most_common(1)[0][0]
        big_entries = sorted([a for a in add if a["set"] == big], key=lambda a: a["cp"])
        drop_ids = set(id(a) for a in big_entries[-over:])
        kept = [a for a in add if id(a) not in drop_ids]
        trimmed = {"applied": True, "budget": budget, "dropped": over,
                   "trimmed_set": big, "note": "技术约束临时裁剪，最终子集待产品决策"}
        add = kept

    # 断言：补入集 ⊆ 放行集
    for a in add:
        assert nc.allowed_set_of(a["cp"]) is not None, "补入越界: %s" % a["hex"]
    # 断言：新 glyph 名唯一
    names = [a["new_glyph"] for a in add]
    assert len(names) == len(set(names)), "新 glyph 名冲突"

    # 统计
    per_set = {}
    for a in add:
        per_set[a["set"]] = per_set.get(a["set"], 0) + 1
    n_pl = sum(1 for a in add if a["class"] == "powerline")

    manifest = {
        "meta": {
            "generated": datetime.date.today().isoformat(),
            "nerd_version": "v3.4.0",
            "source_font": src_path.rsplit("/", 1)[-1],
            "source_upm": src["head"].unitsPerEm,
            "occupied_reference": prod_path.rsplit("/", 1)[-1],
            "dst_upm": prod["head"].unitsPerEm,
            "thresholds": nc.THRESHOLDS,
            "excluded_note": nc.EXCLUDED_NOTE,
            "budget_trim": trimmed,
        },
        "counts": {
            "add_total": len(add), "add_powerline": n_pl,
            "add_normal": len(add) - n_pl, "per_set": per_set,
            "keep_occupied_in_allowed": len(keep_occupied),
        },
        "add": add,
        "keep_occupied_in_allowed": [
            {"cp": cp, "hex": "U+%04X" % cp, "set": s} for cp, s in keep_occupied
        ],
    }
    with open(out_json, "w") as f:
        json.dump(manifest, f, ensure_ascii=False, indent=1)

    lines = []
    lines.append("# NF-T6 逐码位 manifest（人读说明）\n")
    lines.append("固定源 Nerd v3.4.0 `%s`，占用参照 `%s`。\n" % (
        manifest["meta"]["source_font"], manifest["meta"]["occupied_reference"]))
    lines.append("## 补入统计\n")
    lines.append("- 补入合计 **%d**（普通 %d + Powerline 贴边 %d）\n" % (
        len(add), len(add) - n_pl, n_pl))
    for s in sorted(per_set):
        lines.append("  - %s: %d\n" % (s, per_set[s]))
    lines.append("- 放行范围内成品已占（保留既有、不补）：%d\n" % len(keep_occupied))
    lines.append("\n## 处理策略\n")
    lines.append("- 补入：放行集 ∩ 源存在 ∩ 成品未占；advance=500，几何适配（NF-T7）。\n")
    lines.append("- 保留/跳过（不覆盖）：成品已占 PUA（Powerline 核心 E0A0-BF、EE00-0B、F880-9F、IEC/box/braille）+ 决策排除。\n")
    lines.append("- 显式排除：\n")
    for k, v in nc.EXCLUDED_NOTE.items():
        lines.append("  - %s：%s\n" % (k, v))
    lines.append("\n## 断言\n- 补入集 ⊆ 放行集 ✔\n- 新 glyph 名唯一 ✔\n- 8 样式共用本 manifest（SC/J 同 style 占用一致）\n")
    with open(out_md, "w") as f:
        f.write("".join(lines))

    print("manifest: add=%d (normal=%d, powerline=%d), keep_occupied_in_allowed=%d" % (
        len(add), len(add) - n_pl, n_pl, len(keep_occupied)))
    print("per_set:", per_set)
    print("wrote", out_json, out_md)


if __name__ == "__main__":
    main()
