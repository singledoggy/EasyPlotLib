"""
Map aspect ratio vs colourbar height — lesson + regression check.

THE LESSON (learned the hard way on a WRF d01/d02 + land-use + irrigation row):

  * A geographic panel is almost never 1:1. With ``ax.set_aspect("equal")`` (every
    map: cartopy, salem, or a plain ``imshow`` of a lon/lat field) the AXES BOX
    shrinks to the data's width/height ratio. Δlon and Δlat differ (and projection
    distorts further), so the drawn map is shorter (or narrower) than the grid cell
    matplotlib allocated for it.

  * ``fig.colorbar(mappable, ax=ax)`` sizes the colourbar to the CELL, not to the
    shrunk map. Result: the colourbar stands taller than the map it annotates — even
    though nothing "overlaps". This is the bug this test reproduces.

  * In a single ROW of maps with DIFFERENT aspects (e.g. a wide parent domain next to
    square nests), equal-width cells make the wide panel short and the square panels
    tall → the row looks ragged.

THE FIXES (both demonstrated and asserted below):

  A. EQUAL PANEL HEIGHTS: give each map a column ``width_ratio`` proportional to its
     own aspect (= width/height). Then every cell matches its map's aspect and all
     maps render at the same height.

  B. COLOURBAR = MAP HEIGHT: let the layout engine place the colourbars (so they sit
     to the right with no overlap), then ``fig.canvas.draw()``, FREEZE the layout
     (``fig.set_layout_engine("none")``) and clamp each colourbar axes' ``y0``/height
     to its map's drawn ``get_position()``. Only the height/bottom change, so the
     horizontal placement the engine chose is preserved.

Run:  python tests/test_map_aspect_colorbar.py
Produces tests/test_map_aspect_colorbar_before.png and _after.png for eyeballing,
and asserts the colourbar/map height ratio is ~1.7 before and ~1.0 after.
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
RNG = np.random.default_rng(0)


# --- synthetic "maps": random smooth fields on lon/lat boxes whose Δlon != Δlat ----
def smooth_field(ny, nx, sigma=6):
    """A random field smoothed by FFT so it looks map-like, not white noise."""
    a = RNG.standard_normal((ny, nx))
    fy = np.exp(-0.5 * (np.fft.fftfreq(ny)[:, None] * ny / sigma) ** 2)
    fx = np.exp(-0.5 * (np.fft.fftfreq(nx)[None, :] * nx / sigma) ** 2)
    a = np.fft.ifft2(np.fft.fft2(a) * (fy * fx)).real
    a -= a.min()
    return a / a.max()


# (name, lon0, lon1, lat0, lat1) — a wide parent + two square-ish nests, like d01/d02.
BOXES = [
    ("parent (wide)", 103.0, 129.0, 27.0, 43.0),   # Δlon 26, Δlat 16 -> aspect 1.62
    ("nest A",        111.5, 121.5, 31.5, 40.0),    # Δlon 10, Δlat 8.5 -> aspect 1.18
    ("nest B",        111.5, 121.5, 31.5, 40.0),
]


def box_aspect(b):
    """Width/height of the lon/lat box (the value to feed width_ratios)."""
    _, lo0, lo1, la0, la1 = b
    return (lo1 - lo0) / (la1 - la0)


def draw_map(ax, b):
    _, lo0, lo1, la0, la1 = b
    data = smooth_field(120, int(120 * box_aspect(b)))
    im = ax.imshow(data, origin="lower", extent=(lo0, lo1, la0, la1),
                   cmap=epl.COLORMAPS["sequential"], vmin=0, vmax=1, aspect="equal")
    ax.set_xticks(np.linspace(lo0, lo1, 4).round())
    ax.set_yticks(np.linspace(la0, la1, 4).round())
    ax.tick_params(labelsize=6)
    return im


def heights(fig, ax_map, cb):
    """(map height, colourbar height) in figure fraction, after a draw."""
    fig.canvas.draw()
    return ax_map.get_position().height, cb.ax.get_position().height


# ----------------------------------------------------------------------------------
def build(fix_aspect, clamp_cbar, path, title):
    """Build the 3-map row. fix_aspect -> width_ratios; clamp_cbar -> fix B."""
    epl.journal_style("nat2", palette="nature", inverted_aspect_ratio=0.40, apply=True)
    wr = [box_aspect(b) for b in BOXES] if fix_aspect else [1, 1, 1]
    fig, axs = plt.subplots(1, 3, layout="constrained",
                            gridspec_kw=dict(width_ratios=wr))
    cbs = []
    for n, (ax, b) in enumerate(zip(axs, BOXES)):
        im = draw_map(ax, b)
        ax.set_title(b[0], fontsize=7)
        ax.annotate(**epl.subplot_labels(n, "a"))
        extend = "max" if n == 2 else "neither"   # mimic the real irrigation bar
        cb = fig.colorbar(ScalarMappable(Normalize(0, 1), im.cmap), ax=ax,
                          fraction=0.05, pad=0.02, aspect=32, extend=extend)
        cb.ax.tick_params(labelsize=6)
        cbs.append(cb)

    if clamp_cbar:
        fig.canvas.draw()
        fig.set_layout_engine("none")
        for ax, cb in zip(axs, cbs):
            pm, pc = ax.get_position(), cb.ax.get_position()
            cb.ax.set_position([pc.x0, pm.y0, pc.width, pm.height])

    fig.suptitle(title, fontsize=8)
    fig.savefig(path, dpi=200)
    ratios = [heights(fig, ax, cb)[1] / heights(fig, ax, cb)[0] for ax, cb in zip(axs, cbs)]
    map_hs = [ax.get_position().height for ax in axs]
    plt.close(fig)
    return ratios, map_hs


if __name__ == "__main__":
    before_path = os.path.join(HERE, "test_map_aspect_colorbar_before.png")
    after_path = os.path.join(HERE, "test_map_aspect_colorbar_after.png")

    # BEFORE: equal-width cells, colourbars sized to the cell (the bug).
    r_before, h_before = build(fix_aspect=False, clamp_cbar=False,
                               path=before_path, title="BEFORE: equal cells, cbar=cell height")
    # AFTER: width_ratios ~ aspect (equal map heights) + colourbar clamped to map.
    r_after, h_after = build(fix_aspect=True, clamp_cbar=True,
                             path=after_path, title="AFTER: width_ratios~aspect + clamped cbar")

    print(f"colourbar/map height ratio  BEFORE = {[round(x, 2) for x in r_before]}")
    print(f"colourbar/map height ratio  AFTER  = {[round(x, 2) for x in r_after]}")
    print(f"map heights (fig frac)      BEFORE = {[round(x, 3) for x in h_before]}")
    print(f"map heights (fig frac)      AFTER  = {[round(x, 3) for x in h_after]}")
    print("saved", before_path)
    print("saved", after_path)

    # Fix B: colourbars must match their map height (the whole point).
    assert max(r_before) > 1.25, f"expected tall colourbars before fix, got {r_before}"
    assert all(abs(r - 1.0) < 0.06 for r in r_after), \
        f"colourbars not clamped to map height: {r_after}"
    # Fix A: width_ratios ~ aspect makes the three maps nearly the same height
    # (BEFORE spread ~0.075 -> AFTER ~0.02). NOTE the equality is only exact when the
    # figure is tall enough that every map is WIDTH-limited; a very wide/short figure
    # pushes the square-ish nests into being HEIGHT-limited, so a small residual remains.
    assert (max(h_before) - min(h_before)) > 2 * (max(h_after) - min(h_after)), \
        f"width_ratios~aspect should shrink the height spread: {h_before} -> {h_after}"
    assert max(h_after) - min(h_after) < 0.03, \
        f"map heights not equalised by width_ratios~aspect: {h_after}"
    print("OK: colourbars clamped to map height; panel heights equalised.")
