import matplotlib; matplotlib.use("Agg"); import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch
plt.rcParams.update({"font.family": "serif", "font.serif": ["Liberation Serif", "Times New Roman"], "font.size": 7.2})
fig, ax = plt.subplots(figsize=(3.3, 3.25)); ax.set_xlim(0, 10); ax.set_ylim(0, 10.2); ax.axis("off")
boxes = [("Weather input", "GHI, T$_{air}$ (CODiS hourly or ERA5)", "#eeeeee", None),
         ("Solar position, air mass", "location.get_solarposition\nirradiance.get_extra_radiation", "#dcebf7", "pvlib"),
         ("GHI → DNI, DHI", "irradiance.erbs | disc | boland |\norgill_hollands", "#dcebf7", "pvlib"),
         ("Transposition to 23° plane", "irradiance.get_total_irradiance\n(isotropic, klucher, haydavies, reindl, perez)", "#dcebf7", "pvlib"),
         ("Cell temperature", "temperature.ross | faiman | sapm_cell", "#dcebf7", "pvlib"),
         ("DC power per module", "pvsystem.pvwatts_dc  (×372, 8.7% DC loss)", "#dcebf7", "pvlib"),
         ("Inverter (3 units) ← mapping a / b", "constant η | PVWatts-DS | PVWatts-G\nown code = inverter.pvwatts (max diff 0 W)", "#f7e3c8", "this work"),
         ("Plant AC energy", "sum of 3 inverters, hourly → kWh", "#eeeeee", None)]
n = len(boxes); h = 0.98; gap = 0.30; y0 = 10.1
for i, (t, sub, c, tag) in enumerate(boxes):
    y = y0 - (i + 1) * h - i * gap
    ax.add_patch(FancyBboxPatch((0.3, y), 9.4, h, boxstyle="round,pad=0.02,rounding_size=0.12", fc=c, ec="#444", lw=0.6))
    ax.text(5, y + h * 0.72, t, ha="center", va="center", fontweight="bold"); ax.text(5, y + h * 0.27, sub, ha="center", va="center", fontsize=5.9)
    if tag: ax.text(9.55, y + h - 0.12, tag, ha="right", va="top", fontsize=5.2, style="italic", color="#555")
    if i < n - 1: ax.annotate("", xy=(5, y - gap + 0.02), xytext=(5, y), arrowprops=dict(arrowstyle="-|>", lw=0.7, color="#444"))
plt.tight_layout(pad=0.1); plt.savefig("paper_figs/fig_flow.png", dpi=300)
