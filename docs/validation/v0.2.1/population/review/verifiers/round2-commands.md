# Phase G, second review (harness 33e2d4186ea4..., branch commit a83e09a): commands

Working folder `C:\Projetos\refute\.cache\review-g\r2\`. Variables as in
`round1-commands.md`, with `W` the population folder of the branch worktree:

```bash
R=/c/Projetos/refute
W=$R/.claude/worktrees/v0-2-1-gauntlet-fixes-13f5e7/docs/validation/v0.2.1/population
H=$W/population.py
P0=$R/.worktrees/v0.2.0/.venv/Scripts/python.exe
P3=$R/.worktrees/M3-9d3f369/.venv/Scripts/python.exe
```

## Self-test 3 folder

```bash
cd $W/selftest-3 && sha256sum -c SHA256SUMS      # 567 OK, and the file list equals the folder
```

## N1 and determinism (output: outputs-round2/generate-checks.log, check-*.json)

```bash
OPENBLAS_NUM_THREADS=2 OMP_NUM_THREADS=4 $P0 $H generate --population selftest --cache r2/nostore --no-store --check $W/selftest-2/manifest.json --check-report r2/check-s2-w1.json --workers 1
$P0 $H generate --population selftest --cache r2/nostore --no-store --check $W/selftest-2/manifest.json --check-report r2/check-s2-w3.json --workers 3 --order reverse
$P0 $H generate --population selftest --cache r2/nostore --no-store --check $W/selftest-3/manifest.json --check-report r2/check-s3-w24.json --workers 24 --order shuffle:99
```

## Cache and six-case manifest

```bash
# manifest-6.json: the six cases of round 1, taken from selftest-3/manifest.json (same one-liner as round 1)
$P0 $H generate --population selftest --cache cache --cases-from cases-8.txt --check $W/selftest-3/manifest.json --check-report check-cache.json --workers 4
```

## Interruption by PID (PowerShell, output: outputs-round2/kill-1.out, resume-and-m3.log)

```powershell
$a = @($H, 'analyze', '--manifest', "$G\manifest-6.json", '--cache', "$G\cache", '--out', "$G\runs\M0", '--point', 'M0', '--workers', '2')
$p = Start-Process -FilePath $p0 -ArgumentList $a -RedirectStandardOutput "$G\kill-1.out" -RedirectStandardError "$G\kill-1.err" -PassThru -NoNewWindow
# poll until runs\M0\cases has 2 results, then
taskkill /PID $p.Id /T /F        # PID 17324 and its two workers
```

```bash
sha256sum runs/M0/cases/*.json > snap-after-kill.txt
$P0 $H analyze --manifest manifest-6.json --cache cache --out runs/M0 --point M0 --workers 2
sha256sum -c snap-after-kill.txt
$P3 $H analyze --manifest manifest-6.json --cache cache --out runs/M3 --point M3 --workers 1
```

## Negative scenarios

`round2-negatives.sh` (output: `outputs-round2/negatives.log`).

## In-worker infrastructure stop (PowerShell, output: outputs-round2/race.out, neg-h-and-metrics.log)

```powershell
Copy-Item "$G\cache\*.rpc" "$G\neg\racecache\"
$a = @($H, 'analyze', '--manifest', "$G\manifest-6.json", '--cache', "$G\neg\racecache", '--out', "$G\neg\race", '--point', 'M0', '--workers', '1')
$p = Start-Process ... -PassThru -NoNewWindow
# after the first result: remove the input of the last case of the manifest order
Remove-Item -LiteralPath "$G\neg\racecache\planet-near-white-0005.rpc"
```

```bash
$P0 $H metrics --manifest manifest-6.json --runs neg/race --out neg/out/h-before.json
cp cache/planet-near-white-0005.rpc neg/racecache/
$P0 $H analyze --manifest manifest-6.json --cache neg/racecache --out neg/race --point M0 --workers 1
$P0 $H metrics --manifest manifest-6.json --runs neg/race runs/M3 --out neg/out/h-after.json
$P0 $H metrics --manifest manifest-6.json --runs runs/M0 runs/M3 --out out/m-base.json
```

## Kept verifiers against the new harness (output: outputs-round2/*_check.txt)

```bash
$P0 keep/snr_check.py $W/selftest-3/manifest.json <the 8 ids of round 1>
$P0 keep/ser_check.py $W/selftest-3/manifest.json r2/cache/planet-measurable-white-0000.rpc r2/cache/false_positive-measurable-white-0004.rpc r2/cache/no_transit-none-correlated-0004.rpc
$P0 keep/stats_check.py $H
$P0 keep/seed_check.py $H
$P0 keep/compare_outcomes.py $W/selftest-2/runs $W/selftest-3/runs M0-f479823=M0-f479823 M1-3217db7=M1-3217db7 M2-78d79f5=M2-78d79f5 M3-9d3f369=M3-9d3f369
$P0 keep/compare_outcomes.py $W/selftest-3/runs r2/runs M0-f479823=M0 M3-9d3f369=M3
```

Not run (rules of this review): `orchestrate` beyond its two refusals, because it now
requires `--project` to be the top of the harness's repository, so its cache would be the
branch worktree's `.cache/population/`, outside `.cache/review-g/`; and the dirty-`src/`
refusals, which need an edit in a point's worktree.
