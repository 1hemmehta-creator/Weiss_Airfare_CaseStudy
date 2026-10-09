"""Combine the yearly / quarterly pulls into single zstd parquet files. Usage: combine_to_parquet.py t100 | Market | Ticket | Coupon"""
import os, sys, glob, re, zipfile, duckdb

DATA = os.environ.get("AIRFARE_DATA", os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data")); os.makedirs(DATA, exist_ok=True)
HERE = DATA; DL = DATA
TMP = os.path.join(HERE, "combine_tmp"); os.makedirs(TMP, exist_ok=True)
what = sys.argv[1]
con = duckdb.connect()
con.execute(f"SET threads=4; SET memory_limit='6GB'; SET temp_directory='{TMP.replace(chr(92), '/')}/spill'")
KEEP = "COLUMNS(c -> NOT regexp_matches(c, '^column[0-9]+$'))"

if what == "t100":
    csvs = []
    for zp in sorted(glob.glob(os.path.join(HERE, "t100_zips", "T100_SEGMENT_ALL_*.zip"))):
        y = re.search(r"(\d{4})\.zip$", zp).group(1)
        z = zipfile.ZipFile(zp); name = [m for m in z.namelist() if m.startswith("T_")][0]
        dst = os.path.join(TMP, f"t100_{y}.csv")
        with z.open(name) as src, open(dst, "wb") as out:
            while chunk := src.read(1 << 24):
                out.write(chunk)
        csvs.append(dst.replace("\\", "/"))
    lst = "[" + ",".join(f"'{c}'" for c in csvs) + "]"
    out = f"{DL}/T100_Segment_All_Carriers_2006-2026.parquet"
    con.execute(f"COPY (SELECT {KEEP} FROM read_csv({lst}, header=true, union_by_name=true, sample_size=-1) "
                f"ORDER BY YEAR, MONTH, UNIQUE_CARRIER, ORIGIN, DEST) TO '{out}' (FORMAT parquet, COMPRESSION zstd, COMPRESSION_LEVEL 9)")
    for c in csvs: os.remove(c)
    print(con.execute(f"SELECT YEAR, count(*) n_rows, count(DISTINCT MONTH) months, round(sum(PASSENGERS)/1e6,1) pax_m, "
                      f"round(sum(DEPARTURES_PERFORMED)/1e6,2) deps_m FROM '{out}' GROUP BY 1 ORDER BY 1").fetchall())
else:
    files = sorted(glob.glob(os.path.join(HERE, "db1b_q", f"{what}_*.parquet")),
                   key=lambda p: tuple(int(x) for x in re.findall(r"_(\d{4})_(\d)\.parquet$", p)[0]))
    lst = "[" + ",".join("'" + f.replace("\\", "/") + "'" for f in files) + "]"
    out = f"{DL}/DB1B_{what}_2006-2025.parquet"
    con.execute(f"COPY (SELECT {KEEP} FROM read_parquet({lst}, union_by_name=true)) "
                f"TO '{out}' (FORMAT parquet, COMPRESSION zstd, COMPRESSION_LEVEL 9, ROW_GROUP_SIZE 1000000)")
    print(len(files), "quarters", con.execute(f"SELECT Year, Quarter, count(*) FROM '{out}' GROUP BY 1,2 ORDER BY 1,2").fetchall())
print(out, f"{os.path.getsize(out)/1e6:,.0f}MB")
