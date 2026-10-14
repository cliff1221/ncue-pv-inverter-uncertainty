"""Baseline tahunan 2023 (CODiS 467270): energi harian/bulanan, kelas cuaca, per inverter, batas clipping 1 menit."""
import numpy as np, pandas as pd, pvlib
import config as cfg, weather as wx, inverter_model as im, pv_model
import year_compare as yc            # menjalankan ulang perbandingan (cepat) dan menyediakan chain()
Y, IDX, SITE = yc.Y, yc.IDX, yc.SITE
ac, dc, clip, poa = yc.chain(Y.ghi_codis, Y.T_codis)
day = ac.resample("D").sum(); pk = ac.resample("D").max()
cs = SITE.get_clearsky(IDX)["ghi"]; kt = Y.ghi_codis.groupby(IDX.date).sum() / cs.groupby(IDX.date).sum(); kt.index = pd.to_datetime(kt.index).tz_localize(cfg.SITE["tz"])
dd = pd.DataFrame({"ac_kWh": day, "peak_kW": pk}); dd["kt"] = kt.reindex(dd.index).values
dd["kelas"] = pd.cut(dd.kt, [0, 0.4, 0.75, 2], labels=["mendung", "sebagian", "cerah"])
dd["ghi_mj"] = (Y.ghi_codis.resample("D").sum() * 3600 / 1e6).values
dd.to_csv("outputs/yr_baseline_harian.csv")
cls = dd.groupby("kelas", observed=True).agg(n=("ac_kWh", "size"), rata_kWh=("ac_kWh", "mean"))
print(cls.round(1)); print("tahunan AC %.1f MWh, yield %.0f kWh/kWp, harian rata %.1f maks %.1f kWh/kWp, puncak %.1f kW" % (ac.sum()/1000, ac.sum()/139.5, (dd.ac_kWh/139.5).mean(), (dd.ac_kWh/139.5).max(), ac.max()))
print("GHI harian rata %.2f MJ/m2, tahunan %.0f kWh/m2" % (dd.ghi_mj.mean(), Y.ghi_codis.sum()/1000))
print("korelasi kt terhadap AC: n/a;  hari tanpa data kt:", int(dd.kt.isna().sum()))
# per inverter (pvwatts_ds, a dan b)
rows = []
for mp, m in cfg.MAPPING_OPTIONS.items():
    for inv, subs in m.items():
        n = sum(cfg.SUBARRAYS[s]["n_modules"] for s in subs)
        pm = (pvlib.pvsystem.pvwatts_dc(poa, pvlib.temperature.ross(poa, Y.T_codis, cfg.MODULE["noct_c"]), cfg.MODULE["pmax_stc_w"], cfg.MODULE["gamma_pdc"], 25.0) * (1 - yc.LOSS)).clip(lower=0) * n
        a, r = im.inverter_ac(pm, cfg.INVERTERS[inv], "pvwatts_ds")
        rows.append(dict(pemetaan=mp, inverter=inv, modul=n, dc_ac=n * 375 / cfg.INVERTERS[inv]["pac_w"], jam_clip=int(((r - a) > 0).sum()), clip_kWh=float((r - a).sum()) / 1000, ac_kWh=float(a.sum()) / 1000, puncak_kW=float(a.max()) / 1000))
P = pd.DataFrame(rows); P.to_csv("outputs/yr_per_inverter.csv", index=False); print(P.round(3).to_string(index=False))
# batas clipping: langit cerah 1 menit sepanjang tahun vs rata-rata jam, dengan suhu stasiun, tanpa dan dengan rugi DC
t1 = pd.date_range("2023-01-01 00:00", "2023-12-31 23:59", freq="1min", tz=cfg.SITE["tz"])
csm = SITE.get_clearsky(t1, model="ineichen")[["ghi", "dni", "dhi"]]
ta = Y.T_codis.reindex(Y.T_codis.index.union(t1)).interpolate().reindex(t1).bfill().ffill()
w1 = csm.copy(); w1["temp_air"] = ta.values
hr = csm.groupby(pd.Grouper(freq="1h", label="left", closed="left")).mean(); hr.index = hr.index + pd.Timedelta(minutes=30)
wh = hr.copy(); wh["temp_air"] = Y.T_codis.reindex(wh.index).values
out = []
for loss in (0.0, yc.LOSS):
    d1 = pv_model.simulate_dc(w1, dc_loss_fraction=loss); dh = pv_model.simulate_dc(wh, dc_loss_fraction=loss)
    for mk, m in cfg.MAPPING_OPTIONS.items():
        a1, r1, _ = im.simulate_ac(d1, m, "pvwatts_ds"); ah, rh, _ = im.simulate_ac(dh, m, "pvwatts_ds")
        e1 = a1.sum().sum() / 60 / 1000; eh = ah.sum().sum() / 1000
        out.append(dict(rugi_DC=loss, pemetaan=mk, E_1min_kWh=e1, E_jam_kWh=eh, clip_1min_kWh=(r1 - a1).sum().sum() / 60 / 1000, clip_jam_kWh=(rh - ah).sum().sum() / 1000,
                        puncak_1min_kW=a1.sum(axis=1).max() / 1000, puncak_jam_kW=ah.sum(axis=1).max() / 1000))
O = pd.DataFrame(out); O["clip_1min_pct"] = O.clip_1min_kWh / O.E_1min_kWh * 100; O["clip_jam_pct"] = O.clip_jam_kWh / O.E_jam_kWh * 100
O.to_csv("outputs/yr_clip_resolusi.csv", index=False); print(O.round(3).to_string(index=False))
