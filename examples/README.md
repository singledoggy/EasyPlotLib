# EasyPlotLib examples — index

A catalog of worked examples so the `sci-figure` skill (and you) can find a
close precedent before writing a new figure from scratch. **Look here first**:
match the task to a row, open that file, adapt it.

| Example | What it demonstrates | Key APIs | Extra deps |
|---------|----------------------|----------|------------|
| [`gallery.py`](gallery.py) → [`gallery/`](gallery) | One publication panel per common chart archetype (bars, ablation, trend+CI, heatmap, scatter, radar, violin/box, forest, stacked area). The reference for **color consistency**. | `journal_style`, `get_palette`, `SEMANTIC`, `shades`, `alpha_ramp`, `COLORMAPS`, `subplot_labels`, `save_pub` | numpy, matplotlib |
| [`example_plot.ju.py`](example_plot.ju.py) | Basics: multi-panel layout, journal figure sizing, panel labels, cartopy China maps with clean lon/lat ticks, `subplot_mosaic`. | `figsizes`, `subplot_labels`, `cartopy_plot_tickmarks` | cartopy, cnmaps |
| [`example_plot.ipynb`](example_plot.ipynb) | Notebook walkthrough of the same basics. | as above | cartopy, cnmaps |
| [`wrf_domain.py`](wrf_domain.py) → [`wrf_domain.png`](wrf_domain.png) | **WRF nested-domain / study-area map.** Parses `namelist.wps` (geogrid.exe emulator), draws parent + nest boxes (D01, D02 …) on a projected map with a Natural-Earth background and Chinese province boundaries. | `journal_style`, `save_pub`; salem `Grid`/`Map`; `cnmaps.get_adm_maps` | salem, cnmaps, shapely |

<p align="center">
  <img src="wrf_domain.png" width="360"><br>
  <sub><code>wrf_domain.py</code> — parent D01 (15 km Lambert) + D02 nest, cnmaps provinces.</sub>
</p>

## Conventions worth copying

- **Sizing + style in one call:** `epl.journal_style(key, base_style="nature",
  nrows=, ncols=, ratio=/inverted_aspect_ratio=)`. Keys: `nat1/2`, `aaas1/2`,
  `pnas1..3`, `agu1..4`, `ams1..4`.
- **Color by meaning, not index** — `SEMANTIC` (blue = hero, grey = baseline),
  one restrained palette per figure. See `gallery.py` and the root README's
  "Color scheme guidance".
- **Panel labels:** `ax.annotate(**epl.subplot_labels(n, "a"))`.
- **Export:** `epl.save_pub(fig, path, formats=("pdf", "png"))` — editable vector
  text + 600-dpi raster.

## Maps (geoscience figures)

- **China admin boundaries:** use `from cnmaps import get_adm_maps` and
  `get_adm_maps(level="省", engine="geopandas")` — never read an ad-hoc
  `country.shp` (outdated/incorrect national outline). Works both as a cartopy
  layer (`example_plot.ju.py`) and a salem `Map.set_shapefile(shape=...)` layer
  (`wrf_domain.py`).
- **WRF domains:** drive `geogrid_simulator(namelist.wps)` in `wrf_domain.py`;
  the parsed `namelist.wps` lives in [`data/`](data).
- **Clean cartopy ticks:** `epl.cartopy_plot_tickmarks(ax, gl)`.
