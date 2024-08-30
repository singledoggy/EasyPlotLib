import os
import matplotlib.font_manager as fm
import matplotlib.pyplot as plt

from .cartopy_helper import cartopy_plot_tickmarks
from .figsizes_set import figsizes, subplot_labels
import EasyPlotLib

# register the bundled stylesheets in the matplotlib style library
EasyPlotLib_path = EasyPlotLib.__path__[0]
style_dir = os.path.join(EasyPlotLib_path, "styles")
font_dir = os.path.join(EasyPlotLib_path, "fonts")
# 加载字体
font_files = fm.findSystemFonts(fontpaths=[font_dir])
for font_file in font_files:
    fm.fontManager.addfont(font_file)

# 注册所有 mplstyle
stylesheets = {}
for root, dirs, files in os.walk(style_dir):
    new_stylesheets = plt.style.core.read_style_directory(root)
    stylesheets.update(new_stylesheets)

plt.style.core.update_nested_dict(plt.style.library, stylesheets)
plt.style.core.available[:] = sorted(plt.style.library.keys())
