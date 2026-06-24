"""WRF nested-domain map — publication-styled with EasyPlotLib.

Emulates ``geogrid.exe``: reads a ``namelist.wps`` and draws every WRF domain
(parent D01 + nests D02, D03 …) on one map, the standard figure you put in the
"Model configuration" / "Study area" section of a regional-modelling paper.

Pipeline
--------
1. :func:`geogrid_simulator` parses the WPS namelist and returns one
   :class:`salem.Grid` per domain (projection + extent), plus ready-made
   :class:`salem.Map` objects with the nest rectangles and ``D0x`` labels drawn.
2. We render D01 with a Natural-Earth background and overlay Chinese province
   boundaries from :mod:`cnmaps` (``get_adm_maps``) — the correct, up-to-date
   national/provincial outlines for a China study area (do **not** read a random
   ``country.shp``). For other regions, swap in ``m.set_shapefile()`` /
   ``m.set_natural_earth()`` instead.
3. EasyPlotLib supplies the journal column size, Nature style and editable
   vector + 600-dpi raster export.

Dependencies beyond EasyPlotLib: ``salem``, ``cnmaps`` (China admin maps).

Run::

    python examples/wrf_domain.py        # writes examples/wrf_domain.{pdf,png}
"""

import os

import matplotlib.pyplot as plt
import numpy as np

import EasyPlotLib as epl

HERE = os.path.dirname(__file__)
NAMELIST = os.path.join(HERE, "data", "namelist.wps")


# --------------------------------------------------------------------------- #
# geogrid.exe emulator — namelist.wps -> list of salem Grids (+ Maps).
# Adapted from salem.wrftools.geogrid_simulator.
# --------------------------------------------------------------------------- #
def geogrid_simulator(fpath, do_maps=True, map_kwargs=None):
    """Emulate geogrid.exe; useful when defining new WRF domains.

    Parameters
    ----------
    fpath : str
        Path to a ``namelist.wps`` file.
    do_maps : bool
        Also return a :class:`salem.Map` per grid (nest boxes + labels drawn).
    map_kwargs : dict
        Extra kwargs forwarded to :class:`salem.Map`.

    Returns
    -------
    (grids, maps)
        ``grids`` is a list of :class:`salem.Grid` (one per domain); ``maps`` is
        the matching list of :class:`salem.Map` (or ``None`` if ``do_maps``).
    """
    from salem import gis, wgs84

    with open(fpath) as f:
        lines = f.readlines()

    pargs = dict()
    for l in lines:
        s = l.split("=")
        if len(s) < 2:
            continue
        s0 = s[0].strip().upper()
        s1 = list(filter(None, s[1].strip().replace("\n", "").split(",")))

        if s0 == "PARENT_ID":
            parent_id = [int(s) for s in s1]
        if s0 == "PARENT_GRID_RATIO":
            parent_ratio = [int(s) for s in s1]
        if s0 == "I_PARENT_START":
            i_parent_start = [int(s) for s in s1]
        if s0 == "J_PARENT_START":
            j_parent_start = [int(s) for s in s1]
        if s0 == "E_WE":
            e_we = [int(s) for s in s1]
        if s0 == "E_SN":
            e_sn = [int(s) for s in s1]
        if s0 == "DX":
            dx = float(s1[0])
        if s0 == "DY":
            dy = float(s1[0])
        if s0 == "MAP_PROJ":
            map_proj = s1[0].replace("'", "").strip().upper()
        if s0 == "REF_LAT":
            pargs["lat_0"] = float(s1[0])
        if s0 == "REF_LON":
            pargs["ref_lon"] = float(s1[0])
        if s0 == "TRUELAT1":
            pargs["lat_1"] = float(s1[0])
        if s0 == "TRUELAT2":
            pargs["lat_2"] = float(s1[0])
        if s0 == "STAND_LON":
            pargs["lon_0"] = float(s1[0])

    # Sometimes files are not complete
    pargs.setdefault("lon_0", pargs["ref_lon"])

    # define projection
    if map_proj == "LAMBERT":
        pwrf = (
            "+proj=lcc +lat_1={lat_1} +lat_2={lat_2} "
            "+lat_0={lat_0} +lon_0={lon_0} "
            "+x_0=0 +y_0=0 +a=6370000 +b=6370000"
        ).format(**pargs)
    elif map_proj == "MERCATOR":
        pwrf = (
            "+proj=merc +lat_ts={lat_1} +lon_0={lon_0} "
            "+x_0=0 +y_0=0 +a=6370000 +b=6370000"
        ).format(**pargs)
    elif map_proj == "POLAR":
        pwrf = (
            "+proj=stere +lat_ts={lat_1} +lat_0=90.0 +lon_0={lon_0} "
            "+x_0=0 +y_0=0 +a=6370000 +b=6370000"
        ).format(**pargs)
    else:
        raise NotImplementedError("WRF proj not implemented yet: {}".format(map_proj))
    pwrf = gis.check_crs(pwrf)

    # get easting and northings from dom center (probably unnecessary here)
    e, n = gis.transform_proj(wgs84, pwrf, pargs["ref_lon"], pargs["lat_0"])

    # LL corner
    nx, ny = e_we[0] - 1, e_sn[0] - 1
    x0 = -(nx - 1) / 2.0 * dx + e  # -2 because of staggered grid
    y0 = -(ny - 1) / 2.0 * dy + n

    # parent grid
    grid = gis.Grid(nxny=(nx, ny), x0y0=(x0, y0), dxdy=(dx, dy), proj=pwrf)

    # child grids
    out = [grid]
    for ips, jps, pid, ratio, we, sn in zip(
        i_parent_start, j_parent_start, parent_id, parent_ratio, e_we, e_sn
    ):
        if ips == 1:
            continue
        ips -= 1
        jps -= 1
        we -= 1
        sn -= 1
        nx = we / ratio
        ny = sn / ratio
        if nx != (we / ratio):
            raise RuntimeError(
                "e_we and ratios are incompatible: "
                "(e_we - 1) / ratio must be integer!"
            )
        if ny != (sn / ratio):
            raise RuntimeError(
                "e_sn and ratios are incompatible: "
                "(e_sn - 1) / ratio must be integer!"
            )

        prevgrid = out[pid - 1]
        xx, yy = prevgrid.corner_grid.x_coord, prevgrid.corner_grid.y_coord
        dx = prevgrid.dx / ratio
        dy = prevgrid.dy / ratio
        grid = gis.Grid(
            nxny=(we, sn),
            x0y0=(xx[ips], yy[jps]),
            dxdy=(dx, dy),
            pixel_ref="corner",
            proj=pwrf,
        )
        out.append(grid.center_grid)

    maps = None
    if do_maps:
        import shapely.geometry as shpg
        from salem import Map

        if map_kwargs is None:
            map_kwargs = {}

        maps = []
        for i, g in enumerate(out):
            m = Map(g, **map_kwargs)
            left, right, bottom, top = g.extent
            x_offset = (right - left) * 0.05
            y_offset = -(top - bottom) * 0.05

            m.set_text(
                left + x_offset,
                top + y_offset,
                "D01",
                zorder=6,
                fontsize=11,
                fontweight="bold",
                crs=g.proj,
            )

            for j in range(i + 1, len(out)):
                cg = out[j]
                left, right, bottom, top = cg.extent

                s = np.array(
                    [(left, bottom), (right, bottom), (right, top), (left, top)]
                )
                l1 = shpg.LinearRing(s)
                m.set_geometry(l1, crs=cg.proj, linewidth=(len(out) - j), zorder=5)
                x_offset = (right - left) * 0.05 * j
                y_offset = -(top - bottom) * 0.15 * j
                m.set_text(
                    left + x_offset,
                    top + y_offset,
                    f"D0{j + 1}",
                    fontsize=11,
                    fontweight="bold",
                    zorder=6,
                    crs=cg.proj,
                )

            maps.append(m)

    return out, maps


def main():
    grids, maps = geogrid_simulator(NAMELIST)

    # One single-column Nature panel; square-ish aspect for a map.
    epl.journal_style("nat2", base_style="nature", ratio=1.0)

    fig, ax = plt.subplots()

    m = maps[0]
    # Shaded-relief / land-cover background. "lr" ships with salem (offline);
    # "hr"/"mr" are higher-res but download on first use.
    try:
        m.set_rgb(natural_earth="lr")
    except Exception as exc:  # network / data issue — keep a plain background
        print(f"natural_earth background unavailable ({exc}); plotting without it.")

    # China province boundaries from cnmaps (correct national outline).
    try:
        from cnmaps import get_adm_maps

        china = get_adm_maps(level="省", engine="geopandas")
        if china.crs is None:  # cnmaps returns lon/lat without a CRS tag
            china = china.set_crs("EPSG:4326")
        m.set_shapefile(
            shape=china, edgecolor="black", facecolor="none", linewidth=0.4
        )
    except ImportError:
        print("cnmaps not installed — skipping province boundaries "
              "(`pip install cnmaps`).")

    m.plot(ax=ax)

    out = os.path.join(HERE, "wrf_domain")
    paths = epl.save_pub(fig, out, formats=("pdf", "png"))
    plt.close(fig)
    print("wrote", *paths)


if __name__ == "__main__":
    main()
