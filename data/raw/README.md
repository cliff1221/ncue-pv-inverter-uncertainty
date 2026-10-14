# Raw data (not included)

The raw files are not redistributed here. Download them yourself and put them in this folder
(or set `RAW_DIR`), then run `python src/year2023.py`.

1. **CODiS (Central Weather Administration, Taiwan)**, station 467270, year 2023, hourly tables.
   Download twelve monthly files of each variable from https://codis.cwa.gov.tw/ :
   - `*467270-2023-MM-GlobalSolarRadiation-hour.csv`
   - `*467270-2023-MM-AirTemperature-hour*.csv`
2. **PVGIS 5.3 (ERA5)** hourly time series for 24.066 N, 120.559 E, year 2023, with the
   radiation components and 2 m temperature, file name matching `*Timeseries_24.066_120.559_E5*`.
   https://re.jrc.ec.europa.eu/pvg_tools/

`data/processed/hourly_2023.csv` is the result of `src/year2023.py`, so steps 1-2 can be skipped
to reproduce the paper's results. It contains values derived from CODiS: check the CWA terms of
use before redistributing it.
