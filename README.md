# U.S. Airline Data Pulls, 2006–2025

The data workflows behind a case study on how long-run U.S. airline fares are set. Everything here is public U.S. government data and airline filings, pulled and assembled into analysis-ready parquet files.

## Data sources

| Source | What | Script |
|---|---|---|
| BTS T-100 Segment, all carriers | Every flight segment by carrier, route, aircraft type and month: departures, seats, passengers, air time | `data_pulls/pull_t100.py`, `extract_t100.py`, `combine_to_parquet.py t100` |
| BTS DB1B (Market, Coupon, Ticket) | 10% sample of all domestic tickets: fare, route, fare class, operating and ticketing carrier | `data_pulls/pull_db1b.py`, `combine_to_parquet.py Market` |
| DOT Form 41 | Income statement (P-1.2), expenses by object (P-6), aircraft operating cost by type (P-5.2), traffic by type (T2), fuel (P-12a), balance sheet (B-1), small carriers (P-1.1) | `data_pulls/pull_bts_form41.py`, `form41_to_parquet.py` |
| Airline 10-Ks | Loyalty liability roll-forward, miles issued and redeemed, co-brand cash, award share | Filing text via CapRelay, parsed by `data_pulls/loyalty_ledger_from_10k.py` |
| BLS CPI-U | Annual average, 2006–2025 | `reference/cpi_annual.csv` |
| Seat maps | Seat counts by cabin and seat pitch / width for the top 200 aircraft configurations | `reference/Cabin Layouts Top200.xlsx`, `reference/seat_dims.csv` (source link on every row) |

BTS TranStats table ids for `pull_bts_form41.py`:

| Schedule | Table id |
|---|---|
| P-1.2 | `FMI` |
| P-6 | `FME` |
| P-5.2 | `FMK` |
| T2 | `FIH` |
| P-12(a) | `FMH` |
| B-1 | `FKM` |
| P-1.1 | `FMD` |

## Running it

Requirements: Python 3.12 and `pip install -r requirements.txt`.

Data lands in `data/`, about 15 GB in all. Set the `AIRFARE_DATA` environment variable to put it somewhere else.

```
python data_pulls/pull_t100.py
python data_pulls/extract_t100.py
python data_pulls/combine_to_parquet.py t100
python data_pulls/pull_db1b.py
python data_pulls/combine_to_parquet.py Market
python data_pulls/pull_bts_form41.py FMI P12
python data_pulls/pull_bts_form41.py FME P6
python data_pulls/pull_bts_form41.py FMK P52
python data_pulls/pull_bts_form41.py FIH T2
python data_pulls/pull_bts_form41.py FMH P12A
python data_pulls/pull_bts_form41.py FKM B1
python data_pulls/pull_bts_form41.py FMD P11
python data_pulls/form41_to_parquet.py
python data_pulls/loyalty_ledger_from_10k.py
```

The pulls run one request at a time, by design, to stay polite to the BTS servers.

## Layout

```
data_pulls/   downloaders and parsers for the public datasets
reference/    small reference data (CPI, seat maps, aircraft type codes)
```
