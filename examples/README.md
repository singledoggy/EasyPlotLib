# EasyPlotLib examples — index

Worked, runnable precedents grouped by category. **Before writing a new figure,
match your task to a row below, open that file, and adapt it** — don't start from
a blank script. The `sci-figure` skill uses this index the same way.

```
examples/
├── gallery.py              charts — one publication panel per archetype
├── gallery/*.png           rendered chart panels
├── maps/                   geoscience maps (cartopy + cnmaps + salem)
│   ├── china_provinces.py      study-area map + South China Sea inset
│   ├── wrf_domain.py           WRF nested domains from namelist.wps
│   └── data/namelist.wps
└── layout/                 organizing multi-panel figures
    ├── subplot_layouts.py      grids + mosaics, sized & labelled
    └── subplot_layouts.ipynb   notebook companion
```

## Charts — `gallery.py`

One publication-styled panel per archetype a manuscript usually needs; every
panel sources colour from the shared abstracted API (the reference for **colour
consistency**). Run `python examples/gallery.py` → `gallery/`.

| Want to show… | Panel | Colour API |
|---|---|---|
| compare many methods + your method | `01_bar_comparison` | `get_palette("comparison")` (hero last) |
| ablation (one method, components removed) | `02_bar_ablation` | `alpha_ramp(color, n)` |
| trend over x + uncertainty band | `03_line_trend` | `SEMANTIC` (blue=hero, grey=baseline) |
| matrix / magnitudes | `04_heatmap` | `COLORMAPS["sequential"]` |
| 2D embedding / correlation | `05_scatter_bubble` | `SEMANTIC` |
| benchmarks × few methods | `06_radar` | `SEMANTIC` |
| sample spread / distribution | `07_distributions` | `shades(color, n)` |
| effect sizes + CIs | `08_forest` | `SEMANTIC` + null rule |
| composition over time | `09_stacked_area` | `shades(color, n)` |

Shared APIs: `journal_style`, `subplot_labels`, `save_pub`. Deps: numpy, matplotlib.

## Maps — `maps/`

Geoscience base maps. **China admin boundaries always via `from cnmaps import
get_adm_maps`** (`get_adm_maps(level="省", engine="geopandas")`) — never an ad-hoc
`country.shp`. The nine-dash line (南海九段线) ships inside the province set
(cnmaps attaches the South China Sea islands to Hainan, reaching ~3.8°N), so the
**bottom-right SCS inset draws the same `china_map`**. Add geometries with
`ax.add_geometries(china_map.geometry, crs=PROJ, ...)`, which takes the CRS inline
(cnmaps returns lon/lat untagged); for salem instead call `.set_crs("EPSG:4326")`.
To colour a **gridded field** only over land, clip the mesh to one fused boundary —
`clip_pcolormesh_by_map(mesh, MapPolygon(prov.geometry.union_all()))` — and clamp the
colourbar to the drawn map height (equal-aspect maps shrink inside their grid cell).

| Want… | Example | Stack | Deps |
|---|---|---|---|
| **colour-mapped field over China** (clipped to the outline) + colourbar + nine-dash-line inset | [`china_provinces.py`](maps/china_provinces.py) → [png](maps/china_provinces.png) | cartopy `pcolormesh(cmap=COLORMAPS["sequential"])` clipped via `clip_pcolormesh_by_map`; colourbar **clamped to the drawn map height** (equal-aspect maps shrink inside their cell — see `tests/test_map_aspect_colorbar.py`); `ax.inset_axes(...)` SCS inset; `cartopy_plot_tickmarks` for degree labels | cartopy, cnmaps |
| WRF nested-domain / model-config map (D01, D02 …) | [`wrf_domain.py`](maps/wrf_domain.py) → [png](maps/wrf_domain.png) | `geogrid_simulator(namelist.wps)` → salem `Grid`/`Map`, Natural-Earth bg, `cnmaps` provinces | salem, cnmaps, shapely |

<p align="center">
  <img src="maps/china_provinces.png" width="300">
  <img src="maps/wrf_domain.png" width="270"><br>
  <sub><code>china_provinces.py</code> (clipped colour field + nine-dash inset) · <code>wrf_domain.py</code> (D01 + D02 nest)</sub>
</p>

Notes: salem's `set_rgb(natural_earth="hr")` downloads on first use (and the CDN
can 406) — `"lr"` ships with salem and works offline. WRF namelists live in
[`maps/data/`](maps/data).

## Layout — `layout/subplot_layouts.py`

How to organize multi-panel figures so each panel is correctly shaped and
labelled. Two patterns, each rendered to a PNG:

| Pattern | When | Key call |
|---|---|---|
| regular grid ([`subplot_grid.png`](layout/subplot_grid.png)) | panels of equal size/role | `plt.subplots(nrows, ncols)` + matching `journal_style(nrows=, ncols=)` so each cell ≈ golden; share axes |
| irregular mosaic ([`subplot_mosaic.png`](layout/subplot_mosaic.png)) | one hero panel + supporting ones | `plt.subplot_mosaic("AAB\nAAC")` |

APIs: `journal_style`, `subplot_labels`, `save_pub`. Deps: numpy, matplotlib (no
cartopy/cnmaps). `subplot_layouts.ipynb` is the notebook companion.

## Conventions worth copying

- **Sizing + style in one call:** `epl.journal_style(key, base_style="nature",
  nrows=, ncols=, ratio=/inverted_aspect_ratio=)`. Width keys: `nat1/2`,
  `aaas1/2`, `pnas1..3`, `agu1..4`, `ams1..4`.
- **Colour by meaning, not index** — `SEMANTIC` (blue=hero, grey=baseline); one
  restrained palette per figure. See `gallery.py` + root README "Color scheme".
- **Panel labels:** `ax.annotate(**epl.subplot_labels(n, "a"))` (8 pt bold).
- **Export:** `epl.save_pub(fig, path, formats=("pdf", "png"))` — editable vector
  text + 600-dpi raster. (`*.pdf` under `examples/` is gitignored.)
