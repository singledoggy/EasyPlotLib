"""Multi-panel figure composition on a mm-accurate column grid.

This is the *mechanical* half of the ``sci-figure`` skill's
``references/figure-composer.md`` workflow: given a **panel outline** (a JSON
description of a 12-column grid — see :func:`figure_outline_schema`) and a saved
PNG per panel, it tiles the panels onto a single publication-width canvas and
stamps the bold panel letters. The *editorial* half (writing the outline,
fanning one sub-agent out per panel, and the adversarial review loop) lives in
the skill, because it orchestrates agents rather than pixels.

Typical use::

    import EasyPlotLib as epl

    outline = {...}                      # validate against figure_outline_schema()
    # ... render each panel to panel_a.png, panel_b.png, ... at epl.panel_px(...)
    paths = {"a": "panel_a.png", "b": "panel_b.png"}
    out_path, (W, H) = epl.compose_figure(outline, paths, "figure.png")

    # perceptual self-QA: look at each panel crop in the composed png
    for letter, box in epl.compose_crops(outline).items():
        ...                              # view figure.png cropped to box
"""

_DPI = 300
_GUTTER_MM = 4


def figure_outline_schema():
    """JSON schema for a multi-panel ``panel_outline`` (validate before composing).

    An outline is ``{claim, width_mm, ncol, row_heights_mm, panels[]}`` where each
    panel places itself on the ``ncol``-column grid via ``row/col/colspan/rowspan``
    and declares its ``role`` (schematic/hero/primary/supporting), ``chart_family``,
    one-sentence ``message`` (takeaway) and ``ask`` (what to draw).
    """
    return {
        "type": "object",
        "properties": {
            "claim": {"type": "string"},
            "width_mm": {"type": "number"},
            "ncol": {"type": "integer"},
            "row_heights_mm": {"type": "array", "items": {"type": "number"}},
            "panels": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {
                        "letter": {"type": "string"},
                        "role": {
                            "type": "string",
                            "enum": ["schematic", "hero", "primary", "supporting"],
                        },
                        "message": {"type": "string"},
                        "chart_family": {"type": "string"},
                        "data_ref": {"type": ["string", "null"]},
                        "data_desc": {"type": "string"},
                        "row": {"type": "integer"},
                        "col": {"type": "integer"},
                        "colspan": {"type": "integer"},
                        "rowspan": {"type": "integer"},
                        "label_budget": {"type": "integer"},
                        "ask": {"type": "string"},
                    },
                    "required": [
                        "letter", "role", "message", "chart_family",
                        "row", "col", "colspan", "ask",
                    ],
                },
            },
        },
        "required": ["claim", "width_mm", "ncol", "row_heights_mm", "panels"],
    }


def grid_geom(outline, dpi=_DPI, gutter_mm=_GUTTER_MM):
    """Resolve an outline's grid to pixels.

    Returns ``(W, ncol, colw, rowh, row_y, g)``: total width px, column count,
    per-column width px, per-row height px list, per-row top-y px list, and the
    gutter in px.
    """
    mm = dpi / 25.4
    W = int(outline["width_mm"] * mm)
    ncol = outline["ncol"]
    g = int(gutter_mm * mm)
    colw = (W - g * (ncol - 1)) // ncol
    rowh = [int(h * mm) for h in outline["row_heights_mm"]]
    row_y = [sum(rowh[:i]) + g * i for i in range(len(rowh))]
    return W, ncol, colw, rowh, row_y, g


def _panel(outline, letter):
    return next(q for q in outline["panels"] if q["letter"] == letter)


def panel_px(outline, letter, dpi=_DPI, gutter_mm=_GUTTER_MM):
    """Exact ``(width_px, height_px)`` a panel must be rendered at to tile cleanly.

    Render each panel figure to this size (``figsize=(w/dpi, h/dpi)``) with
    ``transparent=True`` and **no** ``bbox_inches='tight'`` / ``tight_layout`` /
    ``constrained_layout`` — those change the pixel dimensions and break tiling.
    """
    W, ncol, colw, rowh, row_y, g = grid_geom(outline, dpi, gutter_mm)
    p = _panel(outline, letter)
    cs, rs, r = p["colspan"], p.get("rowspan", 1), p["row"]
    return colw * cs + g * (cs - 1), sum(rowh[r : r + rs]) + g * (rs - 1)


def panel_xy(outline, letter, dpi=_DPI, gutter_mm=_GUTTER_MM):
    """Top-left ``(x_px, y_px)`` of a panel's slot on the composed canvas."""
    W, ncol, colw, rowh, row_y, g = grid_geom(outline, dpi, gutter_mm)
    p = _panel(outline, letter)
    return p["col"] * (colw + g), row_y[p["row"]]


def compose_crops(outline, dpi=_DPI, gutter_mm=_GUTTER_MM, pad_px=4):
    """Pixel crop boxes ``{letter: (x0, y0, x1, y1)}`` for each panel in the
    composed PNG (origin top-left, for ``PIL.Image.crop`` / the ``Read`` tool).

    The PIL-composed mirror of :func:`EasyPlotLib.panel_crops` — use it for the
    perceptual self-QA pass over :func:`compose_figure`'s output.
    """
    W, ncol, colw, rowh, row_y, g = grid_geom(outline, dpi, gutter_mm)
    H = row_y[-1] + rowh[-1]
    out = {}
    for p in outline["panels"]:
        L = p["letter"]
        w, h = panel_px(outline, L, dpi, gutter_mm)
        x, y = panel_xy(outline, L, dpi, gutter_mm)
        out[L] = (
            max(x - pad_px, 0),
            max(y - pad_px, 0),
            min(x + w + pad_px, W),
            min(y + h + pad_px, H),
        )
    return out


def compose_figure(
    outline,
    panel_paths,
    out_path,
    dpi=_DPI,
    gutter_mm=_GUTTER_MM,
    letter_font="DejaVuSans-Bold.ttf",
    letter_pt=9,
    letter_case="lower",
):
    """Tile per-panel PNGs onto the outline's grid and stamp bold panel letters.

    Parameters
    ----------
    outline:
        A ``panel_outline`` (see :func:`figure_outline_schema`).
    panel_paths:
        ``{letter: png_path}`` — each rendered at :func:`panel_px`. Any panel not
        already at its slot size is resized to fit.
    out_path:
        Where to save the composed figure.
    letter_case:
        ``"lower"`` or ``"upper"`` — follow the target venue's convention.

    Returns
    -------
    (out_path, (W, H))
        The saved path and the composed pixel size.
    """
    from PIL import Image, ImageDraw, ImageFont

    W, ncol, colw, rowh, row_y, g = grid_geom(outline, dpi, gutter_mm)
    H = row_y[-1] + rowh[-1]
    canvas = Image.new("RGB", (W, H), "white")
    draw = ImageDraw.Draw(canvas)
    try:
        ft = ImageFont.truetype(letter_font, int(letter_pt / 72 * dpi))
    except Exception:
        ft = ImageFont.load_default()
    for p in outline["panels"]:
        L = p["letter"]
        w, h = panel_px(outline, L, dpi, gutter_mm)
        x, y = panel_xy(outline, L, dpi, gutter_mm)
        im = Image.open(panel_paths[L]).convert("RGBA")
        if im.size != (w, h):
            im = im.resize((w, h))
        canvas.paste(im, (x, y), im)
        stamp = L.lower() if letter_case == "lower" else L.upper()
        draw.text(
            (x + int(1.5 / 25.4 * dpi), y + int(1 / 25.4 * dpi)),
            stamp, fill="black", font=ft,
        )
    canvas.save(out_path)
    return out_path, (W, H)


def apply_outline_revisions(outline, revisions):
    """Return the set of panel letters that must regenerate after outline-level
    (figure-scale) review revisions.

    The composer applies the geometry/title/label_budget revisions to the
    ``outline`` dict itself; this only computes which panels are in scope so the
    review loop regenerates exactly those and leaves clean panels untouched.
    """
    affected = set()
    for r in revisions:
        affected |= set(r.get("affected_panels", []))
    return affected
