#!/usr/bin/env bash
# NF 后处理接入（NF-T12）：对 8 个未 patch hinted 成品补入 Nerd 图标。
# 独立后处理步骤，不进 Sarasa 主构建关键路径（主构建 hinted CJK 在免费 CI 6h 跑不完）。
# 幂等：从 out/TTF/ 原件重生成到 out/TTF-NF/，不改输入；同输入+同工具链 → 字节级相同。
# 上游 Sarasa 更新后：重跑主构建得新 out/TTF/ → 重跑本脚本。
# 升级 Nerd：更新 sources/nerd/ 固定版本并**重跑 NF-T5 许可核实**，再重跑本脚本。
set -euo pipefail
HERE="$(cd "$(dirname "$0")" && pwd)"; ROOT="$(cd "$HERE/../.." && pwd)"
PY="${PY:-python3}"
SRC="$ROOT/sources/nerd/SymbolsNerdFontMono-Regular.ttf"
MAN="$HERE/nerd-manifest.json"
IN="$ROOT/out/TTF"; OUT="$ROOT/out/TTF-NF"
mkdir -p "$OUT"
for f in "$IN"/*.ttf; do
  "$PY" "$HERE/merge-nerd-icons.py" "$f" "$SRC" "$MAN" "$OUT/$(basename "$f")"
done
echo "done -> $OUT"; echo "verify: $PY $HERE/verify-nerd.py $IN $OUT $MAN"
