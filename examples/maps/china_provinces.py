"""China provincial map with a colour-mapped field — styled with EasyPlotLib.

The standard "gridded variable over China" figure, drawn the compliant way:

* a main axis showing a continuous field (here a synthetic lon/lat grid — swap in
  your own temperature / precipitation / concentration array) drawn with
  ``ax.pcolormesh(..., cmap=epl.COLORMAPS["sequential"], transform=PROJ)`` and
  **clipped to the national outline** so colour only appears over land,
* provincial boundaries from :mod:`cnmaps` (``get_adm_maps`` — the correct,
  up-to-date national outline) drawn on top, and
* a small **South China Sea inset in the bottom-right corner** carrying the
  nine-dash line (南海九段线) — the publication-required layout for any map of China.

Two things make this publication-grade:

1. **Clip the field to China.** ``get_adm_maps(level="省", engine="geopandas")``
   returns a GeoDataFrame; ``MapPolygon(prov.geometry.union_all())`` fuses the
   provinces into one boundary that :func:`cnmaps.clip_pcolormesh_by_map` uses as a
   clip path, so the ``pcolormesh`` rectangle is trimmed to the coastline.

2. **Make the colourbar match the MAP height, not the cell.** A geographic axis uses
   ``set_aspect("equal")``, so the drawn map is shorter than the grid cell matplotlib
   allotted it (Δlon ≠ Δlat). ``fig.colorbar`` otherwise sizes the bar to the *cell*
   and it stands taller than the map. The fix: let the constrained-layout engine place
   the bar, ``fig.canvas.draw()``, freeze the layout, then clamp the colourbar axes'
   ``y0``/height to the map's drawn ``get_position()`` (horizontal placement is kept).
   See ``tests/test_map_aspect_colorbar.py`` for the standalone lesson + regression.

The nine-dash line ships *inside the province set* (cnmaps attaches the South China
Sea islands to Hainan, so ``get_adm_maps(level="省")`` already reaches ~3.8°N); the
same ``prov`` therefore draws both the main boundaries and the inset. Geometries are
added with ``ax.add_geometries(geom, crs=PROJ, ...)``, which takes the source CRS
inline (cnmaps returns lon/lat with no CRS tag).

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


def _draw_china(ax, prov, lw=0.4):
    """Provincial boundaries (and, in the inset, the nine-dash line)."""
    ax.add_geometries(prov.geometry, crs=PROJ, facecolor="none",
                      edgecolor="black", linewidth=lw)


def _demo_field():
    """A smooth synthetic field on the lon/lat grid — replace with your data."""
    lon = np.linspace(EXTENTS_MAIN[0], EXTENTS_MAIN[1], 141)
    lat = np.linspace(EXTENTS_MAIN[2], EXTENTS_MAIN[3], 101)
    LO, LA = np.meshgrid(lon, lat)
    data = np.sin(LO / 12) * np.cos(LA / 9) + 0.4 * np.cos(LO / 5)
    return lon, lat, data


def main():
    # Square-ish single Nature column — a projected map should not be stretched.
    epl.journal_style("nat1", base_style="nature", ratio=1.0)

    from cnmaps import get_adm_maps, clip_pcolormesh_by_map, MapPolygon

    prov = get_adm_maps(level="省", engine="geopandas")
    # One fused boundary to use as the clip path for the field.
    china_outline = MapPolygon(prov.geometry.union_all())

    fig, ax = plt.subplots(subplot_kw={"projection": PROJ}, layout="constrained")

    # 1) Colour-mapped field, clipped to the national outline.
    lon, lat, data = _demo_field()
    mesh = ax.pcolormesh(lon, lat, data, cmap=epl.COLORMAPS["sequential"],
                         shading="auto", transform=PROJ, rasterized=True)
    clip_pcolormesh_by_map(mesh, china_outline)

    # 2) Boundaries on top.
    _draw_china(ax, prov)

    ax.set_extent(EXTENTS_MAIN, crs=PROJ)

    # lon/lat graticule + degree ticks on x and y (cartopy equivalent of salem's
    # m.set_lonlat_contours(add_xtick=True, add_ytick=True, linewidth=0.4)).
    gl = ax.gridlines(draw_labels=True, color="gray", linewidth=0.4,
                      linestyle="dotted", transform=PROJ)
    gl.top_labels = gl.right_labels = False
    gl.rotate_labels = False
    epl.cartopy_plot_tickmarks(ax, gl)

    # 3) Colourbar — placed by the layout engine, then clamped to the map height.
    cb = fig.colorbar(mesh, ax=ax, fraction=0.046, pad=0.02, aspect=30,
                      extend="both")
    cb.set_label("value (units)")

    # 4) South China Sea inset, bottom-right corner, carrying the nine-dash line.
    sub = ax.inset_axes((0.825, 0.0, 0.235, 0.235), projection=PROJ)
    _draw_china(sub, prov)
    sub.set_extent(EXTENTS_SUB, crs=PROJ)
    sub.set_xticks([])
    sub.set_yticks([])
    for spine in sub.spines.values():
        spine.set_linewidth(0.5)

    # Freeze the layout and clamp the colourbar's height/bottom to the drawn map,
    # so the bar matches the map height instead of the (taller) grid cell.
    fig.canvas.draw()
    fig.set_layout_engine("none")
    pm, pc = ax.get_position(), cb.ax.get_position()
    cb.ax.set_position([pc.x0, pm.y0, pc.width, pm.height])

    out = os.path.join(HERE, "china_provinces")
    paths = epl.save_pub(fig, out, formats=("pdf", "png"))
    plt.close(fig)
    print("wrote", *paths)


if __name__ == "__main__":
    main()
