"""Publication-grade chart, annotation, and QA helpers.

These implement the *correctness & legibility* toolkit that the ``sci-figure``
skill's ``references/figure-rules.md`` checklist refers to (its §3–§9). They are
plain matplotlib — no house aesthetic — and compose with
:func:`EasyPlotLib.journal_style` (which already sets the role-mapped font ladder,
outward ticks, frameless legends and Type-42 editable fonts, so it is this
library's equivalent of the skill's ``apply_figure_style()``).

Helpers
-------
set_frame            §3   per-axes spine visibility (open / boxed / none)
bar_with_points      §6.1 bar = mean, overlay raw points OR a t-CI/SD interval
strip_with_median    §6.1 jittered points + a bold median tick per group
goodness_arrow       §3.6 upright "higher = better" direction-of-goodness cue
end_of_line_labels   §6.3 direct-label each line at its right end (no legend box)
two_tier_label       §5   two-line "name / metadata" label string
panel_crops          §9.2 per-panel pixel crop boxes in the SAVED png, for the
                          render-then-verify perceptual pass
"""

META_GREY = "#888888"


def set_frame(ax, style="open"):
    """§3: set spine visibility on an existing axes.

    ``style`` ∈ ``{"open", "boxed", "none"}`` — ``"open"`` keeps only the bottom
    and left spines (the journal default), ``"boxed"`` all four, ``"none"`` none.
    Ticks are re-pointed outward; ``"none"`` also hides tick marks.
    """
    show = {
        "open": (False, False, True, True),
        "boxed": (True, True, True, True),
        "none": (False, False, False, False),
    }[style]
    for side, vis in zip(("top", "right", "bottom", "left"), show):
        ax.spines[side].set_visible(vis)
        if vis:
            ax.spines[side].set_linewidth(0.6)
    ax.tick_params(direction="out", length=0 if style == "none" else 3, width=0.6)
    return ax


def bar_with_points(
    ax,
    x,
    ymat,
    labels,
    colors,
    jitter=0.08,
    show_points=True,
    errorbar=None,
    point_alpha=0.5,
    point_size=8,
):
    """§6.1: bar = mean; optionally overlay raw points OR draw an interval.

    Show the distribution, not just the summary. Raw-point overlays and error
    bars are alternatives — showing both is usually redundant, so ``errorbar`` is
    honoured only when ``show_points`` is ``False``.

    Parameters
    ----------
    ax:
        Target axes.
    x:
        Bar positions (one per group).
    ymat:
        Sequence of per-group value arrays (the raw observations).
    labels:
        Per-group x tick labels.
    colors:
        Per-group colour list, e.g. from :func:`EasyPlotLib.focal_palette`.
    errorbar:
        ``None`` | ``"sd"`` | ``"ci95"``. ``"ci95"`` is the t-distribution 95 %
        CI of the mean (half-width ``t_{0.975,n-1}·s/√n``) — correct at small n,
        where the ``1.96·s/√n`` z-approximation is markedly too narrow. Requires
        SciPy only for ``"ci95"``.
    """
    import numpy as np

    means = np.array([np.mean(y) for y in ymat], float)
    err = None
    if errorbar and not show_points:
        if errorbar == "sd":
            err = np.array(
                [np.std(y, ddof=1) if np.asarray(y).size > 1 else 0 for y in ymat]
            )
        elif errorbar == "ci95":
            from scipy.stats import t

            def _hw(y):
                n = np.asarray(y).size
                return (
                    t.ppf(0.975, n - 1) * np.std(y, ddof=1) / np.sqrt(n)
                    if n > 1
                    else 0
                )

            err = np.array([_hw(y) for y in ymat])
        else:
            raise ValueError(f"errorbar must be None|'sd'|'ci95', got {errorbar!r}")
    ax.bar(
        x,
        means,
        color=colors,
        width=0.7,
        edgecolor="none",
        yerr=err,
        error_kw={"elinewidth": 0.8, "capsize": 0},
    )
    if show_points:
        for xi, ys in zip(x, ymat):
            ys = np.asarray(ys)
            if ys.ndim and ys.size > 1:
                jit = (np.random.rand(ys.size) - 0.5) * 2 * jitter
                ax.scatter(
                    np.full(ys.size, xi) + jit,
                    ys,
                    s=point_size,
                    color="black",
                    alpha=point_alpha,
                    zorder=3,
                    linewidths=0,
                )
    ax.set_xticks(x)
    ax.set_xticklabels(labels)
    return ax


def strip_with_median(ax, groups, values, colors=None, jitter=0.12):
    """§6.1: jittered points + a bold horizontal median tick per group.

    The preferred categorical × numeric chart at small n — it shows every
    observation instead of hiding the spread inside a bar.
    """
    import numpy as np

    labs = list(groups)
    if colors is None:
        colors = ["#444444"] * len(labs)
    for i, (ys, c) in enumerate(zip(values, colors)):
        ys = np.asarray(ys)
        jit = (np.random.rand(ys.size) - 0.5) * 2 * jitter
        ax.scatter(
            np.full(ys.size, i) + jit, ys, s=10, color=c, alpha=0.6, linewidths=0, zorder=2
        )
        m = np.median(ys)
        ax.plot([i - 0.22, i + 0.22], [m, m], color="black", lw=1.6, zorder=3)
    ax.set_xticks(range(len(labs)))
    ax.set_xticklabels(labs)
    return ax


def goodness_arrow(ax, text="higher = better", loc="upper left", axis="y", fontsize=None):
    """§3.6: a small upright direction-of-goodness cue in the margin.

    Place it once per row of panels (never per panel, never only in the caption)
    when higher- or lower-is-better is not obvious from the axis label.
    """
    import matplotlib.pyplot as plt

    if fontsize is None:
        fontsize = plt.rcParams["legend.fontsize"]  # secondary / annotation role
    pos = {
        "upper left": (0.02, 0.98),
        "upper right": (0.98, 0.98),
        "lower left": (0.02, 0.02),
        "lower right": (0.98, 0.02),
    }[loc]
    ha = "left" if "left" in loc else "right"
    va = "top" if "upper" in loc else "bottom"
    arrow = "↑ " if axis == "y" else "→ "
    ax.text(
        pos[0], pos[1], arrow + text, transform=ax.transAxes,
        fontsize=fontsize, color=META_GREY, ha=ha, va=va,
    )
    return ax


def two_tier_label(name, meta):
    """§5: two-line ``"name\\nmetadata"`` label string.

    Style the metadata line separately at the caller (e.g. smaller / grey).
    """
    return f"{name}\n{meta}"


def end_of_line_labels(ax, xs, ys, labels, colors=None, dx=0.01, fontsize=None):
    """§6.3 / §7.3: label each line series at its right end instead of a legend box.

    ``xs``/``ys`` are per-series coordinate sequences; each label is placed just
    past the last point of its line.
    """
    import matplotlib.pyplot as plt

    if fontsize is None:
        fontsize = plt.rcParams["font.size"]  # base / series-identity role
    if colors is None:
        colors = [None] * len(labels)
    span = ax.get_xlim()[1] - ax.get_xlim()[0]
    for x, y, lab, c in zip(xs, ys, labels, colors):
        ax.text(
            x[-1] + dx * span, y[-1], lab, color=c, va="center", ha="left", fontsize=fontsize
        )
    return ax


def panel_crops(fig, dpi=None, pad_px=6, bbox_inches=None, pad_inches=None):
    """§9.2: pixel-space crop boxes for each lettered panel in the SAVED png.

    Returns ``{letter: (x0, y0, x1, y1)}`` in image-space pixels (origin
    top-left, matching ``PIL.Image.crop`` and the ``Read`` tool's view of a
    saved png). Use it to drive the render-then-verify *perceptual* pass: save
    the figure, then look at each panel crop for low-contrast labels, crossing
    leaders, or series colours mistakable for one another — defects the geometric
    (bbox) check cannot catch.

    Panels are detected as bold single-character ``Text`` objects (e.g. from
    :func:`EasyPlotLib.subplot_labels`); each crop is that axes' tight bbox mapped
    into the saved file's pixel space, padded by ``pad_px``. For §3.4 composites
    (abutting subplots sharing an axis, letter on the leftmost only) the crop
    unions in the letterless ``sharex``/``sharey`` siblings on the same grid
    row/col. When no axes carries a panel letter, falls back to one crop per axes
    keyed by index.

    ``bbox_inches`` mirrors ``Figure.savefig`` semantics: ``None`` means *consult
    rcParams* (so under :func:`EasyPlotLib.journal_style`, which sets
    ``savefig.bbox='tight'``, it resolves to ``'tight'``); pass an explicit
    ``Bbox`` only if you saved with one. Boxes are clamped to the saved extent.

        >>> fig.savefig("fig.png")            # bbox_inches='tight' via rcParams
        >>> boxes = epl.panel_crops(fig)      # {'a': (x0, y0, x1, y1), ...}
        >>> from PIL import Image
        >>> Image.open("fig.png").crop(boxes["a"]).save("panel_a.png")
    """
    import matplotlib as mpl
    import matplotlib.text
    from matplotlib.transforms import Bbox, BboxBase

    if dpi is None:
        dpi = mpl.rcParams.get("savefig.dpi", fig.dpi)
        if dpi == "figure":
            dpi = fig.dpi
    dpi = float(dpi)
    if bbox_inches is None:
        bbox_inches = mpl.rcParams.get("savefig.bbox")
    fig.canvas.draw()
    r = fig.canvas.get_renderer()
    # Saved-image frame in *inches*: origin (ox_in, oy_in), size (W_in, H_in).
    if bbox_inches == "tight":
        if pad_inches is None:
            pad_inches = mpl.rcParams.get("savefig.pad_inches", 0.1)
        tb = fig.get_tightbbox(r)
        assert tb is not None
        tb = tb.padded(pad_inches)
        ox_in, oy_in = tb.x0, tb.y0
        W_in, H_in = tb.width, tb.height
    elif isinstance(bbox_inches, BboxBase):
        ox_in, oy_in = bbox_inches.x0, bbox_inches.y0
        W_in, H_in = bbox_inches.width, bbox_inches.height
    else:
        ox_in, oy_in = 0.0, 0.0
        W_in, H_in = fig.get_size_inches()
    W_px, H_px = int(round(W_in * dpi)), int(round(H_in * dpi))
    lettered = {}
    for ax in fig.axes:
        for t in ax.findobj(matplotlib.text.Text):
            s = (t.get_text() or "").strip()
            if len(s) == 1 and s.isalpha() and t.get_fontweight() in ("bold", 700):
                lettered[ax] = s
                break
    # No panel letters (standalone plot): fall back to one crop per axes so the
    # §9.2 loop still inspects something instead of silently iterating over {}.
    if not lettered:
        lettered = {ax: str(i) for i, ax in enumerate(fig.axes)}
    out = {}
    for ax, letter in lettered.items():
        bbs = [ax.get_tightbbox(r)]  # display px at fig.dpi
        # §3.4: a composite panel (abutting subplots sharing an axis, letter on
        # the leftmost only) spans its letterless sharex/sharey siblings in the
        # same grid row/col — NOT the whole grid that subplots(sharey=True) joins.
        ss = ax.get_subplotspec()
        for sib in fig.axes:
            if sib is ax or sib in lettered:
                continue
            ssib = sib.get_subplotspec()
            same_row = ss is None or ssib is None or ss.rowspan == ssib.rowspan
            same_col = ss is None or ssib is None or ss.colspan == ssib.colspan
            if (ax.get_shared_y_axes().joined(ax, sib) and same_row) or (
                ax.get_shared_x_axes().joined(ax, sib) and same_col
            ):
                bbs.append(sib.get_tightbbox(r))
        bb = Bbox.union(bbs)
        # display-px → inches → saved-frame inches → saved px (y flipped)
        bx0 = (bb.x0 / fig.dpi - ox_in) * dpi
        bx1 = (bb.x1 / fig.dpi - ox_in) * dpi
        by0 = H_px - (bb.y1 / fig.dpi - oy_in) * dpi
        by1 = H_px - (bb.y0 / fig.dpi - oy_in) * dpi
        out[letter] = (
            max(int(bx0) - pad_px, 0),
            max(int(by0) - pad_px, 0),
            min(int(bx1) + pad_px, W_px),
            min(int(by1) + pad_px, H_px),
        )
    return out
