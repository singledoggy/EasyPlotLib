"""China provincial map on a cartopy axis — publication-styled with EasyPlotLib.

The standard "study area over China" base map: province boundaries from
:mod:`cnmaps` (``get_adm_maps`` — the correct, up-to-date national outline; do
**not** read a random ``country.shp``) on a :class:`cartopy.crs.PlateCarree`
axis, with clean degree tick labels via :func:`EasyPlotLib.cartopy_plot_tickmarks`.

Drop your own data on top: ``ax.scatter(lon, lat, transform=ccrs.PlateCarree())``,
``ax.contourf(...)``, station markers, etc.

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


def main():
    # Square-ish single Nature column — a map should not be stretched.
    epl.journal_style("nat1", base_style="nature", ratio=1.0)

    crs = ccrs.PlateCarree()
    fig, ax = plt.subplots(subplot_kw={"projection": crs})

    from cnmaps import get_adm_maps

    china = get_adm_maps(level="省", engine="geopandas")
    china.plot(ax=ax, edgecolor="black", facecolor="none", linewidth=0.4)

    # Example payload: a few station markers (replace with your data).
    rng = np.random.default_rng(0)
    lon = rng.uniform(80, 122, 25)
    lat = rng.uniform(22, 48, 25)
    ax.scatter(lon, lat, s=10, color=epl.SEMANTIC["blue_main"],
               edgecolor="white", linewidth=0.3, transform=crs, zorder=5)

    ax.set_extent([72, 136, 16, 54], crs=crs)

    gl = ax.gridlines(draw_labels=True, color="none", linestyle="dotted",
                      transform=crs)
    gl.top_labels = gl.right_labels = False
    gl.rotate_labels = False
    epl.cartopy_plot_tickmarks(ax, gl)

    out = os.path.join(HERE, "china_provinces")
    paths = epl.save_pub(fig, out, formats=("pdf", "png"))
    plt.close(fig)
    print("wrote", *paths)


if __name__ == "__main__":
    main()
