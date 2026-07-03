"""Regression test for the figure-style toolkit (correctness & legibility helpers).

Covers focal_palette (colour emphasis), the categorical × numeric chart helpers
(bar_with_points / strip_with_median), goodness_arrow / set_frame / two_tier_label,
and panel_crops (the §9.2 render-then-verify crop boxes).

Run:  python tests/test_figure_style.py
"""

import os

import numpy as np
import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt

import EasyPlotLib as epl

HERE = os.path.dirname(os.path.abspath(__file__))


# --- focal_palette: focal series keeps its saturated hue, others recede ----------
def test_focal_palette():
    labs = ["baseline", "prior", "ours", "ablation"]
    focal = epl.SEMANTIC["blue_main"]
    cols = epl.focal_palette(labs, "ours", focal)
    assert cols[2] == focal and len(cols) == len(labs)
    assert focal not in [c for i, c in enumerate(cols) if i != 2]  # unique to focal
    # 'grey' mode: every non-focal is the same light grey
    grey = epl.focal_palette(labs, "ours", focal, other="grey")
    assert grey[2] == focal and set(grey) - {focal} == {"#BCBCBC"}
    # 'ordinal' mode: non-focal on a light→dark ramp (distinct greys, in order)
    ordn = epl.focal_palette(labs, "ours", focal, other="ordinal")
    non_focal = [c for i, c in enumerate(ordn) if i != 2]
    assert len(set(non_focal)) == len(non_focal)  # all distinct
    # a set of focal labels is accepted
    both = epl.focal_palette(labs, {"ours", "prior"}, focal)
    assert both[1] == focal and both[2] == focal
    # unknown focal / bad mode rejected
    for bad in (lambda: epl.focal_palette(labs, "nope", focal),
                lambda: epl.focal_palette(labs, "ours", focal, other="rainbow")):
        try:
            bad()
        except ValueError:
            pass
        else:
            raise AssertionError("expected ValueError")


# --- bar_with_points / strip_with_median: distribution, not just the summary -----
def test_chart_helpers():
    rng = np.random.default_rng(0)
    ymat = [rng.normal(m, 0.3, 8) for m in (1.0, 1.4, 1.2)]
    labels = ["a", "b", "ours"]
    cols = epl.focal_palette(labels, "ours", epl.SEMANTIC["blue_main"])

    # Double-column width so two side-by-side panels are physically large enough
    # to read; cell-golden aspect for a 1×2 grid.
    epl.journal_style("nat2", nrows=1, ncols=2)
    fig, axs = plt.subplots(1, 2)

    # points overlay: no error bars drawn (they are alternatives, not both)
    epl.bar_with_points(axs[0], np.arange(3), ymat, labels, cols, show_points=True)
    assert [t.get_text() for t in axs[0].get_xticklabels()] == labels
    n_err_points = len(axs[0].collections)  # scatter overlays present
    assert n_err_points >= 1

    # ci95 interval mode (needs SciPy): error bars, no scatter
    epl.bar_with_points(axs[1], np.arange(3), ymat, labels, cols,
                        show_points=False, errorbar="ci95")
    epl.strip_with_median(axs[1] if False else axs[0], labels[:2],
                          [ymat[0], ymat[1]])  # overlay strip is drawable
    epl.set_frame(axs[1], "boxed")
    assert all(axs[1].spines[s].get_visible() for s in ("top", "right"))
    epl.goodness_arrow(axs[0], "higher = better")
    assert epl.two_tier_label("Method", "n=8") == "Method\nn=8"

    for n, ax in enumerate(axs):
        ax.annotate(**epl.subplot_labels(n, "a"))
    out = os.path.join(HERE, "test_figure_style.png")
    DPI = 150
    fig.savefig(out, dpi=DPI)

    # --- panel_crops: one padded box per lettered panel, within the saved image --
    # Boxes live in the SAVED png's pixel space, so pass the dpi you saved at
    # (default consults rcParams savefig.dpi).
    boxes = epl.panel_crops(fig, dpi=DPI)
    assert set(boxes) == {"a", "b"}, boxes
    from PIL import Image

    W, H = Image.open(out).size
    for L, (x0, y0, x1, y1) in boxes.items():
        assert 0 <= x0 < x1 <= W and 0 <= y0 < y1 <= H, (L, boxes[L], (W, H))
    plt.close(fig)
    print(f"panel_crops -> {boxes}")


if __name__ == "__main__":
    test_focal_palette()
    test_chart_helpers()
    print("OK: focal_palette / chart helpers / set_frame / panel_crops verified.")
