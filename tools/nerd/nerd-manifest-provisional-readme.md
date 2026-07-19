# NF-T6 逐码位 manifest（人读说明）
固定源 Nerd v3.4.0 `SymbolsNerdFontMono-Regular.ttf`，占用参照 `SarasaTermJ-Regular.ttf`。
## 补入统计
- 补入合计 **7400**（普通 7380 + Powerline 贴边 20）
  - Codicons: 439
  - Devicons: 496
  - FontAwesome: 1475
  - FontAwesomeExtension: 170
  - MaterialDesignIcons: 4063
  - Octicons: 308
  - Pomicons: 11
  - PowerlineExtra: 20
  - SetiUI+Custom: 190
  - WeatherIcons: 228
- 放行范围内成品已占（保留既有、不补）：12

## 处理策略
- 补入：放行集 ∩ 源存在 ∩ 成品未占；advance=500，几何适配（NF-T7）。
- 保留/跳过（不覆盖）：成品已占 PUA（Powerline 核心 E0A0-BF、EE00-0B、F880-9F、IEC/box/braille）+ 决策排除。
- 显式排除：
  - Progress(EE00-EE0B)：决策3：保留既有 Iosevka 私有字形，不覆盖 → 不引入 Progress
  - FontLogos：NF-T5 排除：unlicensed + 商标
  - U+2630：决策4 前置条件（未占）不成立：成品已占用 → 逐码位保留既有，不补入

## 断言
- 补入集 ⊆ 放行集 ✔
- 新 glyph 名唯一 ✔
- 8 样式共用本 manifest（SC/J 同 style 占用一致）
