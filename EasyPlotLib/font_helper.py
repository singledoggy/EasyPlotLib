import os
import matplotlib.font_manager as fm
from matplotlib import rcParamsDefault as _rc_matplotlib_native


def set_custom_fonts():
    font_dir = os.path.join(os.path.dirname(__file__), "font")

    # Add font files to the font manager
    for font_file in os.listdir(font_dir):
        if font_file.endswith(".ttf"):
            fm.fontManager.addfont(os.path.join(font_dir, font_file))

    # Set custom fonts
    _rc_matplotlib_native["font.sans-serif"] = "TeX Gyre Heros"
    _rc_matplotlib_native["font.serif"] = "TeX Gyre Schola"
    _rc_matplotlib_native["font.cursive"] = "TeX Gyre Chorus"
    _rc_matplotlib_native["font.fantasy"] = "TeX Gyre Adventor"
    _rc_matplotlib_native["font.monospace"] = "TeX Gyre Cursor"
