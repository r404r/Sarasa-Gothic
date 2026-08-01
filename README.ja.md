# Sarasa Term — r404r カスタム版

[English](README.md) | [简体中文](README.zh-CN.md) | [日本語](README.ja.md)

> [!IMPORTANT]
> これは [be5invis/Sarasa-Gothic](https://github.com/be5invis/Sarasa-Gothic)
> の**非公式な個人 fork**であり、フォントの研究、カスタムビルド、およびリリースを目的と
> しています。オリジナルプロジェクトと完全なファミリー・地域バリエーションについては、
> upstream リポジトリを利用してください。

この fork は、独自ビルドの Iosevka ラテン文字セットと、任意で追加できる保全性検証済みの
Nerd Fonts アイコンレイヤーを備えた、コンパクトなターミナル用フォント配布に特化しています。
デフォルトブランチの `dev/main` にカスタマイズを統合し、`main` は upstream との同期専用に
維持しています。

## カスタマイズ内容

- **Sarasa Term のみ**を対象とし、`SC`、`TC`、`J` の各地域版を提供します。
- 各地域版に Regular、Italic、Bold、Bold Italic の4スタイルを提供します。
- `ss15` / IBM Plex Mono を基にした、再現可能な Iosevka v34.7.0 ラテン文字ソースを
  使用します。`l` にテール、`1` にセリフを付け、`l` / `1` / `I` の判別性を高めています。
- Nerd Fonts v3.4.0 アイコンレイヤーを任意で追加できます。ビルド後処理としてマージする
  ことで、既存の Sarasa グリフと hinting データを保持します。
- SC/TC/J の構成、ラテン文字と CJK の 1:2 メトリクス、既存グリフの保全性、アイコンの
  セル幅、命名、リリース内容を自動検証します。

通常の Release には、24個の hinted TTF ファイルが含まれます。

| バリエーション | ファイル | インストール時のファミリー |
| --- | --- | --- |
| アイコンなし | `SarasaTerm{SC,TC,J}-{Style}.ttf` | `Sarasa Term SC/TC/J` |
| Nerd アイコンあり | `SarasaTerm{SC,TC,J}-NF-{Style}.ttf` | `Sarasa Term SC/TC/J NF` |

2つのバリエーションは異なる family 名を使用するため、同時にインストールできます。配布フォント、
チェックサム、アイコンのクレジット、プラットフォーム検証結果については
[Releases](https://github.com/r404r/Sarasa-Gothic/releases)を参照してください。

この fork では TTC パッケージングを研究・開発中です。検証が完了するまでは、上記の安定版
配布には含まれません。

## ビルド

upstream のビルドには Node.js 20 以降、最新版の AFDKO、および `ttfautohint` が必要です。
JavaScript 依存関係をインストールし、現在の設定で TTF をビルドします。

```bash
npm install
npm run build ttf
```

ビルド結果は `out/TTF` に生成されます。キャッシュなしの hinted CJK ビルドには数時間かかる
場合があります。

カスタムラテン文字のビルドレシピは `iosevka-build/` にあります。Nerd アイコンのソース、
manifest、ライセンス、マージツール、および検証ツールは `sources/nerd/` と `tools/nerd/` に
あります。

GitHub に公開せず、Release の組み立てと検証だけを行うには、次を実行します。

```bash
tools/release/make-release.sh --no-publish
```

必要なツールとリリースオプションは `tools/release/make-release.sh --help` で確認できます。
公開には認証済みの GitHub CLI セッションが必要です。

## upstream との関係

- `main` は `be5invis/Sarasa-Gothic` を追跡し、個人機能の開発には使用しません。
- `dev/main` はこの fork の統合ブランチです。
- `PR/*` ブランチは、個別のカスタマイズを `dev/main` に統合する前に分離するために使用します。

upstream 向けの貢献は、`dev/main` ではなく、最新の状態に同期した `main` を基点にしてください。
これにより、この fork 固有の製品方針、同梱ソース、README が upstream の pull request に混入する
ことを防げます。PR を作成する前に、次のコマンドで対象範囲を確認してください。

```bash
git diff upstream/main...HEAD
```

## ライセンスとクレジット

Sarasa Gothic は SIL Open Font License 1.1 の下で提供されています。詳細は
[`LICENSE`](LICENSE)を参照してください。Nerd アイコンを含むリリース成果物には、該当する
第三者ライセンスとクレジット一式を同梱します。オリジナルプロジェクトのクレジットは、
Sarasa Gothic、Iosevka、Inter、および Source Han Sans の各コントリビューターに帰属します。
