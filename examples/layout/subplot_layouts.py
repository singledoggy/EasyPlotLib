"""Organizing subplots — grids and mosaics, sized & labelled for journals.

How to lay out multi-panel figures with EasyPlotLib so each panel ends up the
right shape and every panel carries a bold letter. Two patterns:

1. **Regular grid** — ``plt.subplots(nrows, ncols)``. Pass the *same* ``nrows,
   ncols`` to :func:`EasyPlotLib.journal_style`; it derives a figure aspect
   (``golden × nrows/ncols``) so each *cell* lands ≈ golden ratio. Share axes to
   drop redundant tick labels.
2. **Irregular mosaic** — ``plt.subplot_mosaic`` for panels of differing size
   (one hero panel + supporting ones). ``per_subplot_kw`` customises individual
   panels (projections, etc.).

Panel letters come from :func:`EasyPlotLib.subplot_labels` (8 pt bold, journal
convention). Pure matplotlib — no cartopy/cnmaps needed.

Run::

    python examples/layout/subplot_layouts.py   # writes subplot_{grid,mosaic}.png
"""

import os

import matplotlib.pyplot as plt
import numpy as np

import EasyPlotLib as epl

HERE = os.path.dirname(__file__)
rng = np.random.default_rng(0)


def grid():
    """2×3 regular grid; shared axes; one bold letter per panel."""
    # Same nrows/ncols -> each cell comes out ≈ golden ratio.
    epl.journal_style("nat2", nrows=2, ncols=3)

    fig, axs = plt.subplots(2, 3, sharex=True, sharey=True)
    x = np.linspace(0, 2 * np.pi, 200)
    for n, ax in enumerate(axs.flatten()):
        ax.plot(x, np.sin(x + n * 0.5), color=epl.SEMANTIC["blue_main"])
        ax.plot(x, np.cos(x + n * 0.5), color=epl.SEMANTIC["neutral_mid"])
        ax.annotate(**epl.subplot_labels(n, "a"))
    for ax in axs[-1]:
        ax.set_xlabel("phase")
    for ax in axs[:, 0]:
        ax.set_ylabel("amplitude")
    return fig, "subplot_grid"


def mosaic():
    """Irregular mosaic: one wide hero panel + three supporting panels."""
    # A 2-column figure, a touch taller than golden to fit two rows.
    epl.journal_style("nat2", inverted_aspect_ratio=0.62)

    fig, axd = plt.subplot_mosaic(
        """
        AAB
        AAC
        """
    )
    # Hero panel A: a filled trend.
    x = np.linspace(0, 10, 200)
    y = 1 - np.exp(-x / 3)
    axd["A"].plot(x, y, color=epl.SEMANTIC["blue_main"])
    axd["A"].fill_between(x, y - 0.05, y + 0.05,
                          color=epl.SEMANTIC["blue_main"], alpha=0.2, lw=0)
    axd["A"].set_xlabel("training steps (k)")
    axd["A"].set_ylabel("performance")

    # Supporting panels B, C: small distributions / bars.
    axd["B"].bar(range(4), rng.uniform(0.4, 0.9, 4),
                 color=epl.shades(epl.SEMANTIC["blue_main"], 4))
    axd["B"].set_ylabel("score")
    axd["C"].hist(rng.normal(size=300), bins=20,
                  color=epl.SEMANTIC["neutral_mid"])
    axd["C"].set_xlabel("residual")

    for n, key in enumerate("ABC"):
        axd[key].annotate(**epl.subplot_labels(n, "a"))
    return fig, "subplot_mosaic"


def main():
    for build in (grid, mosaic):
        fig, name = build()
        paths = epl.save_pub(fig, os.path.join(HERE, name), formats=("png",))
        plt.close(fig)
        print("wrote", *paths)


if __name__ == "__main__":
    main()
