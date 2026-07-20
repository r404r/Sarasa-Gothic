#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
NF-T6/T7/T8 shared logic: 放行集码位范围、逐码位分类、几何适配（UPM 统一 / bbox fit /
side bearing / 水平居中 / overhang / 垂直安放 / Powerline 贴边特例）。

固定输入：Nerd Fonts v3.4.0 `SymbolsNerdFontMono-Regular.ttf`（UPM=2048，advance 全 2048）。
目标字体：Sarasa Term（UPM=1000，半角 cell=500，hhea asc/desc=965/-215，OS/2 typo desc=-285）。

几何阈值（NF-T7 开放阈值，已在成品上实测标定，见 03/04 记录）：
"""

# ---- 固定度量 ----
SRC_UPM = 2048
DST_UPM = 1000
CELL = 500                     # 半角单格宽
HHEA_ASC, HHEA_DESC = 965, -215
TYPO_DESC = -285               # 既有 Powerline 下探到 -285（甚至 -307）

# ---- NF-T7 开放阈值（实测标定值）----
S_CAP = CELL / SRC_UPM         # 0.244140625：普通图标不放大超过“单格设计尺寸”
MARGIN_X = 12                  # 普通图标左右留白（每侧），确保严格落在 [0,500]
ICON_MAX_W = CELL - 2 * MARGIN_X   # 476：普通图标绘制宽上限（禁 overhang）
ICON_CENTER_Y = 368            # 普通图标垂直居中基准（≈ capHeight/2=735/2）
# 普通图标垂直硬边界（防裁切）：[-215, 965]。因 S_CAP 限制，最大高≈505，居中 368 → [115,620]，安全。
NORMAL_VMIN, NORMAL_VMAX = HHEA_DESC, HHEA_ASC

# Powerline 贴边类：非等比填充，与既有 E0B0–E0BF 对齐（源包络实测）
SRC_PL_YMIN, SRC_PL_YMAX = -420, 1649   # 源 Powerline(E0B0–E0D7) 垂直包络
PL_DST_YMIN, PL_DST_YMAX = TYPO_DESC, HHEA_ASC   # 映射到 [-285, 965]，与既有一致（允许 edge-bleed）

# ---- 放行集码位范围（NF-T5 通过的 10 集；补入集上限）----
# 每项：(集名, 起, 止) 闭区间；Powerline Extra 用离散集单列。
ALLOWED_RANGES = [
    ("Pomicons",             0xE000, 0xE00A),
    ("FontAwesomeExtension", 0xE200, 0xE2A9),
    ("WeatherIcons",         0xE300, 0xE3E3),
    ("SetiUI+Custom",        0xE5FA, 0xE6B7),
    ("Devicons",             0xE700, 0xE8EF),
    ("Codicons",             0xEA60, 0xEC1E),
    ("FontAwesome",          0xED00, 0xEFCE),
    ("FontAwesome",          0xF000, 0xF2FF),
    ("Octicons",             0xF400, 0xF533),
    # MaterialDesignIcons (0xF0001–0xF1AF0, 6896 glyphs) 已由产品决策剔除：
    # TrueType glyf numGlyphs≤65535 硬限，J 基座 58022 只余 7513，全集补入 10233 装不下；
    # 决策=剔除 MDI，保留其余非-MDI 集 100% 完整（见 05-final-subset-decision）。
]
# Powerline Extra 补差（缺失码位；离散，不含空洞 E0C9/E0CB）
POWERLINE_EXTRA_ADD = (
    list(range(0xE0C0, 0xE0C9)) + [0xE0CA] + list(range(0xE0CC, 0xE0D8))
)
POWERLINE_CLASS = set(POWERLINE_EXTRA_ADD)   # 贴边白名单

# 显式排除 / 跳过（不属补入；仅用于 manifest 记录与断言）
EXCLUDED_NOTE = {
    "Progress(EE00-EE0B)": "决策3：保留既有 Iosevka 私有字形，不覆盖 → 不引入 Progress",
    "FontLogos": "NF-T5 排除：unlicensed + 商标",
    "U+2630": "决策4 前置条件（未占）不成立：成品已占用 → 逐码位保留既有，不补入",
    "MaterialDesignIcons": "产品决策剔除（glyf 65535 硬限，J 余量不足）：剔 MDI，非-MDI 全集 100% 保留",
}


def allowed_set_of(cp):
    """返回码位所属放行集名；不在放行范围返回 None。"""
    if cp in POWERLINE_CLASS:
        return "PowerlineExtra"
    for name, lo, hi in ALLOWED_RANGES:
        if lo <= cp <= hi:
            return name
    return None


def classify(cp):
    """'powerline' 贴边 / 'normal' 普通。"""
    return "powerline" if cp in POWERLINE_CLASS else "normal"


def new_glyph_name(cp):
    if cp <= 0xFFFF:
        return "nf_uni%04X" % cp
    return "nf_u%06X" % cp


# ---- 几何变换：返回 (sx, sy, dx, dy) 仿射，把源 glyph 坐标映射到目标 ----
def affine_for(cp, bounds):
    """
    bounds = (xMin,yMin,xMax,yMax) 源坐标；None 表示空轮廓。
    返回 (sx, sy, dx, dy, advance)。
    """
    if bounds is None:
        return (S_CAP, S_CAP, 0.0, 0.0, CELL)  # 空轮廓：仅占位，advance=500
    xMin, yMin, xMax, yMax = bounds
    w = max(1.0, xMax - xMin)
    h = max(1.0, yMax - yMin)
    if classify(cp) == "powerline":
        sx = CELL / SRC_UPM
        sy = (PL_DST_YMAX - PL_DST_YMIN) / (SRC_PL_YMAX - SRC_PL_YMIN)
        dx = 0.0                                   # 源已在格内定位，overhang 由源坐标保留
        dy = PL_DST_YMIN - SRC_PL_YMIN * sy        # y_src=SRC_PL_YMIN → PL_DST_YMIN
        return (sx, sy, dx, dy, CELL)
    # normal：等比缩放，min(单格上限, 宽度适配)；高度因 S_CAP 恒安全
    scale = min(S_CAP, ICON_MAX_W / w)
    sx = sy = scale
    drawn_w = w * scale
    dx = (CELL - drawn_w) / 2.0 - xMin * scale     # 水平居中
    ymid = (yMin + yMax) / 2.0
    dy = ICON_CENTER_Y - ymid * scale              # 垂直居中于基准
    return (sx, sy, dx, dy, CELL)


THRESHOLDS = {
    "S_CAP": S_CAP, "MARGIN_X": MARGIN_X, "ICON_MAX_W": ICON_MAX_W,
    "ICON_CENTER_Y": ICON_CENTER_Y, "NORMAL_VBOUND": [NORMAL_VMIN, NORMAL_VMAX],
    "SRC_PL_ENVELOPE_Y": [SRC_PL_YMIN, SRC_PL_YMAX],
    "PL_DST_Y": [PL_DST_YMIN, PL_DST_YMAX], "CELL": CELL,
}
