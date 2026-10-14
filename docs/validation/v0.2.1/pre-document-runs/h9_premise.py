from refute.core.runner import run_processes
from refute.packs.tess import synthetic as s
from refute.packs.tess.ebcatalog import parse_catalog
from refute.packs.tess.params import TessTestPlan
from refute.packs.tess.pipeline import analyze_data

SCAN = {"format": "refute-eb-catalog-scan-1", "radius_arcsec": 120.0,
        "snapshots": [{"file": "x.tsv", "sha256": "0" * 64, "rows": 4584}],
        "per_target": {"TIC-1": {}}}
ROWS = {"planet": "TESS-EB,1,1,{ra},{dec},3.7", "blend": "TESS-EB,2,2,{ra},{dec2},2.3"}

def task(arg):
    name, seed = arg
    data = s.scenario_data(name, seed)
    row = ROWS[name].format(ra=s.TARGET_RA, dec=s.TARGET_DEC, dec2=s.TARGET_DEC + 5 / 3600)
    cat = parse_catalog("catalog,source_id,tic_id,ra_deg,dec_deg,period_days\n" + row + "\n")
    a = analyze_data(data, TessTestPlan.model_validate(s.fast_plan_dict()), catalogs=cat, catalog_scan=SCAN)
    fatal = [t.name for t in a.tests if t.status.value == "FAIL" and t.severity.value == "fatal"]
    return name, seed, data.target_key, round(a.gauntlet.candidate.period, 4), a.verdict, fatal

if __name__ == "__main__":
    for r in run_processes(task, [(n, k) for n in ROWS for k in range(5)], 10):
        print(r)
