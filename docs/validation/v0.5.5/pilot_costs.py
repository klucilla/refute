"""v0.5.5: a timed pilot of R1's unit costs, before the sizes and caps are frozen (#218; the
charter, process change 5, "the price before the freeze"). ``method_status: not_validated``.

On seeds of their own (``refute-v055-pilot-<set>:<family>:<i>``, never in any R1 set), it times:
- D1-P's unit: C1 version 2's curve and the locked battery's paired chain, for 2 EB1 and 2 EB2;
  then the three oracle fits on each binary, whatever its verdict;
- the bridge's unit: the same seeds with C1 version 1 and the paired chain;
- D2-F's unit: one P planet through ``d2f_floor.one`` (version 5, I4's bound, the sinusoid).
**It prints only each unit's status and CPU seconds**: no verdict, distance, power or count.
The pilot's own consumption is charged to v0.5.5's ledger.

Usage: ``.venv/Scripts/python.exe -B .cache/v054/tools/pin.py "import runpy;
runpy.run_path('docs/validation/v0.5.5/pilot_costs.py', run_name='__main__')"``
"""

from __future__ import annotations

import json
import sys
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import d2f_floor  # noqa: E402,I001  (it imports the earlier stages, then ledger_v055 last)
import d1p_price  # noqa: E402
import generator_v2 as g2  # noqa: E402
import r1_common as rc  # noqa: E402
import ledger_v055 as lv  # noqa: E402


def _cpu(fn):
    started = time.process_time()
    try:
        fn()
        status = "OK"
    except Exception as exc:  # noqa: BLE001 - the status only
        status = type(exc).__name__
    return status, time.process_time() - started


def main() -> None:
    from refute.packs.tess.calib05 import c1
    from refute.packs.tess.calib05.plans import pair
    from refute.packs.tess.calib05.steps import v04_test_plan
    from refute.packs.tess.discover.paired import paired_chain

    p04, p05 = pair(v04_test_plan(lv.ROOT))
    out = []
    begun = time.process_time()
    for family in ("EB1", "EB2"):
        for i in range(2):
            s = rc.seed("pilot", "A", family, i)
            box: dict = {}

            def v2(s=s, family=family, box=box):
                box["data"], box["truth"] = g2.generate(family, s)
                box["chain"] = paired_chain(box["data"], p04, p05, stage=2)

            st, cpu = _cpu(v2)
            out.append({"unit": f"d1p chain v2 {family}", "status": st, "cpu_seconds": cpu})
            if st == "OK" and box["chain"]["search_candidate"]:
                sc = box["chain"]["search_candidate"]
                found = {"period_days": sc["period_days"], "t0_btjd": sc["t0_btjd"]}

                def oracle(s=s, family=family, box=box, found=found):
                    d1p_price.distances(family, s, box["data"], box["truth"], found)

                st2, cpu2 = _cpu(oracle)
                out.append({"unit": f"d1p oracle {family}", "status": st2, "cpu_seconds": cpu2})

            def v1(s=s, family=family):
                data, _ = c1.generate(family, s)
                paired_chain(data, p04, p05, stage=2)

            st3, cpu3 = _cpu(v1)
            out.append({"unit": f"bridge chain v1 {family}", "status": st3, "cpu_seconds": cpu3})
    st4, cpu4 = _cpu(lambda: d2f_floor.one("pilot", 0))
    out.append({"unit": "d2f planet", "status": st4, "cpu_seconds": cpu4})
    used = time.process_time() - begun
    print(json.dumps(out, indent=1))
    print(f"pilot total {used:.1f} CPU-s")
    lv.bind()  # d1p_price imported d1_bound, which rebinds budgeted to stage B on import
    lv.declare()
    lv.charge(f"pilot_costs_{time.strftime('%Y%m%dT%H%M%SZ', time.gmtime())}", used / 3600.0,
              f"pilot_costs.py: process time {used:.1f} s")  # fmt: skip


if __name__ == "__main__":
    main()
