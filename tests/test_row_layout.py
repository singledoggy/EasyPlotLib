"""Regression test for the content-driven row layout helpers.

geo_aspect / row_layout / clamp_colorbars replace the hand-tuned
``inverted_aspect_ratio`` and ``width_ratios`` in a single row of maps + plots.
The core claim: with ``width_ratios`` ∝ aspect and ``inverted_aspect_ratio`` from
``row_layout``, every panel ends up WIDTH-limited (fills its column → no
inter-panel gaps) and the panels share one height.

Run:  python tests/test_row_layout.py
"""

import os

import numpy as np
import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.cm import ScalarMappable
from matplotlib.colors import Normalize

import EasyPlotLib as epl

HERE = os.path.dirname(os.path.abspath(__file__))


# --- geo_aspect: width/height = Δlon·cos(lat)/Δlat -------------------------------
def test_geo_aspect():
    # at the equator (lat_ref=0): cos = 1 → pure Δlon/Δlat
    assert abs(epl.geo_aspect(0, 10, -5, 5, lat_ref=0.0) - 1.0) < 1e-9
    assert abs(epl.geo_aspect(0, 20, -5, 5, lat_ref=0.0) - 2.0) < 1e-9
    # default lat_ref = box centre, so cos is evaluated there
    assert abs(epl.geo_aspect(0, 10, 0, 10) - np.cos(np.deg2rad(5.0))) < 1e-9
    # 60°N, Δlon=Δlat=1: aspect = cos(60) = 0.5
    assert abs(epl.geo_aspect(0, 1, 59.5, 60.5, lat_ref=60.0) - np.cos(np.deg2rad(60.0))) < 1e-9
    # order within a pair doesn't matter
    assert epl.geo_aspect(10, 0, 10, 0) == epl.geo_aspect(0, 10, 0, 10)
    # degenerate extent rejected
    for bad in [(0, 0, 0, 10), (0, 10, 5, 5)]:
        try:
            epl.geo_aspect(*bad)
        except ValueError:
            pass
        else:
            raise AssertionError(f"degenerate extent {bad} should raise")


# --- row_layout: width_ratios ∝ aspect, inverted = 1/Σaspect + vmargin ----------
def test_row_layout_formula():
    a = [1.33, 0.95, 0.95]
    lay = epl.row_layout(a, vmargin=0.10)
    assert lay["width_ratios"] == a
    assert abs(lay["inverted_aspect_ratio"] - (1.0 / sum(a) + 0.10)) < 1e-12
    # reproduces the hand-tuned 0.42 of fig_wrf_config_native within 0.02
    assert abs(lay["inverted_aspect_ratio"] - 0.42) < 0.02
    # positivity is enforced
    for bad in [[], [1.0, -1.0], [0.0, 2.0]]:
        try:
            epl.row_layout(bad)
        except ValueError:
            pass
        else:
            raise AssertionError(f"bad aspects {bad} should raise")


# --- end-to-end: panels come out WIDTH-limited and same height ------------------
def _build_row(aspects, inverted, width_ratios):
    epl.journal_style("nat2", palette="nature", inverted_aspect_ratio=inverted, apply=True)
    fig, axs = plt.subplots(1, 3, layout="constrained",
                            gridspec_kw=dict(width_ratios=width_ratios))
    cbs = []
    for n, (ax, asp) in enumerate(zip(axs, aspects)):
        ny, nx = 100, int(round(100 * asp))
        im = ax.imshow(np.random.rand(ny, nx), origin="lower",
                       extent=(0, asp, 0, 1), aspect="equal", vmin=0, vmax=1)
        cb = None
        if n >= 1:  # a = no colourbar, b/c = colourbar (mirrors the real figures)
            cb = fig.colorbar(ScalarMappable(Normalize(0, 1), im.cmap), ax=ax,
                              fraction=0.046, pad=0.04)
        cbs.append(cb)
    fig.canvas.draw()
    heights = [ax.get_position().height for ax in axs]
    return fig, axs, cbs, heights


def test_panels_width_limited_and_equal_height():
    # A wide panel + two square ones (like d01 + two d02 nests) so the
    # equal-height claim is non-trivial.
    a = [1.6, 1.0, 1.0]
    lay = epl.row_layout(a)

    # GOOD: row_layout height → every panel WIDTH-limited (fills its column) and
    # all three share one height.
    fig, axs, cbs, h_good = _build_row(a, lay["inverted_aspect_ratio"], lay["width_ratios"])
    spread_good = max(h_good) - min(h_good)
    w_a_good = axs[0].get_position().width   # panel 'a' fills its column when width-limited

    # clamp_colorbars: each colourbar height matches its panel height.
    epl.clamp_colorbars(fig, (axs[1], cbs[1]), (axs[2], cbs[2]))
    for ax, cb in ((axs[1], cbs[1]), (axs[2], cbs[2])):
        rh = cb.ax.get_position().height / ax.get_position().height
        assert abs(rh - 1.0) < 0.06, f"colourbar not clamped to panel height: {rh:.3f}"
    fig.savefig(os.path.join(HERE, "test_row_layout_good.png"), dpi=120)
    plt.close(fig)

    # BAD: a too-SHORT figure makes panels HEIGHT-limited → each shrinks inside its
    # column and sits centred with side gaps (panel 'a' no longer fills its column).
    fig_b, axs_b, _, _ = _build_row(a, 0.12, lay["width_ratios"])
    w_a_bad = axs_b[0].get_position().width
    plt.close(fig_b)

    print(f"GOOD: height spread={spread_good:.4f}, panel-a width frac={w_a_good:.3f}; "
          f"BAD(short): panel-a width frac={w_a_bad:.3f}")
    # width_ratios ∝ aspect → equal heights
    assert spread_good < 0.02, f"row_layout should equalise heights, got {h_good}"
    # row_layout makes panels fill their columns; a too-short figure leaves gaps
    assert w_a_good > w_a_bad + 0.05, (
        f"row_layout panels should fill columns more than a short figure: "
        f"{w_a_good:.3f} vs {w_a_bad:.3f}")


if __name__ == "__main__":
    test_geo_aspect()
    test_row_layout_formula()
    test_panels_width_limited_and_equal_height()
    print("OK: geo_aspect / row_layout / clamp_colorbars verified.")
