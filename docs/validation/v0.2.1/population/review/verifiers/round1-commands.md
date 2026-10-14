# Phase G, first review (harness 376bd7f9e33f..., commit 6e57b35): commands

Reconstructed verbatim from the reviewer's session history on 2026-10-12. The working
folder was `C:\Projetos\refute\.cache\review-g\` (deleted at the end of that review, by
the maintainer's instruction). Variables used in the bash commands:

```bash
R=/c/Projetos/refute
H=$R/.claude/worktrees/v0-2-1-gauntlet-fixes-13f5e7/docs/validation/v0.2.1/population/population.py
P0=$R/.worktrees/v0.2.0/.venv/Scripts/python.exe
P3=$R/.worktrees/M3-9d3f369/.venv/Scripts/python.exe
M=$R/.claude/worktrees/v0-2-1-gauntlet-fixes-13f5e7/docs/validation/v0.2.1/population/selftest-2/manifest.json
```

## Independent checks

```bash
# SNR (8 cases) and AR(1) Monte Carlo
$P0 snr_check.py $M planet-measurable-white-0000 planet-measurable-correlated-0002 planet-near-correlated-0005 false_positive-measurable-correlated-0002 false_positive-measurable-white-0004 false_positive-measurable-correlated-0004 false_positive-below-correlated-0001 planet-near-white-0007
# serialization: 3 cases generated twice (different workers and order), compared, parsed
printf 'planet-measurable-white-0000\nfalse_positive-measurable-white-0004\nno_transit-none-correlated-0004\n' > ser-cases.txt
$P0 $H generate --population selftest --cache gen-a --cases-from ser-cases.txt --check $M --workers 3
$P0 $H generate --population selftest --cache gen-b --cases-from ser-cases.txt --check $M --workers 1 --order reverse
cmp gen-a/<id>.rpc gen-b/<id>.rpc        # for each of the 3 ids
$P0 ser_check.py $M gen-a/planet-measurable-white-0000.rpc gen-a/false_positive-measurable-white-0004.rpc gen-a/no_transit-none-correlated-0004.rpc
# statistics
$P0 stats_check.py $H
# seeds (seed strings only, no case is built)
$P0 seed_check.py $H
```

## Six-case manifest used by the runtime scenarios

```bash
$P0 -c "
import json,sys
m=json.load(open(sys.argv[1],encoding='utf-8'))
keep=['planet-measurable-white-0004','planet-near-white-0005','false_positive-measurable-white-0004','false_positive-below-white-0001','no_transit-none-white-0000','no_transit-none-correlated-0002']
m['cases']=[c for c in m['cases'] if c['id'] in keep]
assert len(m['cases'])==6
open(sys.argv[2],'w',encoding='utf-8').write(json.dumps(m,sort_keys=True,separators=(',',':'))+'\n')
" $M manifest-6.json
```

## Interruption by PID and resumption (PowerShell)

```powershell
$root = 'C:\Projetos\refute'; $G = "$root\.cache\review-g"
$H = "$root\.claude\worktrees\v0-2-1-gauntlet-fixes-13f5e7\docs\validation\v0.2.1\population\population.py"
$gen = "$root\.worktrees\v0.2.0\.venv\Scripts\python.exe"; $m3 = "$root\.worktrees\M3-9d3f369\.venv\Scripts\python.exe"
$a = @($H, 'orchestrate', '--manifest', "$G\manifest-6.json", '--project', "$G\proj", '--cache', "$G\proj\.cache\population", '--generator-python', $gen, '--point', "M0=$gen=$G\runs2\M0", '--point', "M3=$m3=$G\runs2\M3", '--lot-size', '2', '--records', "$G\records2", '--workers', '1')
$p = Start-Process -FilePath $gen -ArgumentList $a -RedirectStandardOutput "$G\orch-2.out" -RedirectStandardError "$G\orch-2.err" -PassThru -NoNewWindow
# poll until records2 has lot-0001-*-2-regenerated.json and runs2\M0\cases has >= 3 files, then:
taskkill /PID $p.Id /T /F
# snapshot: sha256sum runs2/*/cases/*.json > snap-after-kill.txt
# resume: same $a with -Wait (orch-3.out); then sha256sum -c snap-after-kill.txt
```

## Negative scenarios (bash, in .cache/review-g)

```bash
$P0 $H generate --population selftest --cache cache6 --check manifest-6.json --workers 6   # (no --cases-from: wrote all 44, 38 "DIVERGED")
cp -r runs2/M0 neg/trunc-M0; cp -r runs2/M0 neg/cond-M0; cp -r runs2/M0 neg/poison-M0
# truncated result
f=neg/trunc-M0/cases/planet-near-white-0005.json; s=$(stat -c %s $f); head -c $((s/2)) $f > neg/trunc.tmp && mv neg/trunc.tmp $f
$P0 $H analyze --manifest manifest-6.json --cache cache6 --out neg/trunc-M0 --point M0 --workers 2
# condition ii removed
$P0 -c "
import json,sys; p=sys.argv[1]; r=json.load(open(p,encoding='utf-8')); del r['conditions']['ii']; open(p,'w',encoding='utf-8').write(json.dumps(r))" neg/cond-M0/cases/planet-measurable-white-0004.json
$P0 $H analyze --manifest manifest-6.json --cache cache6 --out neg/cond-M0 --point M0 --workers 2
# C2: resume of an M0 run with the M3 environment, then metrics on it
$P3 $H analyze --manifest manifest-6.json --cache cache6 --out neg/poison-M0 --point M0 --workers 2
$P0 $H metrics --manifest manifest-6.json --runs neg/poison-M0 runs2/M3 --out out/m-poison.json
# metrics refusals
$P0 $H metrics --manifest manifest-6.json --runs runs2/M0 runs2/M0 --out out/m-dup.json
$P0 $H metrics --manifest $M --runs runs2/M0 --out out/m-man.json
# C1: M3 environment labeled M0, merged with half of a real M0 run
printf 'planet-measurable-white-0004\nplanet-near-white-0005\nno_transit-none-white-0000\n' > neg/half.txt
$P3 $H analyze --manifest manifest-6.json --cache cache6 --out neg/label-M0x --point M0 --cases-from neg/half.txt --workers 3
cp -r runs2/M0 neg/half-M0; for i in $(cat neg/half.txt); do rm neg/half-M0/cases/$i.json; done
$P0 $H metrics --manifest manifest-6.json --runs neg/half-M0 neg/label-M0x runs2/M3 --out out/m-mixed.json
# C3: empty cache, then resume with the right cache
mkdir -p neg/emptycache
$P0 $H analyze --manifest manifest-6.json --cache neg/emptycache --out neg/missing --point M0 --workers 2
$P0 $H analyze --manifest manifest-6.json --cache cache6 --out neg/missing --point M0 --workers 2
$P0 $H metrics --manifest manifest-6.json --runs neg/missing --out out/m-missing.json
# N8: a result file whose content claims another case id
cp -r runs2/M0 neg/dupid-M0; cp neg/dupid-M0/cases/planet-near-white-0005.json neg/dupid-M0/cases/planet-measurable-white-0004.json
$P0 $H metrics --manifest manifest-6.json --runs neg/dupid-M0 --out out/m-dupid.json
```

Outputs of the first review are those quoted in its report (not preserved as files).
