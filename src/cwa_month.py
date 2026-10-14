"""
cwa_month.py - membaca tabel bulanan CODiS (matriks Hari x Jam) untuk
radiasi (MJ/m2 per jam), suhu (C), dan sinar matahari (jam).
Label jam h = AKHIR jam; waktu yang dipakai = tengah jam (h - 0.5).
"""
import re
import numpy as np
import pandas as pd
import pvlib
import config as cfg
from weather import make_location, MJ_PER_M2_HOUR_TO_W


def _matrix(path):
    d = pd.read_csv(path, encoding="utf-8-sig")
    d = d[d.iloc[:, 0].astype(str).str.fullmatch(r"\d{1,2}")].copy()   # buang baris "總和/平均"
    day = d.iloc[:, 0].astype(int).values
    hrs = [c for c in d.columns if re.fullmatch(r"\d+", str(c))]
    vals = d[hrs].apply(pd.to_numeric, errors="coerce").values
    total_col = pd.to_numeric(d.iloc[:, -1], errors="coerce").values
    return day, np.array([int(h) for h in hrs]), vals, total_col


def month_frame(irr, tmp, sun, year, month):
    """Gabung 3 matriks -> DataFrame per jam (indeks tengah jam)."""
    di, hi, vi, ti = _matrix(irr)
    dt, ht, vt, _ = _matrix(tmp)
    ds, hs, vs, ss = _matrix(sun)
    assert (di == dt).all() and (di == ds).all() and (hi == ht).all() and (hi == hs).all()
    rows = []
    for k, dd in enumerate(di):
        base = pd.Timestamp(year=year, month=month, day=int(dd), tz=cfg.SITE["tz"])
        for j, h in enumerate(hi):
            rows.append((base + pd.Timedelta(hours=float(h) - 0.5),
                         vi[k, j], vt[k, j], vs[k, j]))
    w = pd.DataFrame(rows, columns=["t", "ghi_mj", "temp_air", "sunshine_h"]).set_index("t")
    w["ghi"] = w["ghi_mj"] * MJ_PER_M2_HOUR_TO_W
    # cek jumlah harian terhadap kolom 總和 pada file
    chk = pd.DataFrame({"day": di, "sum_calc": np.nansum(vi, axis=1), "sum_file": ti})
    chk["selisih"] = (chk.sum_calc - chk.sum_file).round(2)
    return w, chk


def decompose(w):
    """GHI -> DNI, DHI dengan Erbs di posisi matahari tengah jam."""
    site = make_location()
    sp = site.get_solarposition(w.index)
    doy = pd.Series(w.index.dayofyear, index=w.index)
    er = pvlib.irradiance.erbs(w["ghi"].fillna(0.0), sp["zenith"], doy)
    w = w.copy()
    w["dni"] = pd.Series(np.asarray(er["dni"], float), index=w.index).fillna(0.0).where(sp["zenith"] < 87, 0.0)
    w["dhi"] = pd.Series(np.asarray(er["dhi"], float), index=w.index).fillna(0.0)
    w["ghi"] = w["ghi"].fillna(0.0)
    w["temp_air"] = w["temp_air"].interpolate().bfill().ffill()
    w["zenith"] = sp["zenith"]
    return w


def load_all(base, year=2026):
    parts, chks = [], []
    for m, name in [(4, "April"), (5, "May")]:
        w, c = month_frame(f"{base}Irradiance_-_{name}.csv".replace("Irradiance", "Irradiance"),
                           f"{base}Tempreature_-_{name}.csv", f"{base}Sunshine_-_{name}.csv", year, m)
        c["month"] = m
        parts.append(w); chks.append(c)
    return decompose(pd.concat(parts)), pd.concat(chks)
