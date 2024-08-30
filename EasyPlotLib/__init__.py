import os
import matplotlib.font_manager as fm
import matplotlib.pyplot as plt
import pkg_resources

from .cartopy_helper import cartopy_plot_tickmarks
from .figsizes_set import figsizes, subplot_labels

# 获取资源目录的路径，假设 'fonts' 和 'styles' 目录已经在你的包数据中
font_dir = pkg_resources.resource_filename(__name__, "fonts")
style_dir = pkg_resources.resource_filename(__name__, "styles")

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
