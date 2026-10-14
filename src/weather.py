"""
weather.py  -  menyediakan data cuaca untuk model.

Dua cara:
  1. clearsky_weather(...)  : langit cerah teoretis (batas ATAS produksi)
  2. csv_weather(path)      : file CSV Anda sendiri. Kolom wajib:
        timestamp, ghi, dni, dhi, temp_air
     (W/m2 untuk irradiansi, derajat C untuk suhu). Zona waktu lokal.

Semua fungsi mengembalikan DataFrame dengan indeks waktu (tz-aware)
dan kolom: ghi, dni, dhi, temp_air.
"""
import pandas as pd
from pvlib.location import Location
import config as cfg


def make_location():
    s = cfg.SITE
    return Location(s["latitude"], s["longitude"], tz=s["tz"],
                    altitude=s["altitude"], name=s["name"])


def clearsky_weather(start, end, freq="1min", temp_air=None):
    """Irradiansi langit cerah (model Ineichen) + suhu konstan."""
    site = make_location()
    times = pd.date_range(start, end, freq=freq, tz=cfg.SITE["tz"])
    cs = site.get_clearsky(times, model="ineichen")
    w = cs[["ghi", "dni", "dhi"]].copy()
    w["temp_air"] = cfg.TEMP_AIR_DEFAULT_C if temp_air is None else temp_air
    return w


def csv_weather(path):
    """Baca cuaca dari CSV (kolom: timestamp, ghi, dni, dhi, temp_air)."""
    w = pd.read_csv(path, index_col="timestamp", parse_dates=True)
    if w.index.tz is None:
        w.index = w.index.tz_localize(cfg.SITE["tz"])
    missing = {"ghi", "dni", "dhi", "temp_air"} - set(w.columns)
    if missing:
        raise ValueError(f"Kolom hilang di {path}: {missing}")
    return w[["ghi", "dni", "dhi", "temp_air"]]


# ---------------------------------------------------------------
# CWA (CODiS) - file PER JAM untuk SATU HARI, mis. 467490-2026-05-05.csv
# (satu file berisi semua item: suhu, RH, hujan, sunshine, GloblRad, awan)
# ---------------------------------------------------------------
import re
import numpy as np
import pvlib

MJ_PER_M2_HOUR_TO_W = 1e6 / 3600.0   # 1 MJ/m2 per jam = 277.78 W/m2 (rata-rata)


def cwa_day_file(path, date=None):
    """
    Baca file CODiS per-jam-satu-hari. Label jam h (1..24) dianggap AKHIR jam
    (interval (h-1, h]); dari data 5 Mei radiasi mulai muncul di label 6,
    cocok dengan itu. Waktu yang dipakai = TENGAH jam (h - 0.5).
    Return DataFrame: ghi (W/m2 rata-rata jam), dni, dhi (Erbs), temp_air,
    plus sunshine_h, precip_mm, cloud_sat, rh.
    """
    if date is None:
        date = re.search(r"(\d{4}-\d{2}-\d{2})", path).group(1)
    d = pd.read_csv(path, encoding="utf-8-sig", skiprows=[0])
    d = d[pd.to_numeric(d["ObsTime"], errors="coerce").notna()].copy()
    d["h"] = d["ObsTime"].astype(int)
    num = lambda c: pd.to_numeric(d[c].replace({"T": 0.05, "/": np.nan, "x": np.nan}), errors="coerce")
    base = pd.Timestamp(date, tz=cfg.SITE["tz"])
    idx = [base + pd.Timedelta(hours=float(h) - 0.5) for h in d["h"]]
    w = pd.DataFrame({
        "ghi": num("GloblRad").values * MJ_PER_M2_HOUR_TO_W,
        "temp_air": num("Temperature").values,
        "rh": num("RH").values,
        "precip_mm": num("Precp").values,
        "sunshine_h": num("Sunshine").values,
        "cloud_sat": num("Cloud Amount Sat").values,
    }, index=pd.DatetimeIndex(idx))
    # dekomposisi GHI -> DNI, DHI (Erbs) di posisi matahari tengah jam
    site = make_location()
    sp = site.get_solarposition(w.index)
    doy = pd.Series(w.index.dayofyear, index=w.index)
    er = pvlib.irradiance.erbs(w["ghi"].fillna(0.0), sp["zenith"], doy)
    er = pd.DataFrame({"dni": np.asarray(er["dni"], dtype=float),
                       "dhi": np.asarray(er["dhi"], dtype=float)}, index=w.index)
    w["dni"] = er["dni"].fillna(0.0).where(sp["zenith"] < 87, 0.0)
    w["dhi"] = er["dhi"].fillna(0.0)
    w["ghi"] = w["ghi"].fillna(0.0)
    w["temp_air"] = w["temp_air"].interpolate().bfill().ffill()
    return w
