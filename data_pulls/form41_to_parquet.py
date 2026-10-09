"""Turn the yearly DOT Form 41 downloads (data/f41_zips) into the single parquet files the pipeline reads."""
import os, glob, zipfile, tempfile, duckdb
DATA = os.environ.get("AIRFARE_DATA", os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data"))
NAMES = {"P52": "P52 Aircraft Operating Expenses by Type", "T2": "T2 Traffic Capacity by Aircraft Type", "P12": "P12 Income Statement", "P12A": "P12a Fuel"}
c = duckdb.connect()
for tag, name in NAMES.items():
    with tempfile.TemporaryDirectory() as tmp:
        csvs = []
        for zp in sorted(glob.glob(os.path.join(DATA, "f41_zips", f"{tag}_*.zip"))):
            z = zipfile.ZipFile(zp); n = [m for m in z.namelist() if m.startswith("T_")][0]
            out = os.path.join(tmp, os.path.basename(zp) + ".csv")
            with open(out, "wb") as fh: fh.write(z.read(n))
            csvs.append(out.replace("\\", "/"))
        lst = "[" + ",".join(f"'{p}'" for p in csvs) + "]"
        dst = os.path.join(DATA, f"Form41 {name} 2006-2026.parquet").replace("\\", "/")
        c.execute(f"COPY (SELECT * FROM read_csv_auto({lst}, union_by_name=true)) TO '{dst}' (FORMAT parquet, COMPRESSION zstd)")
        print(tag, "->", dst)
