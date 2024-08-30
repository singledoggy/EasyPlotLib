# %%
import cartopy.crs as ccrs
import EasyPlotLib as epl
import matplotlib.pyplot as plt
from cnmaps import get_adm_maps

nrows, ncols = 1, 2
figsizes = epl.figsizes("nat2", nrows=nrows, ncols=ncols)

# plt.style.use(["science", "no-latex"])
plt.style.use(["nature"])
plt.rcParams.update(figsizes)
fig, axs = plt.subplots(nrows=nrows, ncols=ncols, sharex=True, sharey=True)

for n, ax in enumerate(axs.flatten()):
    ax.plot([1.0, 2.0], [3.0, 4.0])
    ax.plot([1.0, 2.0], [2.0, 5.0])
    ax.annotate(**epl.subplot_labels(n, "A"))

plt.savefig("test.png", dpi=300)
# %%
plt.rcParams["font.family"]
# %%
plt.rcParams["font.sans-serif"]
# %%
import matplotlib.pyplot as plt

import EasyPlotLib as epl

nrows, ncols = 1, 1
figsizes = epl.figsizes("nat2", nrows=nrows, ncols=ncols)

plt.style.use(["science", "nature", "no-latex"])
plt.rcParams.update(figsizes)
plt.rcParams.update(
    {
        "font.family": "sans-serif",
        # 'font.sans-serif': ['Helvetica'],
    }
)

fig, axs = plt.subplots(nrows=nrows, ncols=ncols, sharex=True, sharey=True)

# for n, ax in enumerate(axs.flatten()):
#       ax.annotate(**epl.subplot_labels(n, "a",fontsize=12))
# %%

nrows, ncols = 1, 2
figsizes = epl.figsizes("nat2", inverted_aspect_ratio=1)

plt.style.use("default")
plt.rcParams.update(figsizes)

china_map = get_adm_maps(level="省", engine="geopandas")
fig, axs = plt.subplots(
    ncols=ncols,
    nrows=nrows,
    subplot_kw={"projection": ccrs.PlateCarree()},
)
for n, ax in enumerate(axs.flatten()):
    china_map.plot(ax=ax, edgecolor="black", facecolor="none", linewidth=0.5)  # type: ignore
    ax.annotate(**epl.subplot_labels(n, "A"))

width, height = fig.get_size_inches()
inverted_aspect_ratio = height / width
figsizes = epl.figsizes("nat2", inverted_aspect_ratio=inverted_aspect_ratio)
fig.set_size_inches(figsizes["figure.figsize"])
fig.savefig("test2.png", dpi=300)
# %%
