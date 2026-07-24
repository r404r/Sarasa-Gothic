#!/usr/bin/env bash
# =============================================================================
# 一键出 Release —— 把 AGENTS.md 第 7 节「定制字体交付定则」落成可执行流程。
#
# 产出：Sarasa Term SC/TC/J × {Regular,Italic,Bold,BoldItalic} 的两套 hinted TTF
#   · 不含图标： SarasaTerm{SC,TC,J}-{Style}.ttf        (family "Sarasa Term …")
#   · 含 Nerd 图标：SarasaTerm{SC,TC,J}-NF-{Style}.ttf  (family "Sarasa Term … NF")
# 共 24 个 + 图标许可包 + SHA256SUMS，并（可选）发布为 CalVer GitHub Release。
#
# 用法：
#   tools/release/make-release.sh [选项]
#     --version VER    发布版本号（CalVer，默认=当天 YYYY.MM.DD）
#     --target BR      release 目标分支（默认 dev/main）
#     --skip-build     复用已有 out/TTF（跳过 ~数小时的 npm 主构建）
#     --no-publish     只构建/合成/校验/组装到 dist-release/，不创建 GitHub Release（试跑）
#     --prerelease     标记为 pre-release（默认：正式版 latest、非 pre-release）
#     --repo O/N       GitHub 仓库（默认取 origin 远端）
#     -h | --help
#
# 前置（须在 PATH 上；缺失会明确报错）：
#   node + npm（Sarasa 构建）、ttfautohint、otf2ttf、otc2otf（AFDKO）、
#   python3（须 import fontTools 成功；NF 合成/校验用 Pillow 做 raster）、zip、
#   gh（仅发布时；须已 gh auth login）。
#   可用环境变量 PYTHON 指定 python 解释器（默认 python3）。
# =============================================================================
set -euo pipefail

# ---- 定位仓库根 ----
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"
cd "$ROOT"

PYTHON="${PYTHON:-python3}"
STYLES=(Regular Italic Bold BoldItalic)
REGIONS=(SC TC J)

# ---- 解析参数 ----
VERSION=""; TARGET="dev/main"; SKIP_BUILD=0; NO_PUBLISH=0; PRERELEASE=0; REPO=""
while [ $# -gt 0 ]; do
  case "$1" in
    --version) VERSION="$2"; shift 2;;
    --target) TARGET="$2"; shift 2;;
    --skip-build) SKIP_BUILD=1; shift;;
    --no-publish) NO_PUBLISH=1; shift;;
    --prerelease) PRERELEASE=1; shift;;
    --repo) REPO="$2"; shift 2;;
    -h|--help) sed -n '2,30p' "${BASH_SOURCE[0]}" | sed 's/^# \{0,1\}//'; exit 0;;
    *) echo "未知参数: $1" >&2; exit 2;;
  esac
done
[ -n "$VERSION" ] || VERSION="$(date +%Y.%m.%d)"

say(){ printf '\n\033[1;36m==> %s\033[0m\n' "$*"; }
die(){ printf '\033[1;31mERROR: %s\033[0m\n' "$*" >&2; exit 1; }

# ---- 前置检查 ----
say "前置检查"
need(){ command -v "$1" >/dev/null 2>&1 || die "缺少 '$1'（$2）"; }
need node "Sarasa 构建"; need npm "Sarasa 构建"
need ttfautohint "字体 hinting/去hint"; need otf2ttf "AFDKO"; need otc2otf "AFDKO"
need zip "打包许可"
"$PYTHON" -c "import fontTools" 2>/dev/null || die "python 无 fontTools（PYTHON=$PYTHON；请 pip install fonttools）"
"$PYTHON" -c "import PIL" 2>/dev/null || die "python 无 Pillow（NF 校验需 raster；请 pip install pillow）"
[ "$NO_PUBLISH" = 1 ] || need gh "发布 Release（或加 --no-publish 试跑）"

# ---- 仓库/定则一致性检查 ----
say "定则一致性检查（AGENTS.md §7）"
[ -f config.json ] && [ -f verdafile.mjs ] || die "不在 Sarasa-Gothic 仓库根？"
SFO="$(node -e "process.stdout.write(JSON.stringify(require('./config.json').subfamilyOrder))")"
[ "$SFO" = '["SC","TC","J"]' ] || die "config.json subfamilyOrder=$SFO，应为 [\"SC\",\"TC\",\"J\"]（§7.1）"
for f in tools/nerd/merge-nerd-icons.py tools/nerd/verify-nerd.py tools/nerd/nerd-manifest.json \
         sources/nerd/SymbolsNerdFontMono-Regular.ttf sources/nerd/licenses/ATTRIBUTION.md; do
  [ -f "$f" ] || die "缺少 $f"
done
echo "  region=SC/TC/J、NF 工具/图标源/许可 齐全"

# ---- 1) Sarasa 主构建（12 非-NF）----
if [ "$SKIP_BUILD" = 1 ]; then
  say "跳过主构建（--skip-build），复用 out/TTF"
else
  say "Sarasa 主构建（npm run build ttf）—— 冷构建约数小时，缓存命中很快"
  npm run build ttf
fi
NHINT=$(ls out/TTF/SarasaTerm*.ttf 2>/dev/null | wc -l | tr -d ' ')
[ "$NHINT" = 12 ] || die "out/TTF 应有 12 个 hinted，实为 $NHINT（先跑主构建或去掉 --skip-build）"
echo "  out/TTF: 12 个 hinted (SC/TC/J × 4)"

# ---- 2) Nerd 合成（12 NF，后处理，不进主构建）----
say "Nerd 图标合成（fontTools 只补差集后处理 → out/TTF-NF/）"
rm -rf out/TTF-NF; mkdir -p out/TTF-NF
for f in out/TTF/SarasaTerm*.ttf; do
  "$PYTHON" tools/nerd/merge-nerd-icons.py "$f" \
    sources/nerd/SymbolsNerdFontMono-Regular.ttf tools/nerd/nerd-manifest.json \
    "out/TTF-NF/$(basename "$f")" >/dev/null
done
NNF=$(ls out/TTF-NF/*.ttf 2>/dev/null | wc -l | tr -d ' ')
[ "$NNF" = 12 ] || die "out/TTF-NF 应有 12，实为 $NNF"
echo "  out/TTF-NF: 12 个 NF"

# ---- 3) 保真门禁（Linux/FreeType 自动，含 region 断言 + 负向语义）----
say "自动门禁（verify-nerd.py，12 款 + 覆盖断言）"
"$PYTHON" tools/nerd/verify-nerd.py out/TTF out/TTF-NF tools/nerd/nerd-manifest.json \
  || die "自动门禁 FAIL——中止发布（见上方 [FAIL] 项）"

# ---- 4) 组装发布物 ----
DIST="dist-release"; rm -rf "$DIST"; mkdir -p "$DIST"
say "组装发布物 → $DIST/"
cp out/TTF/SarasaTerm*.ttf "$DIST/"                                  # 12 非-NF（原名）
for f in out/TTF-NF/SarasaTerm*.ttf; do                             # 12 NF（插 -NF-）
  b="$(basename "$f" .ttf)"; region="${b#SarasaTerm}"; region="${region%%-*}"; style="${b##*-}"
  cp "$f" "$DIST/SarasaTerm${region}-NF-${style}.ttf"
done
( cd sources/nerd/licenses && zip -q -r "$OLDPWD/$DIST/Nerd-icon-licenses.zip" . )
( cd "$DIST" && sha256sum ./*.ttf | sed 's| \./| |' | sort -k2 > SHA256SUMS.txt )
NTTF=$(ls "$DIST"/*.ttf | wc -l | tr -d ' ')
[ "$NTTF" = 24 ] || die "发布物应有 24 个 TTF，实为 $NTTF"
echo "  $DIST: 24 TTF（12 非-NF + 12 NF）+ Nerd-icon-licenses.zip + SHA256SUMS.txt"

# ---- 5) 发布 ----
NOTES="$(cat <<EOF
Sarasa Term **SC / TC / J** + 自建 Iosevka（l 带尾、1 带衬线，提升 l/1/I 可辨性）。提供**含 Nerd 图标**与**不含 Nerd 图标**两套。

## 文件（各 12 hinted TTF，共 24）
- 不含图标：\`SarasaTerm{SC,TC,J}-{Style}.ttf\`（family \`Sarasa Term SC/TC/J\`）
- 含 Nerd 图标：\`SarasaTerm{SC,TC,J}-NF-{Style}.ttf\`（family \`Sarasa Term SC/TC/J NF\`）
两套 family 名不同、可共存安装。Style = Regular/Italic/Bold/BoldItalic。

## Nerd 图标（Nerd Fonts v3.4.0）
Font Awesome/Devicons/Codicons/Octicons/Weather/Seti-UI/FA Extension/Powerline Extra/Pomicons（不含 MDI——单字体 65535 字形硬限）。既有 hinting/中英 1:2/box-drawing 保真（自动门禁全绿）。

## 许可
字体 OFL 1.1；NF 版须随附 \`Nerd-icon-licenses.zip\`（含 ATTRIBUTION：Font Awesome/Codicons 的 CC BY 4.0 署名）。校验和见 \`SHA256SUMS.txt\`。

_由 tools/release/make-release.sh 依 AGENTS.md §7 定则产出。_
EOF
)"
if [ "$NO_PUBLISH" = 1 ]; then
  say "试跑（--no-publish）：发布物已就绪于 $DIST/，未创建 Release。"
  echo "  如需发布：$0 --version $VERSION${REPO:+ --repo $REPO}"
  exit 0
fi
[ -n "$REPO" ] || REPO="$(gh repo view --json nameWithOwner --jq .nameWithOwner)"
FLAGS=(--target "$TARGET"); [ "$PRERELEASE" = 1 ] && FLAGS+=(--prerelease) || FLAGS+=(--latest)
say "创建 GitHub Release：$VERSION（$REPO，target $TARGET，$([ "$PRERELEASE" = 1 ] && echo pre-release || echo latest)）"
gh release view "$VERSION" -R "$REPO" >/dev/null 2>&1 \
  && die "tag $VERSION 已存在——换 --version 或先删旧 release"
gh release create "$VERSION" -R "$REPO" "${FLAGS[@]}" \
  --title "Sarasa Term SC/TC/J · Iosevka l/1 + Nerd icons — $VERSION" \
  --notes "$NOTES" \
  "$DIST"/*.ttf "$DIST/Nerd-icon-licenses.zip" "$DIST/SHA256SUMS.txt"
say "完成 → https://github.com/$REPO/releases/tag/$VERSION"
