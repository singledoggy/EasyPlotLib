"""WRF vertical cross section — ``vertcross`` over the bundled sample domain.

The everyday "slice through the atmosphere" figure: pick a start/end lat-lon,
interpolate a 3-D WRF field onto that vertical plane with wrf-python's
``vertcross``, and draw it in height coordinates with the terrain filled in
underneath — in EasyPlotLib's journal style.

Workflow (mirrors the wrf-python manual and the urban-PM cross-section script
this example is adapted from):

1. **Pick the transect.** Two ``CoordPair(lat, lon)`` end points.
2. **Interpolate.** ``vertcross(field, z, wrfin=ncfile, start_point, end_point,
   latlon=True)`` returns a *(vertical × along-section)* ``DataArray`` whose
   ``xy_loc`` coordinate carries the lat/lon of every section point — that drives
   the x tick labels. ``z`` (geopotential height) is the vertical coordinate.
3. **In-plane circulation.** Project the horizontal wind (``ua``, ``va``) onto the
   section azimuth to get the along-section wind, pair it with vertical velocity
   ``wa`` (scaled up, since w ≪ u), and overlay it as a quiver.
4. **Terrain.** ``interpline(ter, …)`` gives the ground height along the section;
   ``fill_between`` masks the sub-surface. The lowest model cells that
   ``vertcross`` leaves NaN are back-filled with the first valid value per column
   so the field shading meets the terrain cleanly (the manual's trick).

The bundled sample is the 60×73 Lambert CONUS domain
(``examples/maps/data/wrfout_d01_2000-01-24_12:00:00``); the default transect runs
west→east across the central Appalachians at 37°N.

Dependencies beyond EasyPlotLib: ``wrf-python``, ``netCDF4``.

Run::

    python examples/maps/wrf_cross_section.py   # writes wrf_cross_section.{pdf,png}
"""

import os

import matplotlib.pyplot as plt
import numpy as np
from netCDF4 import Dataset
from wrf import ALL_TIMES, CoordPair, getvar, interpline, to_np, vertcross

import EasyPlotLib as epl

HERE = os.path.dirname(__file__)
WRFOUT = os.path.join(HERE, "data", "wrfout_d01_2000-01-24_12:00:00")

# Transect end points (lat, lon): a west->east slice across the Appalachians.
START = CoordPair(lat=37.0, lon=-88.0)
END = CoordPair(lat=37.0, lon=-72.0)
ZTOP_KM = 10.0  # plot ceiling, km
WSCALE = 50.0  # blow up vertical velocity so w (cm/s) shows against u (m/s)
QKEY = 20.0  # reference-arrow length in the quiver key, m/s


def _cross(field, z, ncfile):
    """vertcross with the shared transect + lat/lon metadata."""
    return vertcross(
        field, z, wrfin=ncfile, start_point=START, end_point=END,
        latlon=True, meta=True,
    )


def _fill_to_ground(cross_da):
    """Back-fill the NaN cells below each column with its first valid value.

    ``vertcross`` leaves the cells beneath the model surface as NaN; filling them
    lets the filled-contour field meet the terrain shading without a white gap.
    """
    arr = to_np(cross_da).copy()
    for i in range(arr.shape[-1]):
        col = arr[:, i]
        valid = np.flatnonzero(~np.isnan(col))
        if valid.size:
            arr[: valid[0], i] = col[valid[0]]
    return arr


def main():
    ncfile = Dataset(WRFOUT)
    t = ALL_TIMES  # average the section over every output time (cf. the
    #                reference script, which averages day by day)

    z = getvar(ncfile, "z", timeidx=t)  # geopotential height (m), the vertical
    ter = getvar(ncfile, "ter", timeidx=0)  # terrain height (m), time-invariant
    theta = getvar(ncfile, "theta", timeidx=t, units="K")
    rh = getvar(ncfile, "rh", timeidx=t)  # relative humidity (%)
    ua = getvar(ncfile, "ua", timeidx=t, units="m s-1")
    va = getvar(ncfile, "va", timeidx=t, units="m s-1")
    wa = getvar(ncfile, "wa", timeidx=t, units="m s-1")

    # Along-section horizontal wind: project (ua, va) onto the transect azimuth.
    dlat, dlon = END.lat - START.lat, END.lon - START.lon
    r = np.hypot(dlat, dlon)
    u_sec = (ua * dlon + va * dlat) / r

    # Interpolate onto the plane, then average over the Time dimension.
    theta_c = _cross(theta, z, ncfile).mean(dim="Time")
    rh_c = _cross(rh, z, ncfile).mean(dim="Time")
    u_c = _cross(u_sec, z, ncfile).mean(dim="Time")
    w_c = _cross(wa, z, ncfile).mean(dim="Time")
    ter_line = to_np(interpline(ter, wrfin=ncfile, start_point=START, end_point=END))

    # Shared section geometry: x = along-section index, y = height in km.
    xs = np.arange(theta_c.shape[-1])
    ys = to_np(theta_c.coords["vertical"]) / 1000.0
    ter_km = ter_line / 1000.0

    # Lat/lon tick labels from the xy_loc coordinate.
    pairs = to_np(theta_c.coords["xy_loc"])
    tick_idx = np.linspace(0, len(pairs) - 1, 5).astype(int)
    tick_lab = [f"{p.lat:.1f}°N\n{abs(p.lon):.1f}°W" for p in pairs[tick_idx]]

    panels = [
        dict(
            field=_fill_to_ground(theta_c),
            label="Potential temperature (K)",
            quiver=True,
        ),
        dict(
            field=_fill_to_ground(rh_c),
            label="Relative humidity (%)",
            quiver=False,
            vmin=0,
            vmax=100,
        ),
    ]

    # Aspect is a SUBPLOT property here, not a whole-figure one. `journal_style`
    # sizes the *figure*; for a 1×2 grid the per-panel shape is
    # ``figure_aspect × ncols/nrows``. Passing `nrows, ncols` makes each gridspec
    # *cell* ≈ golden — a good starting point. But we want the golden shape to be
    # the PLOT BOX itself, excluding the under-panel colourbar + tick labels, so a
    # correction pass below grows the figure to absorb those decorations.
    epl.journal_style("nat2", base_style="nature", nrows=1, ncols=2)
    fig, axs = plt.subplots(
        1, 2, figsize=plt.rcParams["figure.figsize"],
        layout="constrained", sharex=True, sharey=True,
    )

    shown = ys <= ZTOP_KM  # only scale colours to the visible height window
    for n, (ax, p) in enumerate(zip(axs, panels)):
        fld = p["field"]
        vmin = p.get("vmin", np.nanmin(fld[shown]))
        vmax = p.get("vmax", np.nanmax(fld[shown]))
        cf = ax.contourf(
            xs, ys, fld, levels=np.linspace(vmin, vmax, 21),
            cmap="rainbow", extend="both",
        )

        if p["quiver"]:
            sy, sx = slice(None, None, 3), slice(None, None, 2)  # thin the grid
            q = ax.quiver(
                xs[sx], ys[sy], to_np(u_c)[sy, sx], to_np(w_c)[sy, sx] * WSCALE,
                scale=320, width=0.004, headaxislength=3, color="k", zorder=6,
            )
            # Reference arrow just above the top-right corner (cf. the reference
            # script): arrow + plain "N m/s" telling the reader the wind scale.
            qk = ax.quiverkey(
                q, 0.86, 1.02, QKEY, f"{QKEY:g} m s$^{{-1}}$", labelpos="E",
                color="k", labelcolor="k", fontproperties={"size": 7},
            )
            qk.set_clip_on(False)  # don't clip the key above the axes

        # Terrain mask + crisp ground line.
        ax.fill_between(xs, 0, ter_km, facecolor="0.4", zorder=5)
        ax.plot(xs, ter_km, color="k", lw=0.6, zorder=6)

        ax.set_ylim(0, ZTOP_KM)
        ax.set_xlim(xs[0], xs[-1])
        ax.set_xticks(xs[tick_idx])
        ax.set_xticklabels(tick_lab)
        if n == 0:
            ax.set_ylabel("Height (km)")
        # Horizontal colourbar under each panel (cf. the reference script).
        # `pad` is a FRACTION of the panel, so matplotlib's ~0.15 default balloons
        # the gap on a tall panel. Keep it small and let constrained_layout place
        # the bar adaptively just below the (two-line) tick labels.
        fig.colorbar(cf, ax=ax, orientation="horizontal", aspect=35, pad=0.04,
                     label=p["label"])
        ax.annotate(**epl.subplot_labels(n, "a"))

    # Make the golden ratio apply to the DATA AXES, not the colourbar-inclusive
    # cell. The decorations (colourbar, its labels, the two-line x ticks) are
    # ~fixed in height, so each pass grows the figure by the plot box's height
    # deficit and lets constrained_layout re-flow; two or three passes converge.
    golden = (5.0**0.5 - 1.0) / 2.0
    for _ in range(4):
        fig.canvas.draw()
        fig_w, fig_h = fig.get_size_inches()
        box = axs[0].get_position()  # both panels share width + height
        w_ax, h_ax = box.width * fig_w, box.height * fig_h
        deficit = golden * w_ax - h_ax
        if abs(deficit) < 0.01:
            break
        fig.set_size_inches(fig_w, fig_h + deficit)

    out = os.path.join(HERE, "wrf_cross_section")
    paths = epl.save_pub(fig, out, formats=("pdf", "png"))
    plt.close(fig)
    print("wrote", *paths)


if __name__ == "__main__":
    main()
