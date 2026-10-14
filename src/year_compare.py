"""Satu tahun 2023: ERA5 vs CODiS 467270 per jam + model pvlib dengan kedua sumber radiasi (suhu stasiun 467270 di semua varian)."""
import numpy as np, pandas as pd, pvlib
import config as cfg, weather as wx, inverter_model as im
Y = __import__("io_year").load_year(); IDX = Y.index; SITE = wx.make_location()
sp = SITE.get_solarposition(IDX); day = sp["zenith"] < 85
cs = SITE.get_clearsky(IDX)["ghi"]
D = pd.DataFrame({"codis": Y.ghi_codis, "era5": Y.ghi_era5, "z": sp["zenith"]})[day]
D = D[IDX[day] >= pd.Timestamp("2023-01-01 08:00", tz=cfg.SITE["tz"])]          # buang 8 jam ERA5 yang hilang
D["mon"] = D.index.month
kt = Y.ghi_codis.groupby(IDX.date).sum() / cs.groupby(IDX.date).sum(); D["kt"] = pd.Series(D.index.date, index=D.index).map(kt)
D["kls"] = pd.cut(D.kt, [0, 0.35, 0.65, 2], labels=["mendung (kt<0.35)", "sebagian (0.35-0.65)", "cerah (kt>0.65)"])
def st(x):
    d = x.era5 - x.codis; mu = x.codis.mean()
    return pd.Series(dict(n=len(x), codis_W=mu, era5_W=x.era5.mean(), MBE_W=d.mean(), MBE_pct=d.mean()/mu*100, RMSE_W=np.sqrt((d**2).mean()),
                          RMSE_pct=np.sqrt((d**2).mean())/mu*100, MAE_W=d.abs().mean(), r=x.era5.corr(x.codis)))
S = D.groupby("mon").apply(st); S.loc["all"] = st(D); K = D.groupby("kls", observed=True).apply(st)
pd.set_option("display.width", 200); print(S.round(2).to_string()); print(K.round(2).to_string())
S.to_csv("outputs/yr_era5_vs_codis_bulan.csv"); K.to_csv("outputs/yr_era5_vs_codis_kelas.csv"); D.to_csv("outputs/yr_era5_vs_codis_data.csv")
DOY = pd.Series(IDX.dayofyear, index=IDX); am = SITE.get_airmass(IDX, solar_position=sp)["airmass_relative"]
ex = pd.Series(np.asarray(pvlib.irradiance.get_extra_radiation(IDX)), index=IDX); SA = cfg.SUBARRAYS; ALB = 0.25; LOSS = 0.087
def chain(ghi, tair, dni=None, dhi=None, mapping="a", invm="pvwatts_ds", loss=LOSS):
    ghi = ghi.fillna(0).clip(lower=0)
    if dni is None:
        r = pvlib.irradiance.erbs(ghi, sp["zenith"], DOY); dni, dhi = r["dni"], r["dhi"]
    dni = pd.Series(np.asarray(dni, float), index=IDX).fillna(0).where(sp["zenith"] < 87, 0).clip(lower=0)
    dhi = pd.Series(np.asarray(dhi, float), index=IDX).fillna(0).clip(lower=0)
    poa = pvlib.irradiance.get_total_irradiance(23.0, 180.0, sp["apparent_zenith"], sp["azimuth"], dni, ghi, dhi, dni_extra=ex, airmass=am,
            albedo=ALB, model="perez")["poa_global"].fillna(0).clip(lower=0)
    tc = pvlib.temperature.ross(poa, tair, cfg.MODULE["noct_c"])
    pm = (pvlib.pvsystem.pvwatts_dc(poa, tc, cfg.MODULE["pmax_stc_w"], cfg.MODULE["gamma_pdc"], 25.0) * (1 - loss)).clip(lower=0)
    ac, clip, dc = 0.0, 0.0, 0.0
    for inv, subs in cfg.MAPPING_OPTIONS[mapping].items():
        pdc = pm * sum(SA[s]["n_modules"] for s in subs); a, r = im.inverter_ac(pdc, cfg.INVERTERS[inv], invm)
        ac = ac + a; clip = clip + (r - a); dc = dc + pdc
    return ac / 1000.0, dc / 1000.0, clip / 1000.0, poa
T = Y.T_codis; e_dni = (Y.gb_era5 / np.cos(np.radians(sp["zenith"])).clip(lower=0.05)).where(sp["zenith"] < 85, 0)
SRC = {"CODiS": dict(ghi=Y.ghi_codis, tair=T), "ERA5 (GHI)": dict(ghi=Y.ghi_era5, tair=T),
       "ERA5 (GHI, DNI, DHI)": dict(ghi=Y.ghi_era5, tair=T, dni=e_dni, dhi=Y.gd_era5)}
rows = []; daily = {}
for mp in ("a", "b"):
    for invm in im.MODELS:
        for nm, kw in SRC.items():
            ac, dc, clip, poa = chain(mapping=mp, invm=invm, **kw); daily[(mp, invm, nm)] = ac.resample("D").sum()
            for mo in list(range(1, 13)) + ["all"]:
                sel = (ac.index.month == mo) if mo != "all" else np.ones(len(ac), bool)
                rows.append(dict(mapping=mp, inverter=invm, sumber=nm, bulan=str(mo), E_AC_kWh=ac[sel].sum(), E_DC_kWh=dc[sel].sum(), clip_kWh=clip[sel].sum(),
                                 puncak_kW=ac[sel].max(), POA_kWhm2=poa[sel].sum() / 1000))
R = pd.DataFrame(rows)
base = R[(R.sumber == "CODiS")].set_index(["mapping", "inverter", "bulan"]).E_AC_kWh
R["sel_pct"] = [(r.E_AC_kWh / base[(r.mapping, r.inverter, r.bulan)] - 1) * 100 for r in R.itertuples()]
R.to_csv("outputs/yr_model_energi.csv", index=False)
v = R[(R.mapping == "a") & (R.inverter == "pvwatts_ds")]
print(v.pivot(index="sumber", columns="bulan", values="E_AC_kWh").round(0)[[str(i) for i in range(1, 13)] + ["all"]].to_string())
print(v.pivot(index="sumber", columns="bulan", values="sel_pct").round(1)[[str(i) for i in range(1, 13)] + ["all"]].to_string())
print(R[(R.sumber == "CODiS") & (R.bulan == "all")][["mapping", "inverter", "E_AC_kWh", "E_DC_kWh", "clip_kWh", "puncak_kW", "POA_kWhm2"]].round(1).to_string(index=False))
dd = pd.DataFrame({"codis": daily[("a", "pvwatts_ds", "CODiS")], "era5": daily[("a", "pvwatts_ds", "ERA5 (GHI)")]})
dd.to_csv("outputs/yr_model_harian_AC.csv")
print("harian AC: MBE %.1f%% RMSE %.1f%% r %.3f" % ((dd.era5 - dd.codis).mean() / dd.codis.mean() * 100, np.sqrt(((dd.era5 - dd.codis)**2).mean()) / dd.codis.mean() * 100, dd.era5.corr(dd.codis)))
print("yield tahunan CODiS (kWh/kWp):", R[(R.sumber=="CODiS")&(R.bulan=="all")&(R.mapping=="a")&(R.inverter=="pvwatts_ds")].E_AC_kWh.iloc[0] / 139.5)
