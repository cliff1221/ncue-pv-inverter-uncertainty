import numpy as np, pandas as pd
import matplotlib; matplotlib.use('Agg')
import matplotlib.pyplot as plt
plt.rcParams.update({'font.family': 'serif', 'font.serif': ['Liberation Serif', 'Times New Roman'], 'font.size': 7.5, 'axes.linewidth': 0.6})
oat = pd.read_csv("outputs/yr05_sens_oat.csv"); S = pd.read_csv("outputs/yr05_sens_sobol.csv").set_index("faktor")
name = {"rugi_DC": "DC loss (0-11.4%)", "galat_GHI": "GHI error (±5%)", "model_inverter": "Inverter model", "transposisi": "Transposition model",
        "model_suhu_sel": "Cell-temperature model", "geser_waktu": "Time-stamp shift", "NOCT": "NOCT (44-48 °C)",
        "dekomposisi_GHI": "Decomposition model", "pemetaan": "Panel-inverter mapping"}
g = oat.groupby("faktor").selisih_persen.agg(["min", "max"]); g["w"] = g["max"] - g["min"]; g = g.sort_values("w")
fig, ax = plt.subplots(figsize=(3.3, 2.6))
y = np.arange(len(g))
ax.barh(y, g["max"].clip(lower=0), color="#2a7ab0", height=0.62); ax.barh(y, g["min"].clip(upper=0), color="#d9822b", height=0.62)
ax.set_yticks(y); ax.set_yticklabels([name[i] for i in g.index]); ax.axvline(0, color="k", lw=0.6)
for yi, f in zip(y, g.index):
    ax.text(10.6, yi, "$S_T$ = %.2f" % max(S.loc[f, "ST"], 0), va="center", fontsize=6.5)
ax.set_xlim(-6, 15.5); ax.set_xlabel("Change in annual AC energy vs. baseline (%)")
ax.spines[["top", "right"]].set_visible(False); plt.tight_layout(); plt.savefig("paper_figs/fig_sens.png", dpi=300); plt.close()
print("ok")
