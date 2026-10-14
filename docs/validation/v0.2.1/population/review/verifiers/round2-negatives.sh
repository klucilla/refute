#!/usr/bin/env bash
# Phase G, second review (harness 33e2d418..., branch commit a83e09a): negative scenarios.
# Run from C:\Projetos\refute\.cache\review-g\r2 after the M0 and M3 runs exist (runs/M0
# with an interruption by PID and a resumption, runs/M3 with one worker) and the cache
# holds the 6 cases of manifest-6.json. Everything is written under r2/neg/.
R=/c/Projetos/refute
W=$R/.claude/worktrees/v0-2-1-gauntlet-fixes-13f5e7/docs/validation/v0.2.1/population
H=$W/population.py
P0=$R/.worktrees/v0.2.0/.venv/Scripts/python.exe
P3=$R/.worktrees/M3-9d3f369/.venv/Scripts/python.exe
WT=$R/.claude/worktrees/v0-2-1-gauntlet-fixes-13f5e7
mkdir -p neg

edit() {  # edit <json file> <python expression on r>
  $P0 -c "
import json,sys
p=sys.argv[1]; r=json.load(open(p,encoding='utf-8'))
$2
open(p,'w',encoding='utf-8').write(json.dumps(r))" "$1"
}
nfiles() { find "$1" -type f 2>/dev/null | wc -l; }

echo "=== A1 (C1) M3 environment with --point M0, on a copy of the M0 run"
cp -r runs/M0 neg/c1-wrongenv
sha256sum neg/c1-wrongenv/cases/*.json neg/c1-wrongenv/run.json > neg/c1-wrongenv.snap
$P3 $H analyze --manifest manifest-6.json --cache cache --out neg/c1-wrongenv --point M0 --workers 2; echo "exit=$?"
sha256sum -c --quiet neg/c1-wrongenv.snap && echo "results and run.json unchanged"
ls neg/c1-wrongenv/attempts

echo "=== A2 (C1) unknown point M9"
$P0 $H analyze --manifest manifest-6.json --cache cache --out neg/c1-unknown --point M9 --workers 2; echo "exit=$?"
echo "files written: $(nfiles neg/c1-unknown) ($(ls neg/c1-unknown/attempts))"

echo "=== A3 (C1) metrics: point M0 made of half of the real M0 run and half of the M3 run relabeled M0"
printf 'planet-measurable-white-0004\nplanet-near-white-0005\nno_transit-none-white-0000\n' > neg/half.txt
cp -r runs/M0 neg/c1-mixed-a; for i in $(cat neg/half.txt); do rm neg/c1-mixed-a/cases/$i.json; done
cp -r runs/M3 neg/c1-mixed-b; for f in neg/c1-mixed-b/cases/*.json; do b=$(basename $f .json); grep -qx "$b" neg/half.txt || rm $f; done
edit neg/c1-mixed-b/run.json "r['point']='M0'; r['binding']['point']='M0'"
for f in neg/c1-mixed-b/cases/*.json; do edit $f "r['point']='M0'"; done
for f in neg/c1-mixed-b/attempts/*started.json; do edit $f "r['binding']['point']='M0'"; done
$P0 $H metrics --manifest manifest-6.json --runs neg/c1-mixed-a neg/c1-mixed-b runs/M3 --out neg/out/a3.json; echo "exit=$?"; ls neg/out 2>&1
echo "--- A3b: also the binding commit set to M0's commit"
cp -r neg/c1-mixed-b neg/c1-mixed-c
edit neg/c1-mixed-c/run.json "r['binding']['commit']='f4798230f1bca607bcc0e98fe47711a26ec4ee59'"
for f in neg/c1-mixed-c/attempts/*started.json; do edit $f "r['binding']['commit']='f4798230f1bca607bcc0e98fe47711a26ec4ee59'"; done
$P0 $H metrics --manifest manifest-6.json --runs neg/c1-mixed-a neg/c1-mixed-c runs/M3 --out neg/out/a3b.json; echo "exit=$?"; ls neg/out 2>&1

echo "=== B (C2) metrics over the run with the refused attempt of A1"
$P0 $H metrics --manifest manifest-6.json --runs neg/c1-wrongenv runs/M3 --out neg/out/b.json; echo "exit=$?"
$P0 -c "import json; m=json.load(open('neg/out/b.json')); print(m['points'][0]['refused_attempts'])"

echo "=== C1 (C3) empty cache"
mkdir -p neg/emptycache
$P0 $H analyze --manifest manifest-6.json --cache neg/emptycache --out neg/c3-missing --point M0 --workers 2; echo "exit=$?"
echo "result files: $(ls neg/c3-missing/cases | wc -l); attempts: $(ls neg/c3-missing/attempts)"
echo "--- same command with the right cache"
$P0 $H analyze --manifest manifest-6.json --cache cache --out neg/c3-missing --point M0 --workers 2; echo "exit=$?"
echo "result files: $(ls neg/c3-missing/cases | wc -l)"

echo "=== C2 (C3) divergent hash: one of two inputs with its last byte changed"
mkdir -p neg/badcache
cp cache/planet-near-white-0005.rpc cache/no_transit-none-white-0000.rpc neg/badcache/
$P0 -c "
p='neg/badcache/no_transit-none-white-0000.rpc'; b=bytearray(open(p,'rb').read()); b[-1]^=1; open(p,'wb').write(bytes(b))"
printf 'planet-near-white-0005\nno_transit-none-white-0000\n' > neg/two.txt
$P0 $H analyze --manifest manifest-6.json --cache neg/badcache --out neg/c3-divergent --point M0 --cases-from neg/two.txt --workers 2; echo "exit=$?"
echo "result files: $(ls neg/c3-divergent/cases | wc -l); attempts: $(ls neg/c3-divergent/attempts)"

echo "=== D truncated result, on a copy of the M0 run"
cp -r runs/M0 neg/trunc
f=neg/trunc/cases/planet-near-white-0005.json; s=$(stat -c %s $f); head -c $((s/2)) $f > neg/trunc.part && mv neg/trunc.part $f
sha256sum neg/trunc/cases/*.json > neg/trunc.snap
rm neg/trunc/cases/no_transit-none-white-0000.json   # so that the resume has a case to dispatch
$P0 $H analyze --manifest manifest-6.json --cache cache --out neg/trunc --point M0 --workers 2; echo "exit=$?"
echo "result files: $(ls neg/trunc/cases | wc -l) (5 expected, nothing redone)"

echo "=== E1 (N8) a result file whose content is another case"
cp -r runs/M0 neg/dupid; cp neg/dupid/cases/planet-near-white-0005.json neg/dupid/cases/planet-measurable-white-0004.json
$P0 $H metrics --manifest manifest-6.json --runs neg/dupid --out neg/out/e1.json; echo "exit=$?"; ls neg/out/e1* 2>&1

echo "=== E2 (N8) --records: constructed results-reread record over runs/M0 and runs/M3"
mkdir -p neg/records
$P0 -c "
import hashlib,glob,json,os
h={}
for d in ('runs/M0','runs/M3'):
    for f in sorted(glob.glob(d+'/cases/*.json')):
        h[os.path.basename(d)+'/'+os.path.basename(f)[:-5]]=hashlib.sha256(open(f,'rb').read()).hexdigest()
open('neg/records/lot-0000-review-3-results-reread.json','w').write(json.dumps({'lot':0,'results_sha256':h}))
print(len(h),'hashes')"
$P0 $H metrics --manifest manifest-6.json --runs runs/M0 runs/M3 --records neg/records --out neg/out/e2-ok.json; echo "exit=$?"
mkdir -p neg/e2; cp -r runs/M0 neg/e2/M0
edit neg/e2/M0/cases/planet-near-white-0005.json "r['conditions']['i']['verdict']='SURVIVED' if r['conditions']['i']['verdict']!='SURVIVED' else 'REFUTED'"
$P0 $H metrics --manifest manifest-6.json --runs neg/e2/M0 runs/M3 --records neg/records --out neg/out/e2-bad.json; echo "exit=$?"; ls neg/out/e2-bad* 2>&1

echo "=== E3 (N8) existing output"
$P0 $H metrics --manifest manifest-6.json --runs runs/M0 runs/M3 --out neg/out/e2-ok.json; echo "exit=$?"
echo "=== E4 (N8) same point twice; two runs with the same folder name"
$P0 $H metrics --manifest manifest-6.json --runs runs/M0 neg/c1-mixed-a --out neg/out/e4.json; echo "exit=$?"
$P0 $H metrics --manifest manifest-6.json --runs runs/M0 neg/e2/M0 --out neg/out/e4b.json; echo "exit=$?"

echo "=== F points.json history: recorded repository commit where points.json does not exist; recorded SHA-256 changed"
cp -r runs/M0 neg/f-commit; edit neg/f-commit/run.json "r['points_at_start']['repository_commit']='6e57b358b3aa542f5feb5b11342a9af8a5f04a36'"
$P0 $H metrics --manifest manifest-6.json --runs neg/f-commit runs/M3 --out neg/out/f1.json; echo "exit=$?"
cp -r runs/M0 neg/f-sha; edit neg/f-sha/run.json "r['points_at_start']['sha256']='0'*64"
$P0 $H metrics --manifest manifest-6.json --runs neg/f-sha runs/M3 --out neg/out/f2.json; echo "exit=$?"

echo "=== G (N9) orchestrate with --project not the top of the harness's repository; cache outside .cache/population"
$P0 $H orchestrate --manifest manifest-6.json --project neg/proj --cache neg/proj/.cache/population --generator-python $P0 --point "M0=$P0=neg/g-run" --records neg/g-records --workers 1; echo "exit=$?"
$P0 $H orchestrate --manifest manifest-6.json --project $WT --cache neg/g-cache --generator-python $P0 --point "M0=$P0=neg/g-run" --records neg/g-records --workers 1; echo "exit=$?"
echo "written by G: $(ls -d neg/proj neg/g-run neg/g-records neg/g-cache 2>&1 | grep -vc 'No such')"
