import os

import matplotlib as mpl
import matplotlib.font_manager as fm
import matplotlib.pyplot as plt

import EasyPlotLib

from .cartopy_helper import cartopy_plot_tickmarks
from .figsizes_set import figsizes, subplot_labels

# register the bundled stylesheets in the matplotlib style library
EasyPlotLib_path = EasyPlotLib.__path__[0]
font_dir = os.path.join(EasyPlotLib_path, "fonts")
styles_path = os.path.join(EasyPlotLib_path, "styles")

font_files = fm.findSystemFonts(fontpaths=[font_dir])
font_files_set = set(font_files)

# 检查是否需要更新缓存
existing_fonts = {font.fname for font in fm.fontManager.ttflist}
if not existing_fonts >= font_files_set:
    for font_file in font_files:
        fm.fontManager.addfont(font_file)

    # 仅当添加了新字体时更新缓存
    cache = os.path.join(
        mpl.get_cachedir(), f"fontlist-v{fm.FontManager.__version__}.json"
    )
    fm.json_dump(fm.fontManager, cache)

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
