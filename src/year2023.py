"""Dataset satu tahun 2023: CODiS 467270 (radiasi per jam) + ERA5 PVGIS. Menyimpan outputs/year2023.pkl"""
import glob, numpy as np, pandas as pd
import config as cfg, cwa_month as cm, weather as wx
import os
U = os.environ.get("RAW_DIR", os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "data", "raw")) + "/"; g = lambda p: sorted(glob.glob(U + p))
TZ = cfg.SITE["tz"]; SITE = wx.make_location()
parts, qc = [], []
for m in range(1, 13):
    f = g(f"*467270-2023-{m:02d}-GlobalSolarRadiation-hour.csv")[0]
    di, hi, vi, ti = cm._matrix(f)
    for k, dd in enumerate(di):
        base = pd.Timestamp(year=2023, month=m, day=int(dd), tz=TZ)
        for j, h in enumerate(hi): parts.append((base + pd.Timedelta(hours=float(h) - 0.5), vi[k, j]))
    qc.append(dict(bulan=m, hari=len(di), NaN=int(np.isnan(vi).sum()), selisih_maks=float(np.nanmax(np.abs(np.nansum(vi, axis=1) - ti))),
                   total_MJ=float(np.nansum(vi))))
Q = pd.DataFrame(qc); print(Q.round(2).to_string(index=False)); Q.to_csv("outputs/year_qc.csv", index=False)
tp = []
for m in range(1, 13):
    f = g(f"*467270-2023-{m:02d}-AirTemperature-hour*.csv")[0]
    di, hi, vi, ti = cm._matrix(f)
    for k, dd in enumerate(di):
        base = pd.Timestamp(year=2023, month=m, day=int(dd), tz=TZ)
        for j, h in enumerate(hi): tp.append((base + pd.Timedelta(hours=float(h) - 0.5), vi[k, j]))
TS = pd.DataFrame(tp, columns=["t", "T"]).set_index("t")["T"]
print("suhu stasiun: NaN", int(TS.isna().sum()), list(TS.index[TS.isna()].strftime("%m-%d %H:%M")), " min %.1f maks %.1f rata %.2f" % (TS.min(), TS.max(), TS.mean()))
TS = TS.interpolate(limit=3)
C = pd.DataFrame(parts, columns=["t", "ghi_mj"]).set_index("t")
C["ghi"] = C.ghi_mj * 1e6 / 3600
nan_h = C.ghi.isna(); print("jam NaN radiasi:", int(nan_h.sum()), list(C.index[nan_h].strftime("%m-%d %H:%M")))
C["ghi"] = C.ghi.interpolate(limit=2)
e = pd.read_csv(g("*Timeseries_24.066_120.559_E5*")[0], skiprows=8, nrows=8760)
e["t"] = pd.to_datetime(e["time"], format="%Y%m%d:%H%M", utc=True).dt.tz_convert(TZ); e = e.set_index("t")
e["ghi"] = e["Gb(i)"] + e["Gd(i)"] + e["Gr(i)"]
E = e.reindex(C.index); print("ERA5 NaN:", int(E.ghi.isna().sum()), "pada", list(E.index[E.ghi.isna()].strftime("%m-%d %H:%M"))[:10])
out = pd.DataFrame({"ghi_codis": C.ghi, "ghi_era5": E.ghi.fillna(0.0), "gb_era5": E["Gb(i)"].fillna(0.0), "gd_era5": E["Gd(i)"].fillna(0.0), "T_era5": E.T2m.bfill(), "T_codis": TS.reindex(C.index)})
print("beda suhu ERA5-stasiun: bias %.2f RMSE %.2f C" % ((out.T_era5 - out.T_codis).mean(), np.sqrt(((out.T_era5 - out.T_codis) ** 2).mean())))
import io_year; io_year.save_year(out); print(out.shape, "tahunan GHI CODiS %.0f  ERA5 %.0f kWh/m2" % (out.ghi_codis.sum() / 1000, out.ghi_era5.sum() / 1000))
