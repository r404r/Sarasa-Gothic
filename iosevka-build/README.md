# Iosevka Latin source build recipe

本分支 `sources/IosevkaNTerm/IosevkaNTerm-{Regular,Italic,Bold,BoldItalic}.ttf`
四个 Latin 源为**自建**，用于提升 l/1 可辨性（l 带尾；整体采用 ss15 / IBM Plex
Mono 风格，数字 1 沿用 ss15 默认的底衬线）。

> 交付说明：`inherits = "ss15"` 会改变**大量** Latin 字形（不止 l/1），整体呈 IBM
> Plex Mono 风格——这是有意选择。除 l/1 外其他 Latin 字形与官方 IosevkaNTerm 存在
> 差异（be5invis 的 IosevkaN 构建参数不公开，无法完全复刻）。中英 1:2 等宽、字符
> 覆盖（自建为官方超集）已验证保持。

## 固定版本

- Iosevka 仓库：<https://github.com/be5invis/Iosevka>
- **tag：`v34.7.0`**
- **commit：`6828cb0bd569992bb19565a5e448540de3b50541`**
- 构建环境（已验证）：**Node v24.18.0、npm 11.16.0**；`ttfautohint 1.8.4`（Iosevka
  自身构建需要，非 AFDKO）。
- 构建计划：本目录 `private-build-plans.toml`（`[buildPlans.IosevkaCustom]`，
  `spacing = "term"`、`variants.inherits = "ss15"`、`variants.design.l = "tailed-serifed"`、
  `exportGlyphNames = true`）。

## 精确复现步骤

```sh
# 1) 取固定版本
git clone https://github.com/be5invis/Iosevka.git
cd Iosevka
git checkout 6828cb0bd569992bb19565a5e448540de3b50541   # == tag v34.7.0

# 2) 放入本目录的 private-build-plans.toml（覆盖仓库根同名文件）
cp <this-repo>/iosevka-build/private-build-plans.toml ./private-build-plans.toml

# 3) 装依赖并构建该 plan（产出 Regular/Italic/Bold/BoldItalic + Extended 宽度）
npm ci
npm run build -- ttf::IosevkaCustom

# 4) 取「无 hint」产物（Sarasa 的 LatinSource 会自行 ttfautohint -d，取 unhinted 最干净）
#    产物路径：dist/IosevkaCustom/TTF-Unhinted/IosevkaCustom-<Style>.ttf
#    只取 4 个「非 Extended」样式，重命名映射如下：
#      IosevkaCustom-Regular.ttf     -> IosevkaNTerm-Regular.ttf
#      IosevkaCustom-Italic.ttf      -> IosevkaNTerm-Italic.ttf
#      IosevkaCustom-Bold.ttf        -> IosevkaNTerm-Bold.ttf
#      IosevkaCustom-BoldItalic.ttf  -> IosevkaNTerm-BoldItalic.ttf
#    （dist 里同时有 IosevkaCustom-Extended*.ttf，本项目不使用，忽略。）
```

## 复现校验（目标文件 SHA-256）

替换进 `sources/IosevkaNTerm/` 的四个自建源（本分支当前值）：

```
be8ed9f5ccbbe35df69b58ac7281ab597c2f365e592f640233b68b6dfbfb9cee  IosevkaNTerm-Regular.ttf
dcd4016d48ef2d5ec96679401e83e4edd4859403ecae30e7bd28283748e9ac69  IosevkaNTerm-Italic.ttf
3fadaeaf5c7876ca46cc6b01f860a96832f31f4ffdb5b9b0950dd81a926f8d44  IosevkaNTerm-Bold.ttf
b5ed75c5bb2fc25dd3aedc0070731e7f059918441f1005975e870a1a33b51ab2  IosevkaNTerm-BoldItalic.ttf
```

> 注：Iosevka 产物可能内嵌构建时间戳，跨机/跨时重建的字节级 SHA 未必完全一致；
> 若不匹配，用 fontTools 做**语义比对**（UPM=1000、ASCII advance=500、cmap 覆盖、
> GSUB/GPOS、关键 glyph 轮廓）确认等效，而非仅比字节。
