"""
pv_model.py  -  dari cuaca sampai daya DC tiap sub-array.

Rantai:  posisi matahari -> irradiansi di bidang panel (POA, Perez)
         -> suhu sel (model NOCT/Ross, dari datasheet) -> daya DC.
"""
import numpy as np
import pandas as pd
import pvlib
import config as cfg
from weather import make_location


def simulate_dc(weather, dc_loss_fraction=None):
    """
    Return DataFrame daya DC (W) per sub-array + info POA dan suhu sel.
    Kolom: DC_<nama_subarray>, poa_<nama_subarray>, tcell_<nama_subarray>
    """
    loss = cfg.DC_LOSS_FRACTION if dc_loss_fraction is None else dc_loss_fraction
    site = make_location()
    times = weather.index

    solpos = site.get_solarposition(times)
    dni_extra = pvlib.irradiance.get_extra_radiation(times)
    airmass = site.get_airmass(times, solar_position=solpos)["airmass_relative"]

    out = pd.DataFrame(index=times)
    for name, sa in cfg.SUBARRAYS.items():
        poa = pvlib.irradiance.get_total_irradiance(
            surface_tilt=sa["tilt"], surface_azimuth=sa["azimuth"],
            solar_zenith=solpos["apparent_zenith"], solar_azimuth=solpos["azimuth"],
            dni=weather["dni"], ghi=weather["ghi"], dhi=weather["dhi"],
            dni_extra=dni_extra, airmass=airmass, albedo=cfg.ALBEDO, model="perez",
        )["poa_global"].fillna(0.0).clip(lower=0.0)

        tcell = pvlib.temperature.ross(
            poa_global=poa, temp_air=weather["temp_air"], noct=cfg.MODULE["noct_c"])

        pdc0 = cfg.MODULE["pmax_stc_w"] * sa["n_modules"]
        # argumen posisional: nama parameter pertama berbeda antar versi pvlib
        pdc = pvlib.pvsystem.pvwatts_dc(
            poa, tcell, pdc0, cfg.MODULE["gamma_pdc"], 25.0)
        pdc = (pdc * (1.0 - loss)).clip(lower=0.0)

        out[f"DC_{name}"] = pdc
        out[f"poa_{name}"] = poa
        out[f"tcell_{name}"] = tcell
    return out
