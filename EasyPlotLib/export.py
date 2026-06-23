"""Publication-quality figure export.

Saves a figure to several formats at once with settings that keep text
**editable** in Illustrator/Inkscape (``pdf.fonttype = 42``, ``svg.fonttype =
none`` — configured in the bundled ``nature`` style) and rasters at journal DPI.
"""

import os
from typing import Iterable

import matplotlib.figure


def save_pub(
    fig: matplotlib.figure.Figure,
    filename: str,
    formats: Iterable[str] = ("pdf", "png"),
    dpi: int = 600,
    transparent: bool = False,
    bbox_inches: str = "tight",
    pad_inches: float = 0.02,
    **savefig_kwargs,
) -> list:
    """Save ``fig`` to one file per format and return the written paths.

    Parameters
    ----------
    filename:
        Path *without* extension, e.g. ``"figures/fig1"``. Parent directories
        are created if needed.
    formats:
        Any matplotlib-supported extensions. Vector formats (``pdf``, ``svg``,
        ``eps``) are preferred for line art; ``tiff``/``png`` at ``dpi`` for
        raster submission. Most journals want one vector + one high-DPI raster.
    dpi:
        Resolution for raster formats. 600 dpi suits line art; use 300 for
        photographic/heatmap content if file size matters.
    """
    if isinstance(formats, str):  # a bare "png" must not iterate into 'p','n','g'
        formats = (formats,)

    directory = os.path.dirname(filename)
    if directory:
        os.makedirs(directory, exist_ok=True)

    written = []
    for fmt in formats:
        path = f"{filename}.{fmt.lstrip('.')}"
        fig.savefig(
            path,
            dpi=dpi,
            transparent=transparent,
            bbox_inches=bbox_inches,
            pad_inches=pad_inches,
            **savefig_kwargs,
        )
        written.append(path)
    return written
