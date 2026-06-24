"""China provincial map (with South China Sea inset) — styled with EasyPlotLib.

The standard "study area over China" base map, drawn the compliant way:

* a main axis showing the mainland with provincial boundaries from :mod:`cnmaps`
  (``get_adm_maps`` — the correct, up-to-date national outline; do **not** read a
  random ``country.shp``), and
* a small **South China Sea inset in the bottom-right corner** carrying the
  nine-dash line (南海九段线) — the conventional, publication-required layout for
  any map of China.

The nine-dash line ships *inside the province set* (cnmaps attaches the South
China Sea islands to Hainan, so ``get_adm_maps(level="省")`` already reaches
~3.8°N); the same ``china_map`` therefore draws both the main map and the inset.
Geometries are added with ``ax.add_geometries(geom, crs=PROJ, ...)``, which takes
the source CRS inline (cnmaps returns lon/lat with no CRS tag). Drop your own data
on the main axis with ``ax.scatter(lon, lat, transform=PROJ)`` etc.

Dependencies beyond EasyPlotLib: ``cartopy``, ``cnmaps``.

Run::

    python examples/maps/china_provinces.py   # writes china_provinces.{pdf,png}
"""

import os

import cartopy.crs as ccrs
import matplotlib.pyplot as plt
import numpy as np

import EasyPlotLib as epl

HERE = os.path.dirname(__file__)
PROJ = ccrs.PlateCarree()

EXTENTS_MAIN = [70, 140, 10, 60]   # whole country, mainland-framed
EXTENTS_SUB = [105, 120, 2, 25]    # South China Sea / nine-dash line


def _draw_china(ax, china_map, lw=0.5):
    ax.add_geometries(china_map.geometry, crs=PROJ, facecolor="none",
                      edgecolor="black", linewidth=lw)


def main():
    # Square-ish single Nature column — a projected map should not be stretched.
    epl.journal_style("nat1", base_style="nature", ratio=1.0)

    from cnmaps import get_adm_maps

    china_map = get_adm_maps(level="省", engine="geopandas")

    fig, ax = plt.subplots(subplot_kw={"projection": PROJ})
    _draw_china(ax, china_map)

    # Example payload: a few station markers (replace with your data).
    rng = np.random.default_rng(0)
    lon = rng.uniform(80, 122, 25)
    lat = rng.uniform(22, 48, 25)
    ax.scatter(lon, lat, s=10, color=epl.SEMANTIC["blue_main"],
               edgecolor="white", linewidth=0.3, transform=PROJ, zorder=5)

    ax.set_extent(EXTENTS_MAIN, crs=PROJ)

    gl = ax.gridlines(draw_labels=True, color="none", linestyle="dotted",
                      transform=PROJ)
    gl.top_labels = gl.right_labels = False
    gl.rotate_labels = False
    epl.cartopy_plot_tickmarks(ax, gl)

    # South China Sea inset, bottom-right corner, carrying the nine-dash line.
    sub = ax.inset_axes((0.825, 0.0, 0.235, 0.235), projection=PROJ)
    _draw_china(sub, china_map)
    sub.set_extent(EXTENTS_SUB, crs=PROJ)
    sub.set_xticks([])
    sub.set_yticks([])
    for spine in sub.spines.values():
        spine.set_linewidth(0.5)

    out = os.path.join(HERE, "china_provinces")
    paths = epl.save_pub(fig, out, formats=("pdf", "png"))
    plt.close(fig)
    print("wrote", *paths)


if __name__ == "__main__":
    main()
