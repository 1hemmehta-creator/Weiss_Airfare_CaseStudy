"""Pull DB1B Market/Ticket/Coupon quarterly zips from BTS PREZIP, one at a time,
convert each to a zstd parquet in scratch, delete the CSV/zip."""
import os, sys, time, zipfile, glob, requests, duckdb

DATA = os.environ.get("AIRFARE_DATA", os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data")); os.makedirs(DATA, exist_ok=True)
Q = os.path.join(DATA, "db1b_q"); os.makedirs(Q, exist_ok=True)
TMP = os.path.join(DATA, "db1b_tmp"); os.makedirs(TMP, exist_ok=True)
H = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/129.0 Safari/537.36"}
tables = sys.argv[1].split(",") if len(sys.argv) > 1 else ["Market", "Ticket", "Coupon"]
periods = [(int(p.split("_")[0]), int(p.split("_")[1])) for p in sys.argv[2].split(",")] if len(sys.argv) > 2 else \
          [(y, q) for y in range(2006, 2026) for q in range(1, 5) if (y, q) <= (2025, 2)]

con = duckdb.connect()
con.execute("SET threads=2; SET memory_limit='2GB'; SET preserve_insertion_order=false")

for t in tables:
    for y, q in periods:
        out = os.path.join(Q, f"{t}_{y}_{q}.parquet")
        if os.path.exists(out):
            print(t, y, q, "have", flush=True); continue
        url = f"https://transtats.bts.gov/PREZIP/Origin_and_Destination_Survey_DB1B{t}_{y}_{q}.zip"
        zp = os.path.join(TMP, f"{t}_{y}_{q}.zip")
        for attempt in range(5):
            try:
                with requests.get(url, headers=H, stream=True, timeout=300) as r:
                    r.raise_for_status()
                    with open(zp + ".part", "wb") as f:
                        for chunk in r.iter_content(1 << 20):
                            f.write(chunk)
                os.replace(zp + ".part", zp)
                z = zipfile.ZipFile(zp)
                csvname = [m for m in z.namelist() if m.lower().endswith(".csv")][0]
                z.extract(csvname, TMP); z.close()
                csvp = os.path.join(TMP, csvname).replace("\\", "/")
                try:
                    con.execute(f"COPY (SELECT * FROM read_csv('{csvp}', header=true, sample_size=-1)) "
                                f"TO '{out}.part' (FORMAT parquet, COMPRESSION zstd, COMPRESSION_LEVEL 9)")
                except duckdb.Error as e:
                    print(t, y, q, "typed read failed, all_varchar:", str(e)[:200], flush=True)
                    con.execute(f"COPY (SELECT * FROM read_csv('{csvp}', header=true, all_varchar=true)) "
                                f"TO '{out}.part' (FORMAT parquet, COMPRESSION zstd, COMPRESSION_LEVEL 9)")
                os.replace(out + ".part", out)
                n = con.execute(f"SELECT count(*) FROM '{out}'").fetchone()[0]
                if n == 0:
                    raise RuntimeError("zero rows")
                os.remove(csvp); os.remove(zp)
                print(t, y, q, "ok", f"{n:,} rows", f"{os.path.getsize(out)/1e6:.0f}MB", flush=True)
                break
            except Exception as e:
                print(t, y, q, "attempt", attempt, "failed:", str(e)[:300], flush=True)
                time.sleep(30 * (attempt + 1))
        else:
            print(t, y, q, "GAVE UP", flush=True)
print("DONE", flush=True)
