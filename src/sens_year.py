"""
sens.py - analisis sensitivitas energi AC (61 hari, CODiS Taichung April-Mei 2026).
Faktor tak pasti: lihat FACTORS. Semua rentang adalah ASUMSI yang ditulis jelas;
peringkat pengaruh bergantung pada rentang tersebut.
"""
import glob, time, os
import numpy as np, pandas as pd
import pvlib
import config as cfg, cwa_month as cm, weather as wx, inverter_model as im

# ---------- data tetap (satu tahun 2023, CODiS 467270) ----------
Yd = __import__("io_year").load_year()
W = Yd
GHI0 = Yd["ghi_codis"].fillna(0.0)
TAIR = Yd["T_codis"].interpolate().bfill().ffill()
IDX = Yd.index
SITE = wx.make_location()
DOY = pd.Series(IDX.dayofyear, index=IDX)
DAY = IDX.normalize()
WIND = 2.0   # m/s, ASUMSI (angin tidak ada di data)

TS_OFFSET = {"tengah": 0.0, "awal": -0.5, "akhir": 0.5}     # geser waktu posisi matahari (jam)
SP = {}
for k, off in TS_OFFSET.items():
    t = IDX + pd.Timedelta(hours=off)
    sp = SITE.get_solarposition(t); sp.index = IDX
    am = SITE.get_airmass(t, solar_position=sp.set_axis(t))["airmass_relative"]; am.index = IDX
    ex = pd.Series(np.asarray(pvlib.irradiance.get_extra_radiation(t)), index=IDX)
    SP[k] = (sp, am, ex)

DECOMP = ["erbs", "disc", "boland", "orgill_hollands"]
TRANSP = ["isotropic", "klucher", "haydavies", "reindl", "perez"]
TCELL = ["ross", "faiman", "sapm"]
TSS = list(TS_OFFSET)
MAPS = list(cfg.MAPPING_OPTIONS)
INVM = im.MODELS

GERR = float(os.environ.get("GHI_ERR", "0.05"))
# nama: (jenis, rentang/pilihan)
FACTORS = {
    "dekomposisi_GHI": ("cat", DECOMP),
    "transposisi":     ("cat", TRANSP),
    "model_suhu_sel":  ("cat", TCELL),
    "geser_waktu":     ("cat", TSS),
    "pemetaan":        ("cat", MAPS),
    "model_inverter":  ("cat", INVM),
    "NOCT":            ("num", (44.0, 48.0)),
    "rugi_DC":         ("num", (0.0, 0.114)),   # 0 = tanpa rugi; 0.114 = default PVWatts v5 Tabel 6 termasuk shading
    "galat_GHI":       ("num", (-GERR, GERR)),    # fraksi, perkalian (1+x)
}
BASE = dict(dekomposisi_GHI="erbs", transposisi="perez", model_suhu_sel="ross", geser_waktu="tengah",
            pemetaan="a", model_inverter="pvwatts_ds", albedo=0.25, NOCT=46.0, rugi_DC=0.087, galat_GHI=0.0)

def decompose(kind, ghi, sp):
    z = sp["zenith"]
    if kind == "erbs":
        r = pvlib.irradiance.erbs(ghi, z, DOY); dni, dhi = r["dni"], r["dhi"]
    elif kind == "disc":
        dni = pvlib.irradiance.disc(ghi, z, DOY)["dni"]
        dhi = ghi - dni * np.cos(np.radians(z))
    elif kind == "boland":
        r = pvlib.irradiance.boland(ghi, z, DOY); dni, dhi = r["dni"], r["dhi"]
    else:
        r = pvlib.irradiance.orgill_hollands(ghi, z, DOY); dni, dhi = r["dni"], r["dhi"]
    dni = pd.Series(np.asarray(dni, float), index=IDX).fillna(0.0).where(z < 87, 0.0).clip(lower=0)
    dhi = pd.Series(np.asarray(dhi, float), index=IDX).fillna(0.0).clip(lower=0)
    return dni, dhi

SA = cfg.SUBARRAYS
N_MOD = sum(s["n_modules"] for s in SA.values())
TILT, AZ = 23.0, 180.0   # sama untuk semua sub-array (dikonfirmasi pengguna)
assert all(s["tilt"] == TILT and s["azimuth"] == AZ for s in SA.values())

def run(p, detail=False):
    ghi = GHI0 * (1.0 + p["galat_GHI"])
    sp, am, ex = SP[p["geser_waktu"]]
    dni, dhi = decompose(p["dekomposisi_GHI"], ghi, sp)
    poa = pvlib.irradiance.get_total_irradiance(
        TILT, AZ, sp["apparent_zenith"], sp["azimuth"], dni, ghi, dhi,
        dni_extra=ex, airmass=am, albedo=p["albedo"], model=p["transposisi"])["poa_global"].fillna(0.0).clip(lower=0.0)
    kind = p["model_suhu_sel"]
    if kind == "ross":
        tc = pvlib.temperature.ross(poa, TAIR, p["NOCT"])
    elif kind == "faiman":
        tc = pvlib.temperature.faiman(poa, TAIR, WIND)
    else:
        tc = pvlib.temperature.sapm_cell(poa, TAIR, WIND, -3.56, -0.075, 3.0)   # open rack, glass/polymer
    pm = pvlib.pvsystem.pvwatts_dc(poa, tc, cfg.MODULE["pmax_stc_w"], cfg.MODULE["gamma_pdc"], 25.0)
    pm = (pm * (1 - p["rugi_DC"])).clip(lower=0.0)
    mapping = cfg.MAPPING_OPTIONS[p["pemetaan"]]
    ac_tot, clip = 0.0, 0.0
    for inv, subs in mapping.items():
        pdc = pm * sum(SA[s]["n_modules"] for s in subs)
        a, r = im.inverter_ac(pdc, cfg.INVERTERS[inv], p["model_inverter"])
        ac_tot = ac_tot + a; clip += float((r - a).sum())
    e = float(ac_tot.sum()) / 1000.0
    if detail:
        return e, clip / 1000.0, ac_tot
    return e, clip / 1000.0

if __name__ == "__main__":
    t0 = time.time(); e, c = run(BASE); t1 = time.time()
    print("Baseline: E_AC = %.1f kWh (stage 2: 36788.7), clip = %.2f kWh, waktu %.3fs" % (e, c, t1 - t0))
