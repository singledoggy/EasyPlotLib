"""Visual check that panel labels (a, b, c …) render at the 8 pt bold default."""

import os

import numpy as np
import matplotlib.pyplot as plt

import EasyPlotLib as epl

HERE = os.path.dirname(os.path.abspath(__file__))

epl.journal_style("nat2", palette="nature", nrows=2, ncols=2)

x = np.linspace(0, 10, 100)
fig, axs = plt.subplots(2, 2)
for n, ax in enumerate(axs.flatten()):
    ax.plot(x, np.sin(x + n))
    ax.set_xlabel("x axis (units)")
    ax.set_ylabel("y axis (units)")
    ax.annotate(**epl.subplot_labels(n, "a"))  # 8 pt bold default

d = epl.subplot_labels(0, "a")
print("subplot_labels fontsize ->", d["fontsize"], "| weight ->", d["weight"])
print("base font.size (rc)      ->", plt.rcParams["font.size"])

out = os.path.join(HERE, "test_subplot_labels.png")
fig.savefig(out, dpi=300)
print("saved", out)
