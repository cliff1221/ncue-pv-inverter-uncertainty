import numpy as np, pandas as pd, matplotlib; matplotlib.use("Agg")
import matplotlib.pyplot as plt, matplotlib.dates as mdates
plt.rcParams.update({"font.family": "serif", "font.serif": ["Liberation Serif", "Times New Roman"], "font.size": 7.5, "axes.linewidth": 0.6})
# --- Fig daily
d = pd.read_csv("outputs/yr_baseline_harian.csv", index_col=0, parse_dates=True); d.index = pd.to_datetime(d.index, utc=True).tz_convert("Asia/Taipei").tz_localize(None)
col = {"cerah": "#d9822b", "sebagian": "#6aa0c7", "mendung": "#7a7a7a"}; lab = {"cerah": "Clear ($k_t$ > 0.75)", "sebagian": "Partly cloudy", "mendung": "Overcast ($k_t$ < 0.4)"}
fig, ax = plt.subplots(figsize=(3.3, 2.0))
for k in ["cerah", "sebagian", "mendung"]:
    s = d[d.kelas == k]; ax.bar(s.index, s.ac_kWh, width=1.0, color=col[k], label=lab[k])
ax.set_ylabel("Daily AC energy (kWh)"); ax.xaxis.set_major_locator(mdates.MonthLocator(bymonth=[1, 4, 7, 10])); ax.xaxis.set_major_formatter(mdates.DateFormatter("%b"))
ax.set_xlim(d.index.min(), d.index.max()); ax.legend(frameon=False, fontsize=6.3, ncol=3, loc="upper center", bbox_to_anchor=(0.5, 1.17), handlelength=1, columnspacing=0.7)
ax.spines[["top", "right"]].set_visible(False); plt.tight_layout(); plt.savefig("paper_figs/fig_daily.png", dpi=300); plt.close()
# --- Fig hourly (a) scatter (b) monthly energy
D = pd.read_csv("outputs/yr_era5_vs_codis_data.csv", index_col=0, parse_dates=True); R = pd.read_csv("outputs/yr_model_energi.csv"); R["bulan"] = R.bulan.astype(str)
fig, ax = plt.subplots(1, 2, figsize=(3.4, 1.9), gridspec_kw=dict(width_ratios=[1, 1.45]))
ax[0].hexbin(D.codis, D.era5, gridsize=35, cmap="viridis", mincnt=1, bins="log"); ax[0].plot([0, 1100], [0, 1100], "r-", lw=.8)
ax[0].set_xlabel("CODiS GHI (W/m$^2$)"); ax[0].set_ylabel("ERA5 GHI (W/m$^2$)"); ax[0].set_title("(a) Hourly GHI", fontsize=7)
v = R[(R.mapping == "a") & (R.inverter == "pvwatts_ds") & (R.bulan != "all")]; x = np.arange(12); w = .4
for k, (s, lb) in enumerate([("CODiS", "CODiS GHI"), ("ERA5 (GHI)", "ERA5 GHI")]):
    y = v[v.sumber == s].assign(b=lambda t: t.bulan.astype(int)).sort_values("b").E_AC_kWh.values / 1000
    ax[1].bar(x + (k - .5) * w, y, w, label=lb)
ax[1].set_xticks(x); ax[1].set_xticklabels(list("JFMAMJJASOND")); ax[1].set_ylabel("Monthly AC energy (MWh)"); ax[1].set_ylim(0, 27)
ax[1].legend(frameon=False, ncol=2, loc="upper center", fontsize=5.8, handlelength=1, columnspacing=0.8); ax[1].set_title("(b) Monthly AC energy", fontsize=7)
for a in ax: a.spines[["top", "right"]].set_visible(False)
plt.tight_layout(); plt.savefig("paper_figs/fig_hourly.png", dpi=300); plt.close(); print("ok")
