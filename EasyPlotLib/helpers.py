"""High-level convenience for setting up a journal-ready figure context."""

from typing import Optional

import matplotlib.pyplot as plt

from .figsizes_set import figsizes
from .palettes import DEFAULT_PALETTE, set_palette


def journal_style(
    journal_key: str = "nat1",
    *,
    palette: str = DEFAULT_PALETTE,
    base_style: str = "nature",
    nrows: Optional[int] = None,
    ncols: Optional[int] = None,
    apply: bool = True,
    **figsize_kwargs,
) -> dict:
    """Apply a complete publication style in one call.

    Combines the bundled ``base_style`` stylesheet, a journal column-width
    :func:`~EasyPlotLib.figsizes` figure size, and a qualitative
    :func:`~EasyPlotLib.set_palette` colour cycle.

    Parameters
    ----------
    journal_key:
        A key from ``figsizes`` (e.g. ``"nat1"``/``"nat2"`` single/double
        column for Nature, ``"science"`` keys ``"aaas1"``/``"aaas2"``, etc.).
    palette:
        Qualitative palette name (see :data:`EasyPlotLib.PALETTES`).
    base_style:
        A registered matplotlib style; ``"nature"`` is bundled.
    nrows, ncols:
        Passed to ``figsizes`` to auto-pick a sensible aspect ratio for a grid.
    apply:
        When ``True`` (default) mutate the global rc state. Set ``False`` to
        only compute and return the figsize dict.

    Returns
    -------
    dict
        The figure-size rcParams dict (the return value of ``figsizes``), handy
        to splice into ``plt.rcParams.update`` or ``plt.style.context``.

    Notes
    -----
    This enables **constrained layout** (``figure.constrained_layout.use``) for
    every subsequent figure. Do not call ``fig.subplots_adjust()`` or
    ``plt.tight_layout()`` on such a figure — matplotlib drops the layout
    engine and spacing degrades. Tune panel spacing through the engine:
    ``fig.get_layout_engine().set(wspace=..., hspace=...)``.
    """
    fs = figsizes(journal_key, nrows=nrows, ncols=ncols, **figsize_kwargs)
    if apply:
        plt.style.use(base_style)
        plt.rcParams.update(fs)
        set_palette(palette)
    return fs
