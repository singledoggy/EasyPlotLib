import matplotlib.pyplot as plt
import cartopy.crs as ccrs
from cartopy.mpl.ticker import LongitudeFormatter, LatitudeFormatter


def cartopy_plot_tickmarks_helper(ax, labels, axis):
    assert axis in ["x", "y"]

    ticks = []
    values = [float(txt.get_text().split("°")[0]) for txt in labels]
    directions = [
        txt.get_text().split("°")[1] for txt in labels
    ]  # what comes after the degree symbol
    for i, _ in enumerate(labels):
        value = values[i]
        if directions[i] in ["W", "S"]:
            ticks += [-value]
        else:  # for 'E', 'N' and '' (e.g. 180 degrees)
            ticks += [value]

    if axis == "x":
        ax.set_xticks(ticks, crs=ccrs.PlateCarree())
        ax.set_xticklabels(
            ["" for _ in range(len(ticks))]
        )  # make new ticks have blank labels to not overplot cartopy's
    elif axis == "y":
        ax.set_yticks(ticks, crs=ccrs.PlateCarree())
        ax.set_yticklabels(
            ["" for _ in range(len(ticks))]
        )  # make new ticks have blank labels to not overplot cartopy's


def cartopy_plot_tickmarks(ax, gl):
    plt.draw()
    xlabels = gl.xlabel_artists
    ylabels = gl.ylabel_artists
    lon_formatter = LongitudeFormatter()
    ax.xaxis.set_major_formatter(lon_formatter)
    lat_formatter = LatitudeFormatter()
    ax.yaxis.set_major_formatter(lat_formatter)
    cartopy_plot_tickmarks_helper(ax, xlabels, "x")
    cartopy_plot_tickmarks_helper(ax, ylabels, "y")
