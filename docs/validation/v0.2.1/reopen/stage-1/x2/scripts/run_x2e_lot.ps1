# X2e's lot (x2e-execution-package.md). Run ONLY after the maintainer's authorization.
# Logical processors 8 to 31 (set here, inherited by the 22 workers), the study's M4 configuration,
# the ceiling of 3 h; the run folder .cache/x2e-lot/<UTC date> of the integration worktree.
# A relaunch on the same folder resumes the lot: it is a rerun and needs its approval recorded in a
# GitHub issue first.
#   powershell -NoProfile -ExecutionPolicy Bypass -File <this> [-RunDir <existing folder to resume>]
param([string]$RunDir = '')
$ErrorActionPreference = 'Stop'
[System.Diagnostics.Process]::GetCurrentProcess().ProcessorAffinity = [IntPtr][int64]4294967040
$root = 'C:/Projetos/refute/.cache/wt-merge-check'
$python = "$root/.venv/Scripts/python.exe"
$script = "$root/docs/validation/v0.2.1/population/x2_study.py"
$env:PYTHONDONTWRITEBYTECODE = '1'
$env:REFUTE_M4_CONFIGURATION = "$root/docs/validation/v0.2.1/population/m4-configurations/rmin-study.json"
Remove-Item Env:REFUTE_M4_EXPECTED_IDENTITY -ErrorAction SilentlyContinue
if (-not $RunDir) { $RunDir = "$root/.cache/x2e-lot/" + (Get-Date).ToUniversalTime().ToString('yyyyMMddTHHmmssZ') }
Set-Location -LiteralPath $root
$head = git -C $root rev-parse HEAD
Write-Output "code $head; run folder $RunDir"
& $python $script run $RunDir --lot x2e --workers 22 --deadline-hours 3
$runExit = $LASTEXITCODE
Write-Output "x2e run exit=$runExit"
& $python $script check $RunDir
$checkExit = $LASTEXITCODE
Write-Output "x2e check exit=$checkExit"
# the wrapper fails when either step fails (Codex's review: X2's wrapper only printed the codes)
if ($runExit -ne 0) { exit $runExit }
exit $checkExit
