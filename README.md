# Inverter model uncertainty budget, NCUE rooftop PV plant (pvlib)

Code and processed data for the CSME 2026 paper
"How Much Does the Inverter Model Matter? An Uncertainty Budget for a 139.5 kWp Multi-Inverter
Rooftop PV Plant from Datasheets and Public Weather Data".
[[Add DOI / citation after release]]

**Important:** no measured plant output is used. The results describe model uncertainty, not model accuracy.

## Plant and model
- 372 AJP-S672-375 modules (139.5 kWp), tilt 23 deg, azimuth south, 24.066 N, 120.559 E (all parameters in `src/config.py`).
- 1x30 kW and 2x50 kW inverters. The sub-array to inverter mapping is unconfirmed, so two scenarios (a, b) are run.
- pvlib chain: solar position -> Erbs -> Perez -> Ross cell temperature -> PVWatts DC (8.7 % DC loss) -> inverter -> sum of three inverters.
- Weather year 2023: CODiS station 467270 and PVGIS-ERA5.

## Setup
Tested with Python 3.13.
```
pip install -r requirements.txt
```

## Reproduce
Run everything from the repository root.
```
# 0. (optional) rebuild data/processed/hourly_2023.csv from the raw files in data/raw
python src/year2023.py

# 1. ERA5 vs station comparison, model energy, baseline, clipping, per-inverter (about 1 min)
python src/year_baseline.py          # also runs src/year_compare.py

# 2. Sensitivity: one-at-a-time + Sobol (SALib, N=1024, 11,264 runs; takes long, run in the background)
OUTP=yr05 GHI_ERR=0.05 python src/run_sens_year.py
OUTP=yr10 GHI_ERR=0.10 python src/run_sens_year.py

# 3. Figures
python src/make_figs_year.py
python src/make_figs_sens_year.py
python src/fig_flow.py
```
Results are written to `outputs/`, figures to `paper_figs/`. The shipped `outputs/` are the values used in the paper;
steps 1 reproduces them to about 1e-11 (floating-point noise).

## Files
| Path | Content |
|---|---|
| `src/config.py` | all plant parameters, DC loss, mapping scenarios |
| `src/weather.py`, `src/cwa_month.py` | location, CODiS table reader |
| `src/pv_model.py`, `src/inverter_model.py` | DC chain; inverter formulations (checked against `pvlib.inverter.pvwatts`) |
| `src/year2023.py`, `src/io_year.py` | builds the hourly 2023 dataset |
| `src/year_compare.py`, `src/year_baseline.py` | comparison, baseline, clipping |
| `src/sens_year.py`, `src/run_sens_year.py` | sensitivity analysis |
| `data/processed/hourly_2023.csv` | hourly GHI (station, ERA5), Gb, Gd (ERA5), air temperature; time = mid-hour, Asia/Taipei |
| `outputs/` | result tables (`yr_*.csv`, `yr05_*`, `yr10_*`) |

## Limitations
No validation against measured power; GHI error ranges (+-5 %, +-10 %) are assumptions; one year, one station, one ERA5 cell, hourly resolution;
the inverter uses the datasheet peak efficiency only. Station 467270 is not at the plant site.

## License
Code: MIT (see `LICENSE`). Weather data remain under the terms of CWA (CODiS) and the European Commission JRC (PVGIS).
