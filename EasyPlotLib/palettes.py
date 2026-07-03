"""Curated, journal-friendly qualitative color palettes.

The palettes are low-to-medium saturation sets that read well in print and are
colour-vision-deficiency aware. The names follow the well-known ``ggsci``
collections so they are familiar to anyone coming from R.

Usage
-----
>>> import EasyPlotLib as epl
>>> epl.set_palette("nature")          # set the global color cycle
>>> colors = epl.get_palette("lancet") # grab the raw hex list
"""

from typing import List, Optional

import matplotlib.colors as mcolors
import matplotlib.pyplot as plt
from cycler import cycler
from matplotlib.axes import Axes

# Qualitative palettes. Hex values mirror the canonical ggsci collections,
# which are widely used in Nature/Science/Cell-family figures.
PALETTES = {
    # Nature Publishing Group
    "nature": [
        "#E64B35", "#4DBBD5", "#00A087", "#3C5488", "#F39B7F",
        "#8491B4", "#91D1C2", "#DC0000", "#7E6148", "#B09C85",
    ],
    # Science / AAAS
    "science": [
        "#3B4992", "#EE0000", "#008B45", "#631879", "#008280",
        "#BB0021", "#5F559B", "#A20056", "#808180", "#1B1919",
    ],
    # New England Journal of Medicine
    "nejm": [
        "#BC3C29", "#0072B5", "#E18727", "#20854E", "#7876B1",
        "#6F99AD", "#FFDC91", "#EE4C97",
    ],
    # The Lancet
    "lancet": [
        "#00468B", "#ED0000", "#42B540", "#0099B4", "#925E9F",
        "#FDAF91", "#AD002A", "#ADB6B6", "#1B1919",
    ],
    # JAMA
    "jama": [
        "#374E55", "#DF8F44", "#00A1D5", "#B24745", "#79AF97",
        "#6A6599", "#80796B",
    ],
    # Low-saturation "muted" set, close to Nature Machine Intelligence aesthetics.
    "muted": [
        "#4C72B0", "#DD8452", "#55A868", "#C44E52", "#8172B3",
        "#937860", "#DA8BC3", "#8C8C8C", "#CCB974", "#64B5CD",
    ],
    # Semantic order: blue=proposed/hero, green=gain, red=baseline/drop,
    # teal/violet=extra signal, grey=neutral. See SEMANTIC for role lookup.
    "semantic": [
        "#0F4D92", "#8BCF8B", "#B64342", "#42949E", "#9A4D8E", "#CFCECE",
    ],
    # Nature-Machine-Intelligence pastel family: cool baselines + warm hero.
    "nmi": [
        "#484878", "#7884B4", "#B4C0E4", "#F0C0CC", "#E4CCD8", "#CFCECE",
    ],
    # Many-method comparison (e.g. a bar chart of 8-10 baselines vs. yours):
    # soft low-saturation baselines, related methods share a hue family with
    # graduated lightness, and the proposed method gets the one saturated hero.
    # Put your method LAST so #3775BA lands on it.
    "comparison": [
        "#CFCECE", "#F4EEAC", "#FBDFE2", "#D9B9D4", "#DAA87C",
        "#DDF3DE", "#AADCA9", "#8BCF8B", "#92E3F9", "#3775BA",
    ],
    # Imaging / microscopy: a couple of fluorescent accents meant to sit on a
    # BLACK background, plus a grey context channel. Not for white-background plots.
    "imaging": ["#22D7E6", "#FF2AD4", "#B8B8B8"],
    # The original SciencePlots-style bright cycle (kept for backwards compat).
    "bright": [
        "#0C5DA5", "#00B945", "#FF9500", "#FF2C00", "#845B97",
        "#474747", "#9e9e9e",
    ],
}

# Role-based ("semantic") colours: assign by meaning, never remap a method to a
# different hue family across panels. Reduce saturation before adding categories.
SEMANTIC = {
    "blue_main": "#0F4D92",       # proposed / hero method
    "blue_secondary": "#3775BA",
    "green_light": "#DDF3DE",
    "green_mid": "#AADCA9",
    "green_strong": "#8BCF8B",    # gain / improvement / "delta up"
    "red_light": "#F6CFCB",
    "red_mid": "#E9A6A1",
    "red_strong": "#B64342",      # baseline / drop / "delta down"
    "neutral_light": "#CFCECE",
    "neutral_mid": "#767676",
    "neutral_dark": "#4D4D4D",
    "neutral_black": "#272727",
    "accent_gold": "#FFD700",
    "accent_teal": "#42949E",
    "accent_violet": "#9A4D8E",
    "accent_magenta": "#EA84DD",
    "delta_up": "#2E9E44",
    "delta_down": "#E53935",
}

# Recommended perceptually-uniform colormaps for continuous data (heatmaps,
# images, density). Pass these names to ``cmap=`` in imshow/pcolormesh/etc.
COLORMAPS = {
    "sequential": "viridis",   # single-direction magnitude; also "mako", "cividis"
    "sequential_warm": "magma",
    "diverging": "RdBu_r",     # signed values around a midpoint; also "coolwarm"
    "grayscale": "Greys",      # print-safe context layers
}

DEFAULT_PALETTE = "nature"


def get_palette(name: str = DEFAULT_PALETTE, n: Optional[int] = None) -> List[str]:
    """Return the list of hex colors for ``name``.

    If ``n`` is given, the palette is truncated (or cycled) to that length.
    """
    if name not in PALETTES:
        raise ValueError(
            f"Unknown palette {name!r}. Available: {', '.join(sorted(PALETTES))}"
        )
    colors = PALETTES[name]
    if n is None:
        return list(colors)
    return [colors[i % len(colors)] for i in range(n)]


def alpha_ramp(color: str, n: int, lo: float = 0.2, hi: float = 1.0) -> List[tuple]:
    """One hue at ``n`` graduated opacities — the standard *ablation* encoding.

    Use a single color and let opacity carry the ordering (e.g. progressively
    more complete model variants), rather than introducing more hues. Returns a
    list of RGBA tuples ready to pass to ``color=`` in bar/line calls.

    >>> alpha_ramp(epl.SEMANTIC["blue_main"], 3)   # light -> solid
    """
    r, g, b = mcolors.to_rgb(color)
    if n <= 1:
        return [(r, g, b, hi)]
    return [(r, g, b, lo + (hi - lo) * i / (n - 1)) for i in range(n)]


def shades(color: str, n: int, light: float = 0.82) -> List[str]:
    """``n`` shades of one hue from light to the base color.

    Mirrors the "related methods share a hue family with graduated lightness"
    rule (e.g. a baseline trio dark/mid/soft). The lightest shade is ``color``
    mixed ``light`` of the way toward white; the last shade is ``color`` itself.
    Returns hex strings.
    """
    base = mcolors.to_rgb(color)
    if n <= 1:
        return [mcolors.to_hex(base)]
    out = []
    for i in range(n):
        t = light * (1 - i / (n - 1))  # light at i=0 -> 0 at i=n-1
        mix = (base[0] * (1 - t) + t, base[1] * (1 - t) + t, base[2] * (1 - t) + t)
        out.append(mcolors.to_hex(mix))
    return out


def focal_palette(labels, focal, focal_color, other="muted", base_colors=None):
    """Map ``labels`` → colours with the focal series visually dominant (§4.2).

    Once a figure compares one focal series (your method, the perturbed
    condition) against others, the focal series should be saturated and heavy
    while the comparators recede — colour carries the emphasis, not a callout.

    Parameters
    ----------
    labels:
        The series labels, in draw order.
    focal:
        The focal label (str) or a set/list of focal labels.
    focal_color:
        The saturated hue for the focal series (e.g. ``SEMANTIC["blue_main"]``).
    other:
        How to render the non-focal series:

        - ``"muted"``   — desaturate ``base_colors`` (or the current cycle) toward grey.
        - ``"grey"``    — a uniform light grey for all non-focal series.
        - ``"ordinal"`` — non-focal on a single light→dark grey ramp (input order).
    base_colors:
        Optional base hue list for ``"muted"``; defaults to the rcParams cycle.

    Returns
    -------
    list
        One colour per label, aligned with ``labels``.
    """
    focal_set = {focal} if isinstance(focal, str) else set(focal)
    n = len(labels)
    if not focal_set & set(labels):
        raise ValueError(f"focal {focal!r} not found in labels")
    if base_colors is None:
        base_colors = plt.rcParams["axes.prop_cycle"].by_key().get("color", ["#444444"])
    base_colors = [base_colors[i % len(base_colors)] for i in range(n)]
    if other == "grey":
        rest = ["#BCBCBC"] * n
    elif other == "ordinal":
        nf = max(1, n - len(focal_set))
        ramp = [
            mcolors.to_hex((v, v, v))
            for v in ([0.55] if nf == 1 else [0.80 - 0.35 * i / (nf - 1) for i in range(nf)])
        ]
        rest, k = [], 0
        for lab in labels:
            rest.append(ramp[min(k, nf - 1)])
            k += lab not in focal_set
    elif other == "muted":
        def mute(c):
            r, g, b = mcolors.to_rgb(c)
            m = (r + g + b) / 3
            return mcolors.to_hex(
                (0.3 * r + 0.7 * m, 0.3 * g + 0.7 * m, 0.3 * b + 0.7 * m)
            )

        rest = [mute(c) for c in base_colors]
    else:
        raise ValueError(f"other must be 'muted'|'grey'|'ordinal', got {other!r}")
    return [focal_color if lab in focal_set else rest[i] for i, lab in enumerate(labels)]


def set_palette(name: str = DEFAULT_PALETTE, ax: Optional[Axes] = None) -> List[str]:
    """Set the qualitative color cycle to ``name``.

    With no ``ax`` the global :data:`matplotlib.rcParams` cycle is updated so it
    applies to every subsequent figure. Pass an ``ax`` to scope it to a single
    Axes. Returns the colour list that was applied.
    """
    colors = get_palette(name)
    prop_cycle = cycler("color", colors)
    if ax is None:
        plt.rcParams["axes.prop_cycle"] = prop_cycle
    else:
        ax.set_prop_cycle(prop_cycle)
    return colors
