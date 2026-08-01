# Sarasa Term — r404r 定制版

[English](README.md) | [简体中文](README.zh-CN.md) | [日本語](README.ja.md)

> [!IMPORTANT]
> 这是 [be5invis/Sarasa-Gothic](https://github.com/be5invis/Sarasa-Gothic)
> 的一个**非官方个人 fork**，用于字体研究、定制构建和发布。如需原始项目及其完整的
> 字体家族和区域选择，请使用 upstream 仓库。

本 fork 专注于提供精简的终端字体发行版，包含自建的 Iosevka 拉丁字符集，以及可选且经过
保真验证的 Nerd Fonts 图标层。默认分支 `dev/main` 汇集所有定制内容；`main` 仅用于与
upstream 保持同步。

## 定制内容

- 仅构建 **Sarasa Term**，提供 `SC`、`TC`、`J` 三个区域版本。
- 每个区域提供 Regular、Italic、Bold、Bold Italic 四种样式。
- 可复现构建的 Iosevka v34.7.0 拉丁字符源，以 `ss15` / IBM Plex Mono 为基础；`l`
  带尾、`1` 带衬线，以提高 `l` / `1` / `I` 的辨识度。
- 可选 Nerd Fonts v3.4.0 图标层，以构建后处理方式合入，保留原有 Sarasa 字形和
  hinting 数据。
- 自动检查 SC/TC/J 集合、拉丁与 CJK 的 1:2 度量、既有字形保真、图标单元格宽度、
  命名以及发布物内容。

常规 Release 包含 24 个 hinted TTF 文件：

| 版本 | 文件 | 安装后的字体家族 |
| --- | --- | --- |
| 不含图标 | `SarasaTerm{SC,TC,J}-{Style}.ttf` | `Sarasa Term SC/TC/J` |
| 含 Nerd 图标 | `SarasaTerm{SC,TC,J}-NF-{Style}.ttf` | `Sarasa Term SC/TC/J NF` |

两个版本使用不同的 family 名，可以同时安装。字体包、校验和、图标署名和平台验证说明请见
[Releases](https://github.com/r404r/Sarasa-Gothic/releases)。

本 fork 正在研究和开发 TTC 打包。在相关验证完成前，TTC 不属于上述稳定交付范围。

## 构建

upstream 构建需要 Node.js 20 或更高版本、最新 AFDKO 和 `ttfautohint`。安装 JavaScript
依赖并构建当前配置的 TTF 集合：

```bash
npm install
npm run build ttf
```

构建结果位于 `out/TTF`。一次无缓存的 hinted CJK 构建可能需要数小时。

定制拉丁字符的构建配方位于 `iosevka-build/`。Nerd 图标源、manifest、许可证、合并工具
和验证工具位于 `sources/nerd/` 与 `tools/nerd/`。

只组装并验证 Release、但不发布到 GitHub：

```bash
tools/release/make-release.sh --no-publish
```

运行 `tools/release/make-release.sh --help` 查看依赖要求和发布选项。正式发布需要已认证的
GitHub CLI 会话。

## 与 upstream 的关系

- `main` 跟踪 `be5invis/Sarasa-Gothic`，不用于个人功能开发。
- `dev/main` 是本 fork 的集成分支。
- `PR/*` 分支用于在合入 `dev/main` 前隔离各项定制改动。

准备提交给 upstream 的贡献必须基于已同步的 `main`，不能基于 `dev/main`，以免本 fork
的产品决策、内置资源和 README 进入 upstream PR。创建 PR 前请检查其范围：

```bash
git diff upstream/main...HEAD
```

## 许可证与署名

Sarasa Gothic 使用 SIL Open Font License 1.1，详见 [`LICENSE`](LICENSE)。包含 Nerd
图标的发布物会附带适用的第三方许可证和署名包。Sarasa Gothic、Iosevka、Inter 和
Source Han Sans 的 upstream 贡献者拥有各自项目的原始项目署名。
