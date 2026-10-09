"""Pull any BTS TranStats table (DOT Form 41 schedules), all fields, one year per request, sequential.
Usage: python pull_bts_form41.py <table id> <name> [years]   e.g.  FMK P52   (see README for the table ids)"""
import re, sys, time, zipfile, io, os, requests

TID, NAME = sys.argv[1], sys.argv[2]
URL = f"https://www.transtats.bts.gov/DL_SelectFields.aspx?gnoyr_VQ={TID}&QO_fu146_anzr=Nv4%20Pn44vr4%20Sv0n0pvny"
DATA = os.environ.get("AIRFARE_DATA", os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data")); os.makedirs(DATA, exist_ok=True)
OUT = os.path.join(DATA, "f41_zips")
os.makedirs(OUT, exist_ok=True)
years = [int(y) for y in sys.argv[3:]] or list(range(2006, 2027))
H = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/129.0 Safari/537.36"}

def hidden(s, name):
    m = re.search(r'id="%s" value="([^"]*)"' % name, s)
    return m.group(1) if m else ""

for y in years:
    dest = os.path.join(OUT, f"{NAME}_{y}.zip")
    if os.path.exists(dest) and zipfile.is_zipfile(dest):
        print(y, "have", flush=True); continue
    for attempt in range(5):
        try:
            se = requests.Session(); se.headers.update(H)
            page = se.get(URL, timeout=120).text
            fields = re.findall(r'<input id="([A-Z_]+)" type="checkbox" name="\1"', page)
            data = {"__EVENTTARGET": "", "__EVENTARGUMENT": "", "__LASTFOCUS": "",
                    "__VIEWSTATE": hidden(page, "__VIEWSTATE"),
                    "__VIEWSTATEGENERATOR": hidden(page, "__VIEWSTATEGENERATOR"),
                    "__EVENTVALIDATION": hidden(page, "__EVENTVALIDATION"),
                    "txtSearch": "", "cboYear": str(y), "cboPeriod": "All",
                    "btnDownload": "Download", "chkAllVars": "on", "chkDownloadZip": "on"}
            if 'id="cboGeography"' in page: data["cboGeography"] = "All"
            if 'id="cboPeriod"' not in page: data.pop("cboPeriod")
            for f in fields:
                data[f] = "on"
            r = se.post(URL, data=data, timeout=1200)
            if r.content[:2] != b"PK":
                raise RuntimeError(f"not a zip: {r.status_code} {r.headers.get('content-type')} {r.content[:200]!r}")
            open(dest + ".part", "wb").write(r.content)
            os.replace(dest + ".part", dest)
            z = zipfile.ZipFile(dest)
            n = sum(1 for _ in io.TextIOWrapper(z.open([m for m in z.namelist() if m.startswith("T_")][0]), encoding="utf-8", errors="replace")) - 1
            print(y, "ok", len(r.content), "bytes", n, "rows", len(fields), "fields", flush=True)
            break
        except Exception as e:
            print(y, "attempt", attempt, "failed:", e, flush=True)
            time.sleep(30 * (attempt + 1))
    time.sleep(5)
print("DONE", flush=True)
