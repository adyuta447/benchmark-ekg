"""Gaya grafik hitam putih: font serif, abu-abu, dibedakan marker dan jenis garis."""
import matplotlib.pyplot as plt
from matplotlib import font_manager as fm
fam = next((f for f in ("Times New Roman", "Liberation Serif") if f in {x.name for x in fm.fontManager.ttflist}), "serif")
plt.rcParams.update({"font.family": fam, "font.size": 11, "axes.edgecolor": "#444", "axes.linewidth": .8,
    "axes.spines.top": False, "axes.spines.right": False, "axes.grid": True, "grid.color": "#ddd",
    "grid.linewidth": .6, "axes.axisbelow": True, "figure.dpi": 110, "savefig.dpi": 200})
ST = [dict(color="#000", marker="o", ls="-"), dict(color="#555", marker="s", ls="--"),
      dict(color="#888", marker="^", ls="-."), dict(color="#333", marker="D", ls=":"), dict(color="#999", marker="v", ls="--")]
GRAYS = ["#222", "#555", "#888", "#aaa", "#ccc"]
