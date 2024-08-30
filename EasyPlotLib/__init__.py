import os
import matplotlib.font_manager as fm
import matplotlib.pyplot as plt

from .cartopy_helper import cartopy_plot_tickmarks
from .figsizes_set import figsizes, subplot_labels
import EasyPlotLib

# register the bundled stylesheets in the matplotlib style library
EasyPlotLib_path = EasyPlotLib.__path__[0]
font_dir = os.path.join(EasyPlotLib_path, "fonts")
styles_path = os.path.join(EasyPlotLib_path, "styles")

# add fonts
font_files = fm.findSystemFonts(fontpaths=[font_dir])
for font_file in font_files:
    fm.fontManager.addfont(font_file)

# Reads styles in /styles folder and all subfolders
stylesheets = {}  # plt.style.library is a dictionary
for folder, _, _ in os.walk(styles_path):
    new_stylesheets = plt.style.core.read_style_directory(folder)
    stylesheets.update(new_stylesheets)

# Update dictionary of styles - plt.style.library
plt.style.core.update_nested_dict(plt.style.library, stylesheets)
# Update `plt.style.available`, copy-paste from:
# https://github.com/matplotlib/matplotlib/blob/a170539a421623bb2967a45a24bb7926e2feb542/lib/matplotlib/style/core.py#L266  # noqa: E501
plt.style.core.available[:] = sorted(plt.style.library.keys())
