"""Regression test for the multi-panel composition geometry (figure-composer).

grid_geom / panel_px / panel_xy resolve a 12-column mm outline to exact pixel
slots; compose_figure tiles per-panel PNGs onto that grid and stamps letters;
compose_crops mirrors the slots for the perceptual self-QA pass.

Run:  python tests/test_compose.py
"""

import os

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
from PIL import Image

import EasyPlotLib as epl

HERE = os.path.dirname(os.path.abspath(__file__))

OUTLINE = {
    "claim": "the method scales",
    "width_mm": 180,
    "ncol": 12,
    "row_heights_mm": [40, 60],
    "panels": [
        {"letter": "a", "role": "schematic", "row": 0, "col": 0, "colspan": 12,
         "chart_family": "schematic", "message": "overview", "ask": "draw the pipeline"},
        {"letter": "b", "role": "primary", "row": 1, "col": 0, "colspan": 7,
         "chart_family": "scatter", "message": "b carries the claim", "ask": "scatter + fit"},
        {"letter": "c", "role": "supporting", "row": 1, "col": 7, "colspan": 5,
         "chart_family": "bar", "message": "robustness", "ask": "bar of ablations"},
    ],
}


def test_grid_geometry():
    dpi, gutter = 300, 4
    W, ncol, colw, rowh, row_y, g = epl.grid_geom(OUTLINE, dpi, gutter)
    mm = dpi / 25.4
    assert W == int(180 * mm) and ncol == 12
    # full-width panel a spans all 12 columns + 11 gutters == W
    assert epl.panel_px(OUTLINE, "a", dpi, gutter) == (colw * 12 + g * 11, rowh[0])
    # b (7 col) + c (5 col) + one gutter tile the full width of row 1
    wb, hb = epl.panel_px(OUTLINE, "b", dpi, gutter)
    wc, hc = epl.panel_px(OUTLINE, "c", dpi, gutter)
    assert wb + g + wc == colw * 12 + g * 11
    assert hb == hc == rowh[1]
    # c starts immediately after b's 7 columns + gutter
    assert epl.panel_xy(OUTLINE, "c", dpi, gutter)[0] == 7 * (colw + g)
    assert epl.panel_xy(OUTLINE, "b", dpi, gutter) == (0, row_y[1])


def test_compose_and_crops():
    paths = {}
    # Panel-makers "fill the box" (figure-rules §3.5) by reserving *absolute* label
    # space, not a fixed fraction — so the axes boxes line up across the grid
    # regardless of panel width. (A fixed fractional margin would inset the wide
    # top panel far more than the narrow bottom ones.)
    LEFT_IN, BOT_IN, PAD_IN = 0.55, 0.40, 0.10
    for L in ("a", "b", "c"):
        w, h = epl.panel_px(OUTLINE, L)
        w_in, h_in = w / 300, h / 300
        fig = plt.figure(figsize=(w_in, h_in), dpi=300)
        ax = fig.add_subplot(111)
        fig.subplots_adjust(
            left=LEFT_IN / w_in, right=1 - PAD_IN / w_in,
            bottom=BOT_IN / h_in, top=1 - PAD_IN / h_in,
        )
        ax.plot([0, 1], [0, 1])
        p = os.path.join(HERE, f"_compose_panel_{L}.png")
        fig.savefig(p, dpi=300, transparent=True)
        plt.close(fig)
        # panels must land at exactly their slot size (no tight/constrained layout)
        assert Image.open(p).size == (w, h), (L, Image.open(p).size, (w, h))
        paths[L] = p

    out = os.path.join(HERE, "test_compose.png")
    out_path, (W, H) = epl.compose_figure(OUTLINE, paths, out)
    assert Image.open(out_path).size == (W, H)

    crops = epl.compose_crops(OUTLINE)
    assert set(crops) == {"a", "b", "c"}
    for L, (x0, y0, x1, y1) in crops.items():
        assert 0 <= x0 < x1 <= W and 0 <= y0 < y1 <= H, (L, crops[L], (W, H))

    for p in paths.values():
        os.remove(p)
    print(f"composed {W}x{H}px; crops -> {crops}")


def test_schema_and_revisions():
    sch = epl.figure_outline_schema()
    assert sch["type"] == "object" and "panels" in sch["properties"]
    affected = epl.apply_outline_revisions(
        OUTLINE, [{"affected_panels": ["b", "c"]}, {"affected_panels": ["c"]}]
    )
    assert affected == {"b", "c"}


if __name__ == "__main__":
    test_grid_geometry()
    test_compose_and_crops()
    test_schema_and_revisions()
    print("OK: grid_geom / panel_px / compose_figure / compose_crops verified.")
