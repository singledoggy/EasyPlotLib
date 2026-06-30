"""Multi-row grid of equal-aspect maps (+ a bar row) — styled with EasyPlotLib.

The hard layout case that ``row_layout`` does *not* cover: a **grid** of
equal-aspect cartopy maps stacked in several rows, optionally mixed with a row of
ordinary panels (here grouped bars).  A worked, self-contained precedent for the
``sci-figure`` skill §7a.

The maps are drawn **in the WRF native projection itself** (the WRF default), read
straight from the bundled ``wrfout`` the way ``wrf_field.py`` does —
``salem.open_wrf_dataset(...)`` decodes the Lambert CRS, and
``ds[["south_north", "west_east"]].salem.cartopy()`` hands back a ready Cartopy
projection.  (``wrf_field.py`` also shows how to *cache* that CRS as a pickle so
you skip re-reading the 60 MB file; we keep it inline here — this example is
about the layout.)  Crucially the field is plotted **on the grid's own projected
x/y metres** (``salem.grid.xy_coordinates``) with ``transform=wrf_proj`` — the
data is NOT reprojected to lon/lat; the model grid is the axes' coordinate
system.  Only the vector overlays (coastline/state lines) and the lon/lat
graticule labels are reprojected, which is correct for vectors.

Four things bite in this layout, and this file shows the fix for each:

1. **``hspace`` will not close the gap between the two map rows.** An equal-aspect
   map shrinks inside its (taller) grid cell and centres vertically, so the
   *leftover whitespace* — not ``constrained_layout``'s ``hspace`` — sets the
   inter-row gap.  Fix: let constrained layout solve the **X** geometry (column
   widths + colourbar slots), then freeze it and **restack the rows by hand**,
   keeping each map's *drawn* width & height (change only ``y0``) so the aspect is
   never re-applied and no whitespace creeps back.  Gaps become explicit,
   tunable constants (``ROW_GAP``, ``BAR_GAP``).

2. **Shared colourbars belong at the figure EDGES, never between columns.** A
   vertical colourbar's label is rotated and points sideways, so an *interior*
   bar prints its label on top of the next map.  One shared bar per scale at an
   outer edge — sequential ``Blues`` on the LEFT, diverging ``BrBG`` on the
   RIGHT — keeps every label in the margin.  Each spans both map rows.

3. **An edge colourbar packed by the solver crowds the panel's own tick labels**
   (the left bar lands on the maps' latitude labels).  When repositioning by
   hand, reserve ``LAT_PAD`` between the bar and the left column.

4. **``UserWarning: constrained_layout not applied … collapsed to zero`` is
   benign** once you override positions — equal-aspect maps + spanning colourbars
   over-constrain the solver, but you only consume its X solution.  Silence it.

Dependencies beyond EasyPlotLib: ``salem``, ``cartopy``.

Run::

    python examples/maps/multirow_map_grid.py   # writes multirow_map_grid.{pdf,png}
"""

import os
import warnings

import cartopy.feature as cfeature
import matplotlib.pyplot as plt
from matplotlib.cm import ScalarMappable
from matplotlib.colors import Normalize
import numpy as np

import EasyPlotLib as epl

HERE = os.path.dirname(__file__)
WRFOUT = os.path.join(HERE, "data", "wrfout_d01_2000-01-24_12:00:00")

PERIODS = ["Period 1", "Period 2"]
BAR_X = ["Q1", "Q2", "Q3", "Q4"]

# ---- layout knobs (figure-fraction units) ---------------------------------
TOP = 0.955        # top edge of the upper map row
ROW_GAP = 0.045    # vertical gap between the two map rows
BAR_GAP = 0.085    # vertical gap between bottom map row and the bar row
BAR_ASPECT = 0.6   # bar-panel height / width
LAT_PAD = 0.05     # room reserved left of column-0 maps for their lat labels


# ============================================================
# WRF grid + native projection, and synthetic fields on that grid
# ============================================================
def load_wrf_grid(wrfout=WRFOUT):
    """Native projection + the grid's projected x/y metres, from the wrfout.

    ``wrf_field.py`` shows how to *cache* the CRS so you don't re-read the file;
    kept inline here because this example is about the multi-row layout.
    """
    import salem

    ds = salem.open_wrf_dataset(wrfout)
    x2d, y2d = ds.salem.grid.xy_coordinates          # projected metres
    wrf_proj = ds[["south_north", "west_east"]].salem.cartopy()
    ds.close()
    return np.asarray(x2d, float), np.asarray(y2d, float), wrf_proj


def demo_rows(x2d, y2d):
    """Two periods of synthetic (A, B, Δ=B−A) fields on the wrfout grid."""
    rng = np.random.default_rng(0)
    cx = 0.5 * (x2d.min() + x2d.max())
    cy = 0.5 * (y2d.min() + y2d.max())
    w = 0.18 * (x2d.max() - x2d.min())

    def blob(scale, dx, dy):
        g = np.exp(-(((x2d - cx - dx) / w) ** 2 + ((y2d - cy - dy) / (w * 0.8)) ** 2))
        return scale * (g + 0.12 * rng.random(x2d.shape))

    rows = []
    for s in (40.0, 55.0):
        a = blob(s, -0.35 * w, -0.3 * w)
        b = blob(s * 1.18, 0.15 * w, 0.0)
        rows.append((a, b, b - a))
    return rows


def demo_bars():
    return np.array([90, 140, 160, 120], float), np.array([70, 110, 130, 100], float)


# ============================================================
# Panels
# ============================================================
def draw_map(ax, x2d, y2d, field, wrf_proj, cmap, norm, show_x, show_y):
    # field is on the grid's own projected x/y metres and the axes IS that
    # projection -> transform=wrf_proj (identity); the data is never reprojected.
    ax.pcolormesh(x2d, y2d, field, cmap=cmap, norm=norm,
                  shading="auto", transform=wrf_proj, rasterized=True)
    ax.add_feature(cfeature.COASTLINE, linewidth=0.4, edgecolor="0.25")
    try:
        ax.add_feature(cfeature.STATES, linewidth=0.3, edgecolor="0.55")
    except Exception as exc:  # Natural-Earth states may be unavailable offline
        print(f"(states feature skipped: {exc})")
    ax.set_xlim(x2d.min(), x2d.max())   # limit to the model domain (projected)
    ax.set_ylim(y2d.min(), y2d.max())

    # graticule labels via the gridliner — `set_xticks`/`LongitudeFormatter` only
    # work on PlateCarree/Mercator, not Lambert. Lon labels on the bottom map
    # row, lat on the left column.
    gl = ax.gridlines(draw_labels=True, x_inline=False, y_inline=False,
                      linewidth=0.3, color="0.85", alpha=0.7)
    gl.top_labels = gl.right_labels = False
    gl.bottom_labels = show_x
    gl.left_labels = show_y
    gl.rotate_labels = False
    gl.xlabel_style = {"size": 5}
    gl.ylabel_style = {"size": 5}


def bar_panel(ax, ax2, x, irr, nirr, y_label):
    w = 0.4
    ax.bar(x - w / 2, irr, w, label="B", color=epl.SEMANTIC["red_strong"])
    ax.bar(x + w / 2, nirr, w, label="A", color=epl.SEMANTIC["blue_main"])
    ax.set_xticks(x)
    ax.set_xticklabels(BAR_X)
    ax.set_ylabel(y_label)
    ax.legend(frameon=False, fontsize=6, loc="upper left")

    delta = irr - nirr
    ax2.axhline(0.0, color=epl.SEMANTIC["neutral_mid"], linewidth=0.6, zorder=1)
    ax2.plot(x, delta, "-o", color=epl.SEMANTIC["neutral_black"],
             markersize=3, linewidth=1.0, label="B − A", zorder=3)
    ax2.set_ylim(-1.25 * abs(delta).max(), 1.25 * abs(delta).max())
    ax2.legend(frameon=False, fontsize=6, loc="upper right")


# ============================================================
# Figure
# ============================================================
def main():
    x2d, y2d, wrf_proj = load_wrf_grid()
    rows = demo_rows(x2d, y2d)
    irr, nirr = demo_bars()

    # shared colour scales across both periods
    tot = np.stack([r[0] for r in rows] + [r[1] for r in rows])
    dlt = np.stack([r[2] for r in rows])
    norm_seq = Normalize(0.0, float(np.nanpercentile(tot, 99)))
    vlim = float(np.nanpercentile(np.abs(dlt), 99))
    norm_div = Normalize(-vlim, vlim)

    # --- figure: 3 rows (2 map rows + 1 bar row), 6-col grid for half spans ---
    epl.journal_style("nat2", base_style="nature", nrows=3, ncols=3,
                      inverted_aspect_ratio=0.92)
    fig = plt.figure(layout="constrained")
    fig.get_layout_engine().set(hspace=0.04, wspace=0.10)
    gs = fig.add_gridspec(3, 6, height_ratios=[4, 4, 3])

    map_axes = [[fig.add_subplot(gs[ri, c:c + 2], projection=wrf_proj)
                 for c in (0, 2, 4)] for ri in range(2)]
    ax_bar1 = fig.add_subplot(gs[2, 0:3])
    ax_bar2 = fig.add_subplot(gs[2, 3:6])

    # ---- rows 0-1: maps ----------------------------------------------------
    for ri, (a, b, d) in enumerate(rows):
        ax_a, ax_b, ax_d = map_axes[ri]
        show_x = ri == 1
        draw_map(ax_a, x2d, y2d, a, wrf_proj, "Blues", norm_seq, show_x, True)
        draw_map(ax_b, x2d, y2d, b, wrf_proj, "Blues", norm_seq, show_x, False)
        draw_map(ax_d, x2d, y2d, d, wrf_proj, "BrBG", norm_div, show_x, False)
        ax_a.set_title(f"A ({PERIODS[ri]})", fontsize=7)
        ax_b.set_title(f"B ({PERIODS[ri]})", fontsize=7)
        ax_d.set_title(f"Δ ({PERIODS[ri]})", fontsize=7)

    # PITFALL 2: two shared colourbars at the figure EDGES so their rotated
    # labels point outward into the margins, never onto a neighbouring map.
    blues_axes = [map_axes[0][0], map_axes[0][1], map_axes[1][0], map_axes[1][1]]
    delta_axes = [map_axes[0][2], map_axes[1][2]]
    cb_seq = fig.colorbar(ScalarMappable(cmap="Blues", norm=norm_seq),
                          ax=blues_axes, location="left", fraction=0.05,
                          pad=0.02, aspect=40, extend="max")
    cb_seq.set_label("value (units)", fontsize=6)
    cb_div = fig.colorbar(ScalarMappable(cmap="BrBG", norm=norm_div),
                          ax=delta_axes, location="right", fraction=0.05,
                          pad=0.02, aspect=40, extend="both")
    cb_div.set_label("B − A (units)", fontsize=6)
    for cb in (cb_seq, cb_div):
        cb.ax.tick_params(labelsize=5)
        cb.outline.set_linewidth(0.4)

    # ---- row 2: bars -------------------------------------------------------
    x = np.arange(4)
    ax_bar1_2 = ax_bar1.twinx()
    ax_bar2_2 = ax_bar2.twinx()
    bar_panel(ax_bar1, ax_bar1_2, x, irr, nirr, "metric 1")
    bar_panel(ax_bar2, ax_bar2_2, x, irr * 1e3, nirr * 1e3, "metric 2")

    # ---- panel labels (a)-(h) ----------------------------------------------
    for n, ax in enumerate(map_axes[0] + map_axes[1] + [ax_bar1, ax_bar2]):
        ax.annotate(**epl.subplot_labels(n, "a"))

    # ---- manual vertical layout (PITFALLS 1, 3, 4) -------------------------
    # PITFALL 4: the solver over-constrains (equal-aspect maps + spanning bars);
    # we override every position below, so its "collapsed to zero" gripe is moot.
    with warnings.catch_warnings():
        warnings.filterwarnings("ignore", message="constrained_layout not applied")
        fig.canvas.draw()
    fig.set_layout_engine("none")

    # PITFALL 1: keep each map's DRAWN width & height (aspect untouched ->
    # no re-shrink) and only restack the two rows vertically with explicit gaps.
    r0 = [a.get_position() for a in map_axes[0]]
    r1 = [a.get_position() for a in map_axes[1]]
    h0 = max(p.height for p in r0)
    h1 = max(p.height for p in r1)
    for a, p in zip(map_axes[0], r0):
        a.set_position([p.x0, TOP - h0, p.width, h0])
    y1_top = (TOP - h0) - ROW_GAP
    for a, p in zip(map_axes[1], r1):
        a.set_position([p.x0, y1_top - h1, p.width, h1])

    # clamp each edge colourbar to span both restacked map rows; PITFALL 3:
    # shove the LEFT bar out by LAT_PAD so column-0's lat labels have room.
    for j, cb in ((0, cb_seq), (2, cb_div)):
        p_top = map_axes[0][j].get_position()
        p_bot = map_axes[1][j].get_position()
        pc = cb.ax.get_position()
        x0 = (p_top.x0 - LAT_PAD - pc.width) if j == 0 else pc.x0
        cb.ax.set_position([x0, p_bot.y0, pc.width, p_top.y1 - p_bot.y0])

    # bar row: span the map columns, sit BAR_GAP below the bottom map row
    fw_in, fh_in = fig.get_size_inches()
    x_left = map_axes[0][0].get_position().x0
    x_right = map_axes[0][2].get_position().x1
    gap = 0.15 * (x_right - x_left)
    half_w = (x_right - x_left - gap) / 2.0
    bar_h = (half_w * fw_in * BAR_ASPECT) / fh_in
    bar_top = (y1_top - h1) - BAR_GAP
    for ax_host, ax_tw, x0 in (
        (ax_bar1, ax_bar1_2, x_left),
        (ax_bar2, ax_bar2_2, x_left + half_w + gap),
    ):
        rect = [x0, bar_top - bar_h, half_w, bar_h]
        ax_host.set_position(rect)
        ax_tw.set_position(rect)   # keep the twin axis in sync

    out = os.path.join(HERE, "multirow_map_grid")
    paths = epl.save_pub(fig, out, formats=("pdf", "png"))
    plt.close(fig)
    print("wrote", *paths)


if __name__ == "__main__":
    main()
