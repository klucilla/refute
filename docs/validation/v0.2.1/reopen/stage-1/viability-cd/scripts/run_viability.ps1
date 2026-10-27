# The C/D viability package's execution (README.md, sections 7 and 8; authorization 2 of 2026-10-27).
# Logical processors 8 to 31 (set here, inherited by the 22 workers), the R_min study's M4
# configuration; fixed run folders under .cache/viability-lot of the integration worktree, so a
# relaunch on the same folder resumes the sub-lot (the one pre-approved resumption, recorded in the
# lot's GitHub issue; any other rerun needs its own approval there first).
#   powershell -NoProfile -ExecutionPolicy Bypass -File <this> -Op env -Out <file>
#   powershell -NoProfile -ExecutionPolicy Bypass -File <this> -Op determinism -Lot viability-c -N 24
#   powershell -NoProfile -ExecutionPolicy Bypass -File <this> -Op run -Lot viability-c
param(
    [Parameter(Mandatory = $true)][ValidateSet('env', 'determinism', 'run')][string]$Op,
    [ValidateSet('viability-c', 'viability-d')][string]$Lot = 'viability-c',
    [int]$N = 0,
    [string]$Out = ''
)
$ErrorActionPreference = 'Stop'
[System.Diagnostics.Process]::GetCurrentProcess().ProcessorAffinity = [IntPtr][int64]4294967040
$root = 'C:/Projetos/refute/.cache/wt-merge-check'
$python = "$root/.venv/Scripts/python.exe"
$module = "$root/docs/validation/v0.2.1/population/viability_cd.py"
$env:PYTHONDONTWRITEBYTECODE = '1'
$env:REFUTE_M4_CONFIGURATION = "$root/docs/validation/v0.2.1/population/m4-configurations/rmin-study.json"
Remove-Item Env:REFUTE_M4_EXPECTED_IDENTITY -ErrorAction SilentlyContinue
Set-Location -LiteralPath $root
$head = git -C $root rev-parse HEAD
$base = "$root/.cache/viability-lot"
if (-not (Test-Path -LiteralPath $base)) { New-Item -ItemType Directory -Path $base | Out-Null }
if ($Op -eq 'env') {
    & $python "$root/docs/validation/v0.2.1/reopen/stage-1/after-x2e/scripts/env_record.py" $Out
    exit $LASTEXITCODE
}
if ($Op -eq 'determinism') {
    $file = "$base/determinism-$Lot.json"
    Write-Output "code $head; determinism $Lot n=$N -> $file"
    & $python $module determinism $file --lot $Lot --n $N
    exit $LASTEXITCODE
}
$runDir = "$base/$Lot"
Write-Output "code $head; run folder $runDir"
& $python $module run $runDir --lot $Lot
$runExit = $LASTEXITCODE
Write-Output "$Lot run exit=$runExit"
& $python $module check $runDir --lot $Lot --full
$checkExit = $LASTEXITCODE
Write-Output "$Lot check exit=$checkExit"
if ($runExit -ne 0) { exit $runExit }
exit $checkExit
