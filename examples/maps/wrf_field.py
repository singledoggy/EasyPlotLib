"""WRF output field on its native projection — the cached-CRS workflow.

The everyday WRF figure: plot a model field (here 2-m temperature and total
precipitation) **on the model's own grid and projection**, drawn with
EasyPlotLib's journal style.

The trick is how the projection is obtained. A ``wrfout`` file is large and its
Lambert/Mercator/Polar metadata is buried in global attributes; you do not want
to re-open and re-parse it every time you draw. Instead:

1. **Extract once, cache.** ``salem.open_wrf_dataset(wrfout)`` returns an xarray
   Dataset in which ``salem`` has already decoded the WRF projection. Slicing
   ``[["south_north", "west_east"]]`` keeps only the two grid-coordinate
   variables — but those carry the *full* CRS (``MAP_PROJ``, ``TRUELAT1/2``,
   ``STAND_LON`` …). Pickling that tiny object gives a reusable CRS cache.

2. **Reuse.** ``pickle.load`` the cache and call ``xy_coord.salem.cartopy()`` to
   get a ready-to-use Cartopy projection — no need to touch the 60 MB wrfout.

3. **Plot.** Pass that one projection to every subplot
   (``subplot_kw={"projection": wrf_proj}``). Because the field arrays live on
   the ``south_north`` / ``west_east`` index grid, the correct ``transform`` for
   ``.plot()`` is ``wrf_proj`` itself — the cached CRS is the single source of
   truth for both the axes and the data.

The bundled sample is a 60×73 Lambert-conformal CONUS domain
(``examples/maps/data/wrfout_d01_2000-01-24_12:00:00``).

Dependencies beyond EasyPlotLib: ``salem``, ``cartopy``.

Run::

    python examples/maps/wrf_field.py   # writes wrf_field.{pdf,png}
                                        # + data/xy_coord.pkl on first run
"""

import os
import pickle

import matplotlib.pyplot as plt

import EasyPlotLib as epl

HERE = os.path.dirname(__file__)
WRFOUT = os.path.join(HERE, "data", "wrfout_d01_2000-01-24_12:00:00")
CACHE = os.path.join(HERE, "data", "xy_coord.pkl")


def load_xy_coord(wrfout=WRFOUT, cache=CACHE):
    """Return the cached WRF grid-coordinate Dataset (carries the full CRS).

    First call reads the wrfout once, keeps only ``south_north`` / ``west_east``
    and pickles them; later calls just unpickle that small object.
    """
    if os.path.exists(cache):
        with open(cache, "rb") as f:
            print(f"loaded CRS cache {cache}")
            return pickle.load(f)

    import salem

    xy_coord = salem.open_wrf_dataset(wrfout)[["south_north", "west_east"]]
    with open(cache, "wb") as f:
        pickle.dump(xy_coord, f)
    print(f"extracted CRS from {os.path.basename(wrfout)} -> {cache}")
    return xy_coord


def main():
    import salem

    # 1) + 2) cached CRS -> Cartopy projection (the whole point of this example).
    xy_coord = load_xy_coord()
    wrf_proj = xy_coord.salem.cartopy()

    # Two fields at the last timestep, on the native WRF grid.
    ds = salem.open_wrf_dataset(WRFOUT)
    t2c = ds["T2"].isel(time=-1) - 273.15  # 2-m temperature, °C
    precip = (ds["RAINNC"] + ds["RAINC"]).isel(time=-1)  # accumulated precip, mm

    panels = [
        dict(
            field=t2c,
            title="2-m temperature",
            cmap=epl.COLORMAPS["diverging"],
            label="°C",
            plot_kw=dict(center=0),
        ),
        dict(
            field=precip,
            title="Total precipitation",
            cmap=epl.COLORMAPS["sequential"],
            label="mm",
            plot_kw=dict(vmin=0),
        ),
    ]

    # One double-column Nature figure; two side-by-side maps.
    epl.journal_style("nat2", base_style="nature")
    fig, axs = plt.subplots(
        1,
        2,
        subplot_kw={"projection": wrf_proj},
        figsize=plt.rcParams["figure.figsize"],
        layout="constrained",
    )

    cbars = []
    for n, (ax, p) in enumerate(zip(axs, panels)):
        # 3) data is on the native grid -> transform IS the axes projection.
        im = p["field"].plot(
            ax=ax,
            transform=wrf_proj,
            cmap=p["cmap"],
            add_colorbar=False,
            **p["plot_kw"],
        )
        ax.set_title(p["title"])
        ax.coastlines(linewidth=0.5)

        gl = ax.gridlines(
            draw_labels=True, color="none", x_inline=False, y_inline=False
        )
        gl.top_labels = gl.right_labels = False
        gl.rotate_labels = False

        cb = fig.colorbar(
            im, ax=ax, orientation="vertical", aspect=25, pad=0.04, label=p["label"]
        )
        cbars.append((ax, cb))
        ax.annotate(**epl.subplot_labels(n, "a"))

    # Match each colourbar to its MAP height, not the grid cell. A geographic
    # axis uses set_aspect("equal"), so the drawn Lambert map is shorter than the
    # cell matplotlib allotted it; fig.colorbar otherwise sizes the bar to the
    # cell and it stands taller than the map. Freeze the layout, then clamp every
    # bar's y0/height to its map's drawn get_position(). See china_provinces.py.
    fig.canvas.draw()
    fig.set_layout_engine("none")
    for ax, cb in cbars:
        pm, pc = ax.get_position(), cb.ax.get_position()
        cb.ax.set_position([pc.x0, pm.y0, pc.width, pm.height])

    out = os.path.join(HERE, "wrf_field")
    paths = epl.save_pub(fig, out, formats=("pdf", "png"))
    plt.close(fig)
    print("wrote", *paths)


if __name__ == "__main__":
    main()
