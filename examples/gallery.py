"""Chart-type gallery for EasyPlotLib.

One publication-styled panel per archetype a SCI-journal manuscript usually
needs, each built with the EasyPlotLib helpers. The point of this file is
**colour consistency**: every panel sources its colours from the same small
abstracted API rather than ad-hoc hex codes —

    epl.get_palette(name)      qualitative sets (nature, comparison, nmi, ...)
    epl.SEMANTIC[role]         role-based colours (hero / gain / drop / neutral)
    epl.shades(color, n)       one hue, graduated lightness (related methods)
    epl.alpha_ramp(color, n)   one hue, graduated opacity (ablations)
    epl.COLORMAPS[kind]        perceptual colormaps for continuous data

Run directly to render every panel into ``examples/gallery/``:

    python examples/gallery.py

Only numpy + matplotlib are required (no cartopy/cnmaps).
"""

import os

import matplotlib.pyplot as plt
import numpy as np

import EasyPlotLib as epl

rng = np.random.default_rng(0)
OUT = os.path.join(os.path.dirname(__file__), "gallery")


# --------------------------------------------------------------------------- #
# 1. Method comparison bars — many baselines + your method.
#    Colour: the `comparison` palette (soft, hue-family-grouped, hero last).
# --------------------------------------------------------------------------- #
def bar_comparison():
    epl.journal_style("nat1")
    methods = ["Prime", "NetMHC", "MHCnug", "MHCflu", "DeepNeo",
               "BigMHC-EL", "BigMHC-IM", "BigMHC-rt", "NeoaPred", "Ours"]
    scores = [0.58, 0.61, 0.60, 0.63, 0.66, 0.69, 0.71, 0.74, 0.72, 0.86]
    colors = epl.get_palette("comparison", n=len(methods))  # hero blue lands on "Ours"

    fig, ax = plt.subplots()
    ax.bar(range(len(methods)), scores, color=colors, edgecolor="white", linewidth=0.4)
    ax.set_xticks(range(len(methods)), methods, rotation=45, ha="right")
    ax.set_ylabel("AUROC")
    ax.set_ylim(0.5, 0.9)
    return fig, "01_bar_comparison"


# --------------------------------------------------------------------------- #
# 2. Ablation bars — one hue, opacity carries the ordering (alpha_ramp).
# --------------------------------------------------------------------------- #
def bar_ablation():
    epl.journal_style("nat1")
    labels = ["Full", "− contrastive", "− transfer", "− both"]
    scores = [0.86, 0.80, 0.77, 0.71]
    colors = epl.alpha_ramp(epl.SEMANTIC["blue_main"], len(labels), lo=1.0, hi=0.3)

    fig, ax = plt.subplots()
    ax.bar(range(len(labels)), scores, color=colors, edgecolor=epl.SEMANTIC["blue_main"],
           linewidth=0.5)
    ax.set_xticks(range(len(labels)), labels, rotation=30, ha="right")
    ax.set_ylabel("AUROC")
    ax.set_ylim(0.6, 0.9)
    return fig, "02_bar_ablation"


# --------------------------------------------------------------------------- #
# 3. Line / trend with CI band — hero vs baseline (SEMANTIC roles).
# --------------------------------------------------------------------------- #
def line_trend():
    epl.journal_style("nat1")
    x = np.linspace(0, 10, 200)
    series = [("baseline", epl.SEMANTIC["neutral_mid"], 1.6),
              ("ours", epl.SEMANTIC["blue_main"], 1.0)]
    fig, ax = plt.subplots()
    for name, color, k in series:
        y = 1 - np.exp(-x / (2 * k))
        band = 0.04 + 0.02 * np.sin(x)
        ax.plot(x, y, color=color, label=name)
        ax.fill_between(x, y - band, y + band, color=color, alpha=0.2, linewidth=0)
    ax.set_xlabel("Training steps (k)")
    ax.set_ylabel("Performance")
    ax.legend()
    return fig, "03_line_trend"


# --------------------------------------------------------------------------- #
# 4. Heatmap — continuous magnitude via a perceptual colormap (COLORMAPS).
# --------------------------------------------------------------------------- #
def heatmap():
    epl.journal_style("nat1", inverted_aspect_ratio=0.9)
    data = rng.normal(0, 1, (8, 10)).cumsum(axis=1)
    fig, ax = plt.subplots()
    im = ax.imshow(data, cmap=epl.COLORMAPS["sequential"], aspect="auto")
    ax.set_xlabel("Time")
    ax.set_ylabel("Channel")
    fig.colorbar(im, ax=ax, fraction=0.046, pad=0.03).set_label("Signal")
    return fig, "04_heatmap"


# --------------------------------------------------------------------------- #
# 5. Scatter / bubble — two clusters keyed to SEMANTIC hero/drop colours.
# --------------------------------------------------------------------------- #
def scatter_bubble():
    epl.journal_style("nat1")
    fig, ax = plt.subplots()
    for (mx, my), color, name in [((0, 0), epl.SEMANTIC["red_strong"], "cluster 1"),
                                  ((2.5, 2.0), epl.SEMANTIC["blue_main"], "cluster 2")]:
        x = rng.normal(mx, 0.7, 60)
        y = rng.normal(my, 0.7, 60)
        s = rng.uniform(4, 40, 60)
        ax.scatter(x, y, s=s, color=color, alpha=0.6, edgecolor="white",
                   linewidth=0.3, label=name)
    ax.set_xlabel("UMAP-1")
    ax.set_ylabel("UMAP-2")
    ax.legend()
    return fig, "05_scatter_bubble"


# --------------------------------------------------------------------------- #
# 6. Radar / polar — baseline vs hero (SEMANTIC roles, consistent with #3).
# --------------------------------------------------------------------------- #
def radar():
    epl.journal_style("nat1", ratio=1.0)
    labels = ["Acc", "F1", "AUC", "Speed", "Mem", "Robust"]
    series = [("Baseline", epl.SEMANTIC["neutral_mid"], [0.6, 0.55, 0.7, 0.5, 0.6, 0.45]),
              ("Ours", epl.SEMANTIC["blue_main"], [0.85, 0.82, 0.9, 0.7, 0.78, 0.8])]
    angles = np.linspace(0, 2 * np.pi, len(labels), endpoint=False)
    angles = np.concatenate([angles, angles[:1]])

    fig, ax = plt.subplots(subplot_kw={"projection": "polar"})
    ax.set_theta_zero_location("N")
    ax.set_theta_direction(-1)
    for name, color, vals in series:
        v = np.concatenate([vals, vals[:1]])
        ax.plot(angles, v, color=color, label=name)
        ax.fill(angles, v, color=color, alpha=0.15)
    ax.set_xticks(angles[:-1], labels)
    ax.set_ylim(0, 1)
    ax.legend(bbox_to_anchor=(1.25, 1.05), loc="upper left")
    return fig, "06_radar"


# --------------------------------------------------------------------------- #
# 7. Distributions — related groups as graduated shades of one hue (shades()).
# --------------------------------------------------------------------------- #
def distributions():
    epl.journal_style("nat1")
    groups = [rng.normal(loc, 1.0, 200) for loc in (0, 0.8, 1.6)]
    colors = epl.shades(epl.SEMANTIC["blue_main"], len(groups))  # light -> solid
    fig, ax = plt.subplots()
    parts = ax.violinplot(groups, showextrema=False)
    for body, c in zip(parts["bodies"], colors):
        body.set_facecolor(c)
        body.set_alpha(0.8)
    ax.boxplot(groups, widths=0.15, showfliers=False,
               medianprops=dict(color=epl.SEMANTIC["neutral_black"]))
    ax.set_xticks([1, 2, 3], ["wt", "het", "mut"])
    ax.set_ylabel("Expression (a.u.)")
    return fig, "07_distributions"


# --------------------------------------------------------------------------- #
# 8. Forest / interval — point estimates + CIs (SEMANTIC hero + neutral rule).
# --------------------------------------------------------------------------- #
def forest():
    epl.journal_style("nat1")
    names = ["Age", "Sex", "BMI", "Smoking", "Treatment"]
    est = np.array([1.1, 0.9, 1.4, 1.8, 0.6])
    lo = est - rng.uniform(0.1, 0.3, len(est))
    hi = est + rng.uniform(0.1, 0.3, len(est))
    y = np.arange(len(names))[::-1]

    fig, ax = plt.subplots()
    ax.axvline(1.0, color=epl.SEMANTIC["neutral_mid"], lw=0.6, ls="--")
    ax.errorbar(est, y, xerr=[est - lo, hi - est], fmt="o",
                color=epl.SEMANTIC["blue_main"], capsize=2, markersize=3)
    ax.set_yticks(y, names)
    ax.set_xlabel("Hazard ratio (95% CI)")
    return fig, "08_forest"


# --------------------------------------------------------------------------- #
# 9. Stacked area — one hue family via shades(), hatched for grayscale print.
# --------------------------------------------------------------------------- #
def stacked_area():
    epl.journal_style("nat1")
    x = np.arange(2008, 2026)
    parts = np.abs(rng.normal(1, 0.3, (4, len(x)))).cumsum(axis=1)
    colors = epl.shades(epl.SEMANTIC["accent_teal"], 4)
    fig, ax = plt.subplots()
    ax.stackplot(x, parts, colors=colors,
                 labels=[f"area {i + 1}" for i in range(4)], alpha=0.9)
    ax.set_xlabel("Year")
    ax.set_ylabel("Cumulative count")
    ax.legend(loc="upper left", ncol=2)
    ax.set_xlim(x.min(), x.max())
    return fig, "09_stacked_area"


def main():
    os.makedirs(OUT, exist_ok=True)
    builders = [bar_comparison, bar_ablation, line_trend, heatmap, scatter_bubble,
                radar, distributions, forest, stacked_area]
    for build in builders:
        fig, name = build()
        fig.get_axes()[0].annotate(**epl.subplot_labels(0, "a"))
        paths = epl.save_pub(fig, os.path.join(OUT, name), formats=("png",))
        plt.close(fig)
        print("wrote", paths[0])


if __name__ == "__main__":
    main()
