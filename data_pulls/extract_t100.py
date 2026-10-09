"""Extract each year's T-100 CSV into the data folder and print row / passenger checks."""
import os, zipfile, glob, re
import pandas as pd

DATA = os.environ.get("AIRFARE_DATA", os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data")); os.makedirs(DATA, exist_ok=True)
HERE = DATA; DL = DATA
for zp in sorted(glob.glob(os.path.join(HERE, "t100_zips", "T100_SEGMENT_ALL_*.zip"))):
    y = re.search(r"(\d{4})\.zip$", zp).group(1)
    z = zipfile.ZipFile(zp)
    name = [m for m in z.namelist() if m.startswith("T_")][0]
    df = pd.read_csv(z.open(name), low_memory=False)
    df = df.loc[:, ~df.columns.str.startswith("Unnamed")]
    if len(df) == 0:
        raise SystemExit(f"{y}: zero rows, refusing to write")
    dom = df[(df.ORIGIN_COUNTRY == "US") & (df.DEST_COUNTRY == "US")]
    months = sorted(df.MONTH.unique())
    out = os.path.join(DL, f"T100_Segment_All_Carriers_{y}.csv")
    df.to_csv(out, index=False)
    print(y, f"rows={len(df):,}", f"months={months[0]}-{months[-1]} ({len(months)})",
          f"pax={df.PASSENGERS.sum()/1e6:,.1f}m", f"US-domestic pax={dom.PASSENGERS.sum()/1e6:,.1f}m",
          f"deps={df.DEPARTURES_PERFORMED.sum()/1e6:,.2f}m", flush=True)
