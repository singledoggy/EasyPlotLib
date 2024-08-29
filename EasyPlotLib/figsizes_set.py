from typing import Final, Tuple, Union

import string

_MILLIMETERS_PER_INCH: Final = 25.4
_GOLDEN_RATIO: Final = (5.0**0.5 - 1.0) / 2

_PAD_INCHES: Final = 0.2


def mm_to_inch(mm):
    return round(mm / _MILLIMETERS_PER_INCH, 2)


_JOURNAL_SIZES = {
    "aaas1": mm_to_inch(55),
    "aaas2": mm_to_inch(120),
    "agu1": (mm_to_inch(95), mm_to_inch(115)),
    "agu2": (mm_to_inch(195), mm_to_inch(115)),
    "agu3": (mm_to_inch(95), mm_to_inch(230)),
    "agu4": (mm_to_inch(195), mm_to_inch(230)),
    "ams1": 3.2,
    "ams2": 4.5,
    "ams3": 5.5,
    "ams4": 6.5,
    "nat1": mm_to_inch(89),
    "nat2": mm_to_inch(183),
    "pnas1": mm_to_inch(87),
    "pnas2": mm_to_inch(114),
    "pnas3": mm_to_inch(178),
}


def figsizes(
    journal_key,
    inverted_aspect_ratio=1,
    nrows=None,
    ncols=None,
    constrained_layout=True,
    autolayout=False,
    tight_layout="tight",
    pad_inches=_PAD_INCHES,
    ratio=1,
) -> dict:
    # set defaul inverted_aspect if nrows
    if nrows and ncols:
        inverted_aspect_ratio = _GOLDEN_RATIO * nrows / ncols
    width = _JOURNAL_SIZES[journal_key]
    if isinstance(width, tuple):  # handle case where width is a tuple
        width = width[0]
    height = width * inverted_aspect_ratio
    figsize = (width * ratio, height * ratio)
    return {
        "figure.figsize": figsize,
        "figure.constrained_layout.use": constrained_layout,
        "figure.autolayout": autolayout,
        "savefig.bbox": tight_layout,
        "savefig.pad_inches": pad_inches,
    }


def style_label(n, style="A"):
    labels = string.ascii_uppercase if style.isupper() else string.ascii_lowercase
    if style in ["A", "a"]:
        return labels[n]
    elif style in ["(A)", "(a)"]:
        return f"({labels[n]})"
    elif style in ["A)", "a)"]:
        return f"{labels[n]})"
    elif style in ["A.", "a."]:
        return f"{labels[n]}."
    else:
        raise ValueError("Unsupported style format")


def subplot_labels(
    n: int,
    style: str = "A",
    xy: Tuple[float, float] = (0, 1),
    xycoords: str = "axes fraction",
    xytext: Tuple[float, float] = (+0.5, +1),
    textcoords: str = "offset fontsize",
    fontsize: Union[str, int] = "medium",
    verticalalignment: str = "top",
    family: str = "sans-serif",
    weight: str = "bold",
) -> dict:
    return {
        "text": style_label(n, style),
        "xy": xy,
        "xycoords": xycoords,
        "xytext": xytext,
        "textcoords": textcoords,
        "fontsize": fontsize,
        "verticalalignment": verticalalignment,
        "family": family,
        "weight": weight,
    }
