"""
inverter_model.py  -  tiga cara memodelkan inverter (DC -> AC).

  "constant"      : P_ac = eta_peak * P_dc, lalu dipotong di daya AC maks.
                    (cara sederhana yang dipakai kode lama Anda)
  "pvwatts_ds"    : model PVWatts (efisiensi turun saat beban rendah),
                    eta_nominal = efisiensi PUNCAK datasheet.
                    CATATAN: ini batas atas; efisiensi terbobot datasheet
                    tidak tersedia.
  "pvwatts_gen"   : PVWatts dengan eta_nominal 0.96 (bawaan pvlib),
                    sebagai pembanding pesimis.

Setiap fungsi mengembalikan (ac_terpotong, ac_tanpa_potong) supaya
energi yang hilang karena clipping bisa dihitung.
"""
import numpy as np
import pandas as pd
import pvlib
import config as cfg

MODELS = ["constant", "pvwatts_ds", "pvwatts_gen"]
ETA_REF = 0.9637  # konstanta referensi PVWatts


def _pvwatts_unclipped(pdc, pdc0, eta_nom):
    pdc = np.asarray(pdc, dtype=float)
    zeta = pdc / pdc0
    safe = np.where(pdc == 0, 1.0, zeta)
    eta = eta_nom / ETA_REF * (-0.0162 * zeta - 0.0059 / safe + 0.9858)
    return np.maximum(0.0, eta * pdc)


def inverter_ac(pdc, inv, model):
    """pdc: Series daya DC (W) ke satu inverter. inv: dict dari config."""
    pac0 = inv["pac_w"]
    if model == "constant":
        raw = pdc * inv["eta_peak"]
    elif model in ("pvwatts_ds", "pvwatts_gen"):
        eta_nom = inv["eta_peak"] if model == "pvwatts_ds" else cfg.PVWATTS_GENERIC_ETA_NOM
        pdc0 = pac0 / eta_nom                      # rating DC supaya AC nominal = pac0
        raw = pd.Series(_pvwatts_unclipped(pdc.values, pdc0, eta_nom), index=pdc.index)
    else:
        raise ValueError(model)
    return raw.clip(upper=pac0), raw


def check_against_pvlib():
    """Uji: implementasi sendiri harus sama dengan pvlib.inverter.pvwatts."""
    inv = cfg.INVERTERS["INV50_A"]
    pdc = pd.Series(np.linspace(0, 60000, 61))
    mine, _ = inverter_ac(pdc, inv, "pvwatts_ds")
    ref = pvlib.inverter.pvwatts(pdc, inv["pac_w"] / inv["eta_peak"],
                                 eta_inv_nom=inv["eta_peak"], eta_inv_ref=ETA_REF)
    return float(np.abs(mine.values - ref.values).max())


def simulate_ac(dc_table, mapping, model):
    """
    dc_table: output pv_model.simulate_dc.  mapping: dict inverter -> [subarray].
    Return (ac_per_inverter, unclipped_per_inverter, dc_per_inverter) DataFrame (W).
    """
    ac, raw, dc = {}, {}, {}
    for inv_name, subs in mapping.items():
        pdc = sum(dc_table[f"DC_{s}"] for s in subs)
        a, r = inverter_ac(pdc, cfg.INVERTERS[inv_name], model)
        ac[inv_name], raw[inv_name], dc[inv_name] = a, r, pdc
    return pd.DataFrame(ac), pd.DataFrame(raw), pd.DataFrame(dc)
