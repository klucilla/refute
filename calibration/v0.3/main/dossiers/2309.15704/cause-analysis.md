# 2309.15704: the analysis of the cause of the run's failure (a new record)

This record is step 5 of #162. It is a new record: the locked claims, the run, the sealed
dossier and the verdicts do not change. The verdicts are about the claims as Refute ran them,
never about their authors.

## State of the right of reply

- **Notice sent:** 2026-10-20T00:56Z, by the maintainer (#158).
- **Period ended:** 2026-11-18, in the maintainer's time zone (30 days, D-15).
- **Reply:** none received by the end of the period, by the maintainer's check of
  2026-11-20. No extension was asked for.

## What the run recorded (unchanged)

- **The verdict.** Three of three drawn claims are `INCONCLUSIVE`, with the engine's cause
  `undetermined`.
- **The dossier:** `dossier/`, with `MANIFEST.sha256`
  `3215fb9316d211717e672c731bfe3a655c9f3f7c719a43d831df8ada2e30fb4e` and sealed core
  `314ec1920c6fb593c4ecdb6b8582b891e0436d5fb522af265f7845b2541e7d3f`.
- **The command of each claim's base run,** as the repository's README gives it for the `*_all`
  configurations: `python run.py --config configs/uci_all.yml`.
- **The failure.** Each run ended at once, before any training:
  `TypeError: unsupported operand type(s) for +: 'NoneType' and 'str'`, at `run.py` line 152
  (`run = dataset + "_" + method`). The logs are `dossier/logs/arXiv-2309.15704v2-C{1,2,3}_base_method_s-.log`.

## The analysis (Refute's reading of the code; the authors did not comment)

Code read: `run.py` of <https://github.com/antoinedemathelin/maxwent-expe> at commit
`c67aa620a64e139d8599613e24cc57b34af5b67f`, the commit the claims lock (re-read on 2026-11-16).

1. `read_args` accepts the long option `--config`: it is in the `getopt` list (lines 58-59).
2. An option is kept only when its name without the dashes is a key of `args_dict_default`
   (line 95). That key is `configfile` (line 14), not `config`.
3. The short option `-c` is mapped to `configfile` through `abbrv_dict` (lines 44-45 and 92-93).
   The long option `--config` is not mapped.
4. So with `--config` the configuration file is not read (line 99 needs `configfile`), `dataset`
   and `method` keep their default `None`, and line 152 fails.
5. The README shows both forms: `python run.py --config configs/1d_reg_all.yml` for an `*_all`
   configuration, and `python run.py -c configs/uci.yml -d yacht_interpol -m MCDropout ...` for a
   single experiment.

## What this does and does not show

- **Shown:** at the tested commit, the long-option command that the README documents for the
  `*_all` configurations stops before any experiment, for the reason above.
- **Not shown:** anything about the paper's results. No claim ran.
- **Not run:** the short form `python run.py -c configs/uci_all.yml`. The plan was locked with the
  documented command, and a rerun outside the locked plan is not made.
- **The verdict stays `INCONCLUSIVE`.** Version 1 of the engine does not attribute a failure of
  this kind to either side, so the cause in the dossier stays `undetermined`. This analysis
  does not change it.

## What is published with this record

Held until the period ended, now attached unchanged to the dossier as annexes
(`../../ANNEX-RECORD.md`):
- `annexes/review-opus/`: the primary reviewer's report (SHA-256 `e2e16a80…e2f4`);
- `annexes/review-codex/`: the second reviewer's report (SHA-256 `c34c8724…2fd0`);
- `annexes/reply-body/`: the body of the notice sent to the authors (SHA-256 `750c99c9…995c`).

No address and no message identifier is published.
