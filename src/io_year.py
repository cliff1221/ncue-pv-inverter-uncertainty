"""Load/save the hourly 2023 dataset (CSV, timezone Asia/Taipei)."""
import pandas as pd, os
HERE = os.path.dirname(os.path.abspath(__file__))
PATH = os.path.join(HERE, "..", "data", "processed", "hourly_2023.csv")
def load_year(path=PATH):
    d = pd.read_csv(path, index_col=0)
    d.index = pd.to_datetime(d.index, utc=True).tz_convert("Asia/Taipei"); d.index.name = "t"
    return d
def save_year(d, path=PATH):
    d.to_csv(path, index_label="time", date_format="%Y-%m-%dT%H:%M:%S%z")
