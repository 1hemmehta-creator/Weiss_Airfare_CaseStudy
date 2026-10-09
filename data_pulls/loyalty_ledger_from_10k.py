"""Parse the airlines' 10-K loyalty disclosures (text pulled through CapRelay into data/tenk/) into data/loyalty_ledger.csv."""
import csv, re, os, sys

DATA = os.environ.get("AIRFARE_DATA", os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data")); os.makedirs(DATA, exist_ok=True)
T = os.path.join(DATA, "tenk")
OUT = os.path.join(DATA, "loyalty_ledger.csv")

SRC = {
 'ual_fy19': '10-K filed 2020-02-25', 'ual_fy20': '10-K filed 2021-03-01', 'ual_fy21': '10-K filed 2022-02-18',
 'ual_fy22': '10-K filed 2023-02-16', 'ual_fy23': '10-K filed 2024-02-29', 'ual_fy24': '10-K filed 2025-02-27',
 'ual_fy25': '10-K filed 2026-02-12',
 'dal19': '10-K filed 2020-02-13', 'dal_fy20': '10-K filed 2021-02-12', 'dal21': '10-K filed 2022-02-11',
 'dal_fy22': '10-K filed 2023-02-10', 'dal23': '10-K filed 2024-02-12', 'dal_fy24': '10-K filed 2025-02-11',
 'dal': '10-K filed 2026-02-11',
 'aal_fy19': '10-K filed 2020-02-19', 'aal_fy20': '10-K filed 2021-02-17', 'aal_fy21': '10-K filed 2022-02-22',
 'aal_fy22': '10-K filed 2023-02-22', 'aal_fy23': '10-K filed 2024-02-21', 'aal_fy24': '10-K filed 2025-02-19',
 'aal_fy25': '10-K filed 2026-02-18',
 'alk_fy19': '10-K filed 2020-02-12', 'alk_fy20': '10-K filed 2021-02-26', 'alk_fy22': '10-K filed 2023-02-13',
 'alk_fy23': '10-K filed 2024-02-14', 'alk_fy25': '10-K filed 2026-02-12',
 'luv_fy19': '10-K filed 2020-02-04', 'luv_fy20': '10-K filed 2021-02-08', 'luv_fy22': '10-K filed 2023-02-07',
 'luv_fy23': '10-K filed 2024-02-06', 'luv_fy25': '10-K filed 2026-02-05',
 'jblu_fy19': '10-K filed 2020-02-18', 'jblu_fy20': '10-K filed 2021-03-02', 'jblu_fy22': '10-K filed 2023-02-27',
 'jblu_fy23': '10-K filed 2024-02-12', 'jblu_fy25': '10-K filed 2026-02-12',
}
FY = {k: int('20' + re.search(r'(\d\d)$', k).group(1)) if re.search(r'fy\d\d$', k) else None for k in SRC}
FY.update({'dal19': 2019, 'dal21': 2021, 'dal23': 2023, 'dal': 2025})
AIR = {'ual': 'UAL', 'dal': 'DAL', 'aal': 'AAL', 'alk': 'ALK', 'luv': 'LUV', 'jbl': 'JBLU'}

cache = {}
def lines(f):
    if f not in cache:
        with open(os.path.join(T, f + '.txt'), encoding='utf-8') as fh:
            cache[f] = fh.read().split('\n')
    return cache[f]

def num(s):
    s = s.strip().replace('$', '').replace(',', '').replace('%', '').strip()
    neg = s.startswith('(') and s.endswith(')')
    s = s.strip('()').strip()
    v = float(s)
    v = -v if neg else v
    return int(v) if v == int(v) else v

rows = []
def air(f):
    return AIR[f[:3]]

def table(f, label, years, metric, unit='USD mm', anchor=None, label_out=None):
    """years: list matching the value columns (None = skip)."""
    L = lines(f)
    start = 0
    if anchor:
        start = next(i for i, l in enumerate(L) if anchor in l)
    hit = None
    for l in L[start:]:
        cells = l.split('\t')
        if cells[0].strip() == label:
            vv = [c for c in cells[1:] if c.strip() != '']
            if len(vv) != len(years) or any('%' in c for c in vv) and 'Percentage' not in label:
                continue
            hit = cells
            break
    if hit is None:
        sys.exit(f'MISSING {f} | {label}')
    vals = [c for c in hit[1:] if c.strip() != '']
    if len(vals) < len([y for y in years]):
        sys.exit(f'SHORT {f} | {label} | {vals}')
    for y, v in zip(years, vals):
        if y is None:
            continue
        rows.append([air(f), y, metric, num(v), unit, SRC[f], label_out or label])

def sent(f, pattern, items, label=None):
    """pattern: regex with groups; items: list of (group_index, year, metric, unit)."""
    txt = '\n'.join(lines(f))
    m = re.search(pattern, txt)
    if not m:
        sys.exit(f'NOSENT {f} | {pattern}')
    lab = label or m.group(0).strip()
    for g, y, metric, unit in items:
        v = m.group(g)
        rows.append([air(f), y, metric, num(v) if re.fullmatch(r'[\d.,$()]+', v) else v, unit, SRC[f], lab])

def text(f, pattern, year, metric):
    txt = '\n'.join(lines(f))
    m = re.search(pattern, txt)
    if not m:
        sys.exit(f'NOTEXT {f} | {pattern}')
    rows.append([air(f), year, metric, m.group(0).strip(), 'text', SRC[f], m.group(0).strip()])

# ---------------- UAL ----------------
RF = 'roll forward of Frequent flyer deferred revenue'
table('ual_fy19', 'Total Frequent flyer deferred revenue - beginning balance', [None, 2017], 'deferred_balance_eoy', anchor=RF,
      label_out='Total Frequent flyer deferred revenue - beginning balance (FY2018 opening = FY2017 year-end)')
for f, yrs in [('ual_fy19', [2019, 2018]), ('ual_fy20', [2020, None]), ('ual_fy22', [2022, 2021]), ('ual_fy23', [2023, None])]:
    table(f, 'Total Frequent flyer deferred revenue - ending balance', yrs, 'deferred_balance_eoy', anchor=RF)
    table(f, 'Total miles awarded', yrs, 'miles_awarded', anchor=RF)
    lab = 'Travel miles redeemed (Passenger revenue)' if f in ('ual_fy19', 'ual_fy20') else 'Travel miles redeemed'
    table(f, lab, yrs, 'travel_redeemed', anchor=RF)
    lab = 'Non-travel miles redeemed (Other operating revenue)' if f in ('ual_fy19', 'ual_fy20') else 'Non-travel miles redeemed'
    table(f, lab, yrs, 'nontravel_redeemed', anchor=RF)
table('ual_fy25', 'Balance at December 31', [2025, 2024], 'deferred_balance_eoy', anchor=RF)
table('ual_fy25', 'Miles earned', [2025, 2024], 'miles_awarded', anchor=RF)
table('ual_fy25', 'Travel miles redeemed', [2025, 2024], 'travel_redeemed', anchor=RF)
table('ual_fy25', 'Non-travel miles redeemed', [2025, 2024], 'nontravel_redeemed', anchor=RF)
# Other operating revenue from partner agreements ($ bn, as stated)
sent('ual_fy19', r'In the years ended December 31, 2019, 2018 and 2017, the Company recognized, in Other operating revenue, \$([\d.]+) billion, \$([\d.]+) billion \(including a one-time \$50 million payment\) and \$([\d.]+) billion, respectively, related to the marketing, advertising, non-travel miles redeemed \(net of related costs\) and other travel-related benefits of the mileage revenue',
     [(1, 2019, 'loyalty_other_revenue', 'USD bn'), (2, 2018, 'loyalty_other_revenue', 'USD bn'), (3, 2017, 'loyalty_other_revenue', 'USD bn')])
sent('ual_fy20', r'In the years ended December 31, 2020, 2019 and 2018, the Company recognized, in Other operating revenue, \$([\d.]+) billion,', [(1, 2020, 'loyalty_other_revenue', 'USD bn')],
     label='In the years ended December 31, 2020, 2019 and 2018, the Company recognized, in Other operating revenue, $1.7 billion ... related to the marketing, advertising, non-travel miles redeemed (net of related costs) and other travel-related benefits of the mileage revenue')
sent('ual_fy22', r'In the years ended December 31, 2022, 2021 and 2020, the Company recognized, in Other operating revenue, \$([\d.]+) billion, \$([\d.]+) billion', [(1, 2022, 'loyalty_other_revenue', 'USD bn'), (2, 2021, 'loyalty_other_revenue', 'USD bn')],
     label='In the years ended December 31, 2022, 2021 and 2020, the Company recognized, in Other operating revenue, $2.4 billion, $1.8 billion ... related to the marketing, advertising, non-travel miles redeemed (net of related costs) and other travel-related benefits of the mileage revenue')
sent('ual_fy23', r'In the years ended December 31, 2023, 2022 and 2021, the Company recognized, in Other operating revenue, \$([\d.]+) billion', [(1, 2023, 'loyalty_other_revenue', 'USD bn')],
     label='In the years ended December 31, 2023, 2022 and 2021, the Company recognized, in Other operating revenue, $2.7 billion ... related to the marketing, advertising, non-travel miles redeemed (net of related costs) and other travel-related benefits of the mileage revenue')
sent('ual_fy25', r'In the years ended December 31, 2025, 2024 and 2023, the Company recognized, in Other operating revenue, \$([\d.]+) billion, \$([\d.]+) billion', [(1, 2025, 'loyalty_other_revenue', 'USD bn'), (2, 2024, 'loyalty_other_revenue', 'USD bn')],
     label='In the years ended December 31, 2025, 2024 and 2023, the Company recognized, in Other operating revenue, $3.2 billion, $2.9 billion ... related to the marketing, advertising, non-travel miles redeemed (net of related costs) and other travel-related benefits of the mileage revenue')
for f, y in [('ual_fy19', 2019), ('ual_fy20', 2020), ('ual_fy21', 2021), ('ual_fy22', 2022), ('ual_fy23', 2023), ('ual_fy24', 2024), ('ual_fy25', 2025)]:
    sent(f, r'In %d, approximately ([\d.]+) million MileagePlus flight awards were used on United and United Express\. These awards represented (?:approximately )?([\d.]+)%% of United\'s total revenue passenger miles\.' % y,
         [(1, y, 'award_flights_used', 'million awards'), (2, y, 'award_pct_of_rpm', '%')])
    sent(f, r'MileagePlus members redeemed miles for approximately ([\d.]+) million other awards', [(1, y, 'nonflight_awards_redeemed', 'million awards')])
table('ual_fy19', 'Percentage of miles earned not expected to be redeemed', [2019], 'breakage_pct', unit='%')
table('ual_fy19', 'Impact of 1% change in outstanding miles expected to be redeemed or weighted average ticket value on deferred revenue (in millions)', [2019], 'breakage_sensitivity')
text('ual_fy25', r'The Company uses a statistical model to estimate the probability that an account will redeem its current miles balance and reviews its mileage breakage estimates annually\.', 2025, 'breakage_method')
text('ual_fy19', r'The Company uses a logit regression model to estimate the probability that an account will redeem its current miles balance\.', 2019, 'breakage_method')

# ---------------- DAL ----------------
RF = 'Balance at January 1'
table('dal19', 'Balance at January 1', [None, 2017], 'deferred_balance_eoy', label_out='Balance at January 1 (FY2018 opening = FY2017 year-end)')
table('dal19', 'Balance at December 31', [2019, 2018], 'deferred_balance_eoy', anchor='Miles earned')
table('dal19', 'Miles earned', [2019, 2018], 'miles_awarded')
table('dal19', 'Travel miles redeemed', [2019, 2018], 'travel_redeemed')
table('dal19', 'Non-travel miles redeemed', [2019, 2018], 'nontravel_redeemed')
for f, yrs in [('dal21', [2021, 2020, None]), ('dal23', [2023, 2022, None]), ('dal', [2025, 2024, None])]:
    table(f, 'Balance at December 31', yrs, 'deferred_balance_eoy', anchor='Loyalty program activity')
    table(f, 'Miles earned', yrs, 'miles_awarded', anchor='Loyalty program activity')
    table(f, 'Travel miles redeemed', yrs, 'travel_redeemed', anchor='Loyalty program activity')
    table(f, 'Non-travel miles redeemed', yrs, 'nontravel_redeemed', anchor='Loyalty program activity')
# loyalty program other revenue (Other revenue table, 3 columns)
table('dal19', 'Loyalty program', [2019, 2018, 2017], 'loyalty_other_revenue', anchor='(in millions)\t2019\t2018\t2017')
table('dal21', 'Loyalty program', [2021, 2020, None], 'loyalty_other_revenue', anchor='(in millions)\t2021\t2020\t2019')
table('dal23', 'Loyalty program', [2023, 2022, None], 'loyalty_other_revenue', anchor='(in millions)\t2023\t2022\t2021')
table('dal', 'Loyalty program', [2025, 2024, None], 'loyalty_other_revenue', anchor='(in millions)\t2025\t2024\t2023')
# cash sales from marketing agreements ($ bn)
sent('dal19', r'During the years ended December 31, 2019, 2018 and 2017, total cash sales from marketing agreements were \$([\d.]+) billion, \$([\d.]+) billion and \$([\d.]+) billion, respectively',
     [(1, 2019, 'cobrand_cash', 'USD bn'), (2, 2018, 'cobrand_cash', 'USD bn'), (3, 2017, 'cobrand_cash', 'USD bn')])
sent('dal21', r'During the years ended December 31, 2021, 2020 and 2019, total cash sales from marketing agreements related to our loyalty program were \$([\d.]+) billion, \$([\d.]+) billion and \$([\d.]+) billion, respectively',
     [(1, 2021, 'cobrand_cash', 'USD bn'), (2, 2020, 'cobrand_cash', 'USD bn')])
sent('dal23', r'During the years ended December 31, 2023, 2022 and 2021, total cash sales from marketing agreements related to our loyalty program were \$([\d.]+) billion, \$([\d.]+) billion and \$([\d.]+) billion, respectively',
     [(1, 2023, 'cobrand_cash', 'USD bn'), (2, 2022, 'cobrand_cash', 'USD bn')])
sent('dal', r'During the years ended December 31, 2025, 2024 and 2023, total cash sales from marketing agreements related to our loyalty program were \$([\d.]+) billion, \$([\d.]+) billion and \$([\d.]+) billion, respectively',
     [(1, 2025, 'cobrand_cash', 'USD bn'), (2, 2024, 'cobrand_cash', 'USD bn')])
sent('dal19', r'In 2019, cash sales from American Express totaled \$(\d+) billion', [(1, 2019, 'amex_remuneration', 'USD bn')])
sent('dal23', r'In 2023, remuneration from American Express totaled \$([\d.]+) billion', [(1, 2023, 'amex_remuneration', 'USD bn')])
sent('dal_fy24', r'In 2024, remuneration from American Express totaled \$([\d.]+) billion', [(1, 2024, 'amex_remuneration', 'USD bn')])
sent('dal', r'In 2025, remuneration from American Express totaled \$([\d.]+) billion', [(1, 2025, 'amex_remuneration', 'USD bn')])
sent('dal19', r'In 2019, ([\d.]+)% of revenue miles flown on Delta were from award travel, as program members redeemed miles in the loyalty program for (\d+) million award redemptions\.',
     [(1, 2019, 'award_pct_of_rpm', '%'), (2, 2019, 'award_tickets', 'million awards')])
sent('dal_fy20', r'In 2020 and 2019, nearly (\d+)% of revenue miles flown on Delta were from award travel, as program members redeemed miles in the loyalty program for approximately (\d+) million and 20 million award tickets, respectively\.',
     [(1, 2020, 'award_pct_of_rpm', '% (nearly)'), (2, 2020, 'award_tickets', 'million awards')])
for f, y in [('dal21', 2021), ('dal_fy22', 2022), ('dal23', 2023), ('dal_fy24', 2024), ('dal', 2025)]:
    sent(f, r'In %d, (\d+)%% of revenue miles flown on Delta were from award travel, as program members redeemed miles in the loyalty program for approximately (\d+) million award tickets\.' % y,
         [(1, y, 'award_pct_of_rpm', '%'), (2, y, 'award_tickets', 'million awards')])
text('dal', r'We use statistical models to estimate mileage breakage based on historical redemption patterns\.', 2025, 'breakage_method')

# ---------------- AAL ----------------
CB = 'Contract Balances'
table('aal_fy19', 'Loyalty program liability', [2019, 2018], 'deferred_balance_eoy', anchor=CB)
for f, y in [('aal_fy20', 2020), ('aal_fy21', 2021), ('aal_fy22', 2022), ('aal_fy23', 2023), ('aal_fy24', 2024), ('aal_fy25', 2025)]:
    table(f, 'Loyalty program liability', [y, None], 'deferred_balance_eoy', anchor=CB)
for f, y in [('aal_fy19', 2019), ('aal_fy20', 2020), ('aal_fy21', 2021), ('aal_fy22', 2022), ('aal_fy23', 2023), ('aal_fy24', 2024), ('aal_fy25', 2025)]:
    table(f, 'Deferral of revenue', [y], 'miles_awarded', anchor='Changes in loyalty program liability')
    L = lines(f)
    i = next(k for k, l in enumerate(L) if 'Changes in loyalty program liability' in l)
    rec = next(l for l in L[i:] if l.startswith('Recognition of revenue'))
    lab, v = rec.split('\t')[0], rec.split('\t')[1]
    rows.append(['AAL', y, 'total_redeemed_travel_and_nontravel', num(v), 'USD mm', SRC[f], lab.strip()])
# loyalty revenue lines (3-yr tables)
for f, yrs in [('aal_fy19', [2019, 2018, 2017]), ('aal_fy21', [2021, 2020, None]), ('aal_fy23', [2023, 2022, None]), ('aal_fy25', [2025, 2024, None])]:
    L = lines(f)
    trav = next(l for l in L if l.startswith('Loyalty revenue - travel'))
    mkt = next(l for l in L if l.startswith('Loyalty revenue - marketing services'))
    for line, metric in [(trav, 'loyalty_revenue_travel_passenger'), (mkt, 'loyalty_other_revenue')]:
        cells = line.split('\t')
        for y, v in zip(yrs, cells[1:]):
            if y:
                rows.append(['AAL', y, metric, num(v), 'USD mm', SRC[f], cells[0].strip()])
sent('aal_fy21', r'During the years ended December 31, 2021, 2020 and 2019, cash payments from co-branded credit card and other partners were \$([\d.]+) billion, \$([\d.]+) billion and \$([\d.]+) billion, respectively\.',
     [(1, 2021, 'cobrand_cash', 'USD bn'), (2, 2020, 'cobrand_cash', 'USD bn'), (3, 2019, 'cobrand_cash', 'USD bn')])
sent('aal_fy23', r'During 2023 and 2022, cash payments from co-branded credit card and other partners were \$([\d.]+) billion and \$([\d.]+) billion, respectively\.',
     [(1, 2023, 'cobrand_cash', 'USD bn'), (2, 2022, 'cobrand_cash', 'USD bn')])
sent('aal_fy25', r'During 2025 and 2024, cash payments from co-branded credit card and other partners were \$([\d.]+) billion and \$([\d.]+) billion, respectively\.',
     [(1, 2025, 'cobrand_cash', 'USD bn'), (2, 2024, 'cobrand_cash', 'USD bn')])
for f, y in [('aal_fy19', 2019), ('aal_fy20', 2020), ('aal_fy21', 2021), ('aal_fy22', 2022), ('aal_fy23', 2023), ('aal_fy24', 2024), ('aal_fy25', 2025)]:
    sent(f, r'During %d, our members redeemed approximately (\d+) million awards, including travel redemptions[^.]*\. Approximately (\d+)%% of our %d total revenue passenger miles flown were from award travel\.' % (y, y),
         [(1, y, 'awards_redeemed_all_types', 'million awards'), (2, y, 'award_pct_of_rpm', '%')])
    sent(f, r'For the year ended December 31, %d, a hypothetical 10%% increase in our estimate of (?:miles|mileage credits) not expected to be redeemed would have increased revenues by approximately \$(\d+) million\.' % y,
         [(1, y, 'breakage_sensitivity_10pct', 'USD mm')])

# ---------------- ALK ----------------
RF = 'roll forward of the total'
table('alk_fy19', 'Total Deferred Revenue balance at January 1', [None, 2017], 'deferred_balance_eoy', anchor=RF,
      label_out='Total Deferred Revenue balance at January 1 (FY2018 opening = FY2017 year-end)')
for f, yrs in [('alk_fy19', [2019, 2018]), ('alk_fy20', [2020, None]), ('alk_fy22', [2022, 2021]), ('alk_fy23', [2023, None])]:
    table(f, 'Total Deferred Revenue balance at December 31', yrs, 'deferred_balance_eoy', anchor=RF)
    table(f, 'Increase in liability for mileage credits issued', yrs, 'miles_awarded', anchor=RF)
    table(f, 'Travel miles and companion certificate redemption - Passenger revenue', yrs, 'travel_redeemed', anchor=RF)
    table(f, 'Miles redeemed on partner airlines - Other revenue', yrs, 'nontravel_redeemed', anchor=RF)
f = 'alk_fy25'
table(f, 'Total Deferred Revenue balance at December 31', [2025, 2024], 'deferred_balance_eoy', anchor=RF)
table(f, 'Increase in liability for loyalty points issued', [2025, 2024], 'miles_awarded', anchor=RF)
table(f, 'Loyalty points and companion certificate redemption - Passenger revenue', [2025, 2024], 'travel_redeemed', anchor=RF)
table(f, 'Loyalty points redeemed on partner airlines - Loyalty program other revenue', [2025, 2024], 'nontravel_redeemed', anchor=RF)
table(f, 'Deferred revenue acquired from Hawaiian as of September 18, 2024', [None, 2024], 'acquired_balance', anchor=RF)
for f, yrs, p, o in [('alk_fy19', [2019, 2018, 2017], 'Passenger revenue', 'Mileage Plan other revenue'),
                     ('alk_fy20', [2020, None, None], 'Passenger revenue', 'Mileage Plan other revenue'),
                     ('alk_fy22', [2022, 2021, None], 'Passenger revenue', 'Mileage Plan other revenue'),
                     ('alk_fy23', [2023, None, None], 'Passenger revenue', 'Mileage Plan other revenue'),
                     ('alk_fy25', [2025, 2024, None], 'Loyalty program passenger revenue', 'Loyalty program other revenue')]:
    anc = 'revenue included in the consolidated statements of operations'
    table(f, p, yrs, 'loyalty_revenue_travel_passenger', anchor=anc, label_out=p if f == 'alk_fy25' else 'Passenger revenue (Mileage Plan revenue table)')
    table(f, o, yrs, 'loyalty_other_revenue', anchor=anc)
for f, y in [('alk_fy19', 2019), ('alk_fy20', 2020), ('alk_fy22', 2022), ('alk_fy23', 2023)]:
    sent(f, r'At December 31, %d, we had approximately (\d+) billion miles outstanding' % y, [(1, y, 'miles_outstanding', 'billion miles')])
sent('alk_fy25', r'At December 31, 2025, Atmos Rewards program had approximately (\d+) billion points outstanding', [(1, 2025, 'miles_outstanding', 'billion points')])
sent('alk_fy22', r'Increased remuneration from our co-branded credit card provided \$(\d+) million in incremental cash as compared to 2021', [(1, 2022, 'cobrand_cash_yoy_increase', 'USD mm')])
for f, y in [('alk_fy22', 2022), ('alk_fy23', 2023)]:
    sent(f, r'A hypothetical 1% change in the amount of outstanding miles estimated to be redeemed would result in an approximately \$(\d+) million impact on annual revenue recognized\.', [(1, y, 'breakage_sensitivity_1pct', 'USD mm')])
sent('alk_fy25', r'A hypothetical 1% change in the amount of outstanding points estimated to be redeemed would result in an approximately \$(\d+) million impact on annual revenue recognized\.', [(1, 2025, 'breakage_sensitivity_1pct', 'USD mm')])
text('alk_fy22', r'In 2022, the Company updated its breakage methodology in conjunction with the elimination of mileage expiry, and now recognizes breakage proportionally as mileage credits are redeemed\.', 2022, 'breakage_method')

# ---------------- LUV ----------------
RF = 'Air traffic liability - loyalty program - beginning balance'
table('luv_fy19', RF, [None, 2017], 'deferred_balance_eoy', label_out=RF + ' (FY2018 opening = FY2017 year-end)')
for f, yrs in [('luv_fy19', [2019, 2018]), ('luv_fy20', [2020, None]), ('luv_fy22', [2022, 2021]), ('luv_fy23', [2023, None]), ('luv_fy25', [2025, 2024])]:
    table(f, 'Air traffic liability - loyalty program - ending balance', yrs, 'deferred_balance_eoy')
    table(f, 'Amounts deferred associated with points awarded', yrs, 'miles_awarded')
    table(f, 'Revenue recognized from points redeemed - Passenger', yrs, 'travel_redeemed')
    table(f, 'Revenue recognized from points redeemed - Other', yrs, 'nontravel_redeemed')
table('luv_fy20', 'Unused funds converted to loyalty points', [2020, None], 'other_rollforward_item')
for f, yrs in [('luv_fy19', [2019, 2018, 2017]), ('luv_fy22', [2022, 2021, 2020]), ('luv_fy25', [2025, 2024, 2023])]:
    table(f, 'Passenger loyalty - air transportation', yrs, 'loyalty_revenue_travel_passenger')
    table(f, 'Other', yrs, 'other_revenue_mainly_cobrand_royalties', anchor='Passenger\t$')
sent('luv_fy19', r'For 2019, Customers of Southwest redeemed approximately ([\d.]+) million flight awards, accounting for approximately ([\d.]+) percent of revenue passenger miles flown\. For 2018, Customers of Southwest redeemed approximately ([\d.]+) million flight awards, accounting for approximately ([\d.]+) percent of revenue passenger miles flown\. For 2017, Customers of Southwest redeemed approximately ([\d.]+) million flight awards, accounting for approximately ([\d.]+) percent',
     [(1, 2019, 'award_flights_used', 'million awards'), (2, 2019, 'award_pct_of_rpm', '%'), (3, 2018, 'award_flights_used', 'million awards'), (4, 2018, 'award_pct_of_rpm', '%'), (5, 2017, 'award_flights_used', 'million awards'), (6, 2017, 'award_pct_of_rpm', '%')],
     label='Customers of Southwest redeemed approximately [x] million flight awards, accounting for approximately [y] percent of revenue passenger miles flown')
sent('luv_fy22', r'For 2022, Customers of Southwest redeemed approximately ([\d.]+) million flight awards, accounting for approximately ([\d.]+) percent of revenue passenger miles flown\. For 2021, Customers of Southwest redeemed approximately ([\d.]+) million flight awards, accounting for approximately ([\d.]+) percent of revenue passenger miles flown\. For 2020, Customers of Southwest redeemed approximately ([\d.]+) million flight awards, accounting for approximately ([\d.]+) percent',
     [(1, 2022, 'award_flights_used', 'million awards'), (2, 2022, 'award_pct_of_rpm', '%'), (3, 2021, 'award_flights_used', 'million awards'), (4, 2021, 'award_pct_of_rpm', '%'), (5, 2020, 'award_flights_used', 'million awards'), (6, 2020, 'award_pct_of_rpm', '%')],
     label='Customers of Southwest redeemed approximately [x] million flight awards, accounting for approximately [y] percent of revenue passenger miles flown')
table('luv_fy25', 'Flight awards redeemed (millions)', [2025, 2024, 2023], 'award_flights_used', unit='million awards')
sent('luv_fy25', r'For 2025, 2024, and 2023, Customer redemption of flight awards accounted for approximately ([\d.]+) percent, ([\d.]+) percent, and ([\d.]+) percent of revenue passenger miles flown, respectively\.',
     [(1, 2025, 'award_pct_of_rpm', '%'), (2, 2024, 'award_pct_of_rpm', '%'), (3, 2023, 'award_pct_of_rpm', '%')])
for f, y, w in [('luv_fy19', 2019, 'spoilage'), ('luv_fy20', 2020, 'spoilage'), ('luv_fy22', 2022, 'breakage'), ('luv_fy23', 2023, 'breakage'), ('luv_fy25', 2025, 'breakage')]:
    sent(f, r'For the year ended December 31, %d, based on actual redemptions of points sold to business partners and earned through flights, a hypothetical one percentage point change in the estimated %s rate would have resulted in a change to Passenger revenue of approximately \$(\d+) million' % (y, w),
         [(1, y, 'breakage_sensitivity_1pt', 'USD mm')])
text('luv_fy22', r'The Company updates this model at least annually, and applies the new breakage rates effective October 1st each year, or more frequently if required by changes in the business\.', 2022, 'breakage_method')

# ---------------- JBLU ----------------
J = 'activit'
L = lines('jblu_fy19')
for f, spec in [('jblu_fy19', [(2017, 'x'), (2018, 'Balance at December 31, 2018'), (2019, 'Balance at December 31, 2019')]),
                ('jblu_fy20', [(2020, 'Balance at December 31, 2020')]),
                ('jblu_fy22', [(2021, 'Balance at December 31, 2021'), (2022, 'Balance at December 31, 2022')]),
                ('jblu_fy23', [(2023, 'Balance at December 31, 2023')]),
                ('jblu_fy25', [(2024, 'Balance at December 31, 2024'), (2025, 'Balance at December 31, 2025')])]:
    L = lines(f)
    i = next(k for k, l in enumerate(L) if 'air traffic liability for our loyalty program' in l)
    seg = []
    for l in L[i + 1:]:
        if l.startswith('```') and seg:
            break
        if '\t' in l:
            seg.append(l)
    # walk segments: rows between previous balance and this balance belong to this year
    cur = None
    for l in seg:
        lab, v = l.split('\t')[0].strip(), l.split('\t')[1]
        if lab.startswith('Balance at December 31, '):
            cur = int(lab[-4:]) + 1
            yb = int(lab[-4:])
            if yb in [s[0] for s in spec]:
                rows.append(['JBLU', yb, 'deferred_balance_eoy', num(v), 'USD mm', SRC[f], lab])
            continue
        if cur in [s[0] for s in spec]:
            m = {'TrueBlue® points earned and sold': 'miles_awarded', 'TrueBlue ® points earned and sold': 'miles_awarded',
                 'TrueBlue® points redeemed': 'travel_redeemed', 'TrueBlue ® points redeemed': 'travel_redeemed',
                 'TrueBlue® points redeemed passenger': 'travel_redeemed', 'TrueBlue® points redeemed other': 'nontravel_redeemed'}[lab]
            rows.append(['JBLU', cur, m, num(v), 'USD mm', SRC[f], lab])
for f, yrs in [('jblu_fy19', [2019, 2018, 2017]), ('jblu_fy22', [2022, 2021, 2020]), ('jblu_fy25', [2025, 2024, 2023])]:
    table(f, 'Loyalty revenue - air transportation', yrs, 'loyalty_revenue_travel_passenger')
    table(f, 'Loyalty revenue', yrs, 'loyalty_other_revenue')
sent('jblu_fy19', r'Nearly (\d+) million TrueBlue ® one-way redemption awards were flown during 2019, representing approximately (\d+)% of our total revenue passenger miles\.',
     [(1, 2019, 'award_flights_used', 'million awards (nearly)'), (2, 2019, 'award_pct_of_rpm', '%')])
text('jblu_fy25', r'Breakage is estimated using historical redemption patterns to determine a breakage rate\.', 2025, 'breakage_method')

# ---------------- write ----------------
# de-dup (airline, fy, metric) keeping first
seen = set(); out = []
for r in rows:
    k = (r[0], r[1], r[2])
    if k in seen:
        continue
    seen.add(k); out.append(r)
out.sort(key=lambda r: (r[0], r[1], r[2]))
os.makedirs(os.path.dirname(OUT), exist_ok=True)
with open(OUT, 'w', newline='', encoding='utf-8') as fh:
    w = csv.writer(fh)
    w.writerow(['airline', 'fiscal_year', 'metric', 'value', 'unit', 'source_filing', 'verbatim_label'])
    w.writerows(out)
print(len(out), 'rows; dupes dropped', len(rows) - len(out))
