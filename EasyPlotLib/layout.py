"""Content-driven layout for a single ROW of panels (maps and/or square plots).

Two things make a multi-panel row look right, and both are derivable from the
panels' own aspect ratios — you should not have to hand-tune them:

1. ``width_ratios`` ∝ each panel's aspect (width/height).  Then every gridspec
   cell matches its panel's shape and all panels render at the SAME height.

2. ``inverted_aspect_ratio`` (= figure height / width) tall enough that every
   panel is *width-limited* — i.e. it fills its column instead of shrinking
   inside it and leaving big horizontal gaps between panels.

For (2) there is a closed form.  With ``width_ratios`` ∝ aspect, every panel
crosses from height-limited to width-limited at the SAME figure height
``H_axes = W_axes / Σaspect``.  Ignoring the horizontal margins (tick labels,
colourbars, padding) that only *shrink* ``W_axes`` makes ``W_fig / Σaspect`` a
safe upper bound on the required axes height, so

    inverted_aspect_ratio ≈ 1 / Σaspect + vmargin

never produces inter-panel gaps.  Any slack at the top/bottom is harmless
because ``save_pub`` (``bbox_inches="tight"``) crops it at save time.

``geo_aspect`` supplies the aspect for a PlateCarree / equal-aspect lon-lat map;
pass ``1.0`` for a square scatter/line panel.
"""

from typing import Dict, List, Sequence, Tuple

import numpy as np


def geo_aspect(lon0, lon1, lat0, lat1, lat_ref=None) -> float:
    """Display width/height of an equal-aspect lon-lat (PlateCarree) map panel.

    ``set_aspect("equal")`` on a lon-lat axes (cartopy / salem / ``imshow`` of a
    lon-lat field) draws one degree of longitude shorter than one degree of
    latitude by ``cos(lat)``.  The on-screen box aspect is therefore

        (Δlon · cos(lat_ref)) / Δlat

    Feed the result to ``width_ratios`` (and to :func:`row_layout`).

    Parameters
    ----------
    lon0, lon1, lat0, lat1:
        Panel extent in degrees (order within each pair does not matter).
    lat_ref:
        Latitude (deg) at which to evaluate ``cos`` — defaults to the box centre.
    """
    dlon = abs(float(lon1) - float(lon0))
    dlat = abs(float(lat1) - float(lat0))
    if dlon == 0 or dlat == 0:
        raise ValueError("geo_aspect: degenerate extent (Δlon or Δlat is zero)")
    if lat_ref is None:
        lat_ref = 0.5 * (float(lat0) + float(lat1))
    return dlon * float(np.cos(np.deg2rad(lat_ref))) / dlat


def row_layout(
    aspects: Sequence[float],
    *,
    vmargin: float = 0.10,
    safety: float = 1.0,
) -> Dict[str, object]:
    """Estimate ``width_ratios`` and ``inverted_aspect_ratio`` for a 1-row figure.

    Parameters
    ----------
    aspects:
        Width/height of each panel.  Use :func:`geo_aspect` for maps and ``1.0``
        for a square panel (scatter with equal limits, etc.).
    vmargin:
        Vertical room (as a fraction of figure WIDTH) reserved for titles and
        tick labels above/below the panels.  ~0.10 suits a Nature-style row with
        a title and lon/lat labels; raise it if titles/labels are large.
    safety:
        Multiplier (≥ 1) on the ``1/Σaspect`` core term.  The estimate already
        errs tall; only bump this if a panel still shows side gaps.

    Returns
    -------
    dict with ``"width_ratios"`` (list, ∝ aspect) and ``"inverted_aspect_ratio"``
    (float).  Pass the latter to :func:`EasyPlotLib.journal_style` /
    :func:`EasyPlotLib.figsizes`, and the former to ``plt.subplots(gridspec_kw=)``.

    Examples
    --------
    >>> asp = [geo_aspect(112, 122, 32, 40), geo_aspect(112, 122, 32, 40), 1.0]
    >>> lay = row_layout(asp)
    >>> epl.journal_style("nat2", nrows=1, ncols=3,
    ...                   inverted_aspect_ratio=lay["inverted_aspect_ratio"])
    >>> fig, axs = plt.subplots(1, 3,
    ...                         gridspec_kw=dict(width_ratios=lay["width_ratios"]))
    """
    a: List[float] = [float(x) for x in aspects]
    if not a:
        raise ValueError("row_layout: need at least one aspect")
    if any(x <= 0 for x in a):
        raise ValueError(f"row_layout: aspects must be positive, got {a}")
    s = sum(a)
    return {
        "width_ratios": a,
        "inverted_aspect_ratio": safety / s + vmargin,
    }


def clamp_colorbars(fig, *pairs: Tuple) -> None:
    """Freeze constrained layout and clamp each colourbar to its panel's height.

    An equal-aspect map fills only part of its (taller) cell, but a colourbar
    attached with ``fig.colorbar(..., ax=ax)`` is sized to the CELL, so it ends
    up taller than the map it labels.  Call this AFTER all panels and colourbars
    are drawn: it lets constrained layout place the colourbars (to the right, no
    overlap), then freezes the layout and clamps each colourbar's bottom/height
    to its panel's drawn box (horizontal position is left untouched).

    Parameters
    ----------
    fig:
        The figure.
    *pairs:
        ``(panel_axes, colorbar)`` tuples.  ``colorbar`` may be a ``Colorbar``
        or a bare colourbar ``Axes``.
    """
    fig.canvas.draw()
    fig.set_layout_engine("none")
    for panel_ax, cb in pairs:
        cax = getattr(cb, "ax", cb)
        pm = panel_ax.get_position()
        pc = cax.get_position()
        cax.set_position([pc.x0, pm.y0, pc.width, pm.height])
