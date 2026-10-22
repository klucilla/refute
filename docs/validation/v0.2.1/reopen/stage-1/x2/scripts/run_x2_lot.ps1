# X2's lot (x2-execution-package.md, section 5). Run ONLY after the maintainer's authorization.
# Logical processors 8 to 31 (set here, inherited by the 22 workers), the study's M4 configuration,
# the ceiling of 11 h; the run folder .cache/x2-lot/<UTC date> of the integration worktree.
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
if (-not $RunDir) { $RunDir = "$root/.cache/x2-lot/" + (Get-Date).ToUniversalTime().ToString('yyyyMMddTHHmmssZ') }
Set-Location -LiteralPath $root
$head = git -C $root rev-parse HEAD
Write-Output "code $head; run folder $RunDir"
& $python $script run $RunDir --workers 22 --deadline-hours 11
Write-Output "x2 run exit=$LASTEXITCODE"
& $python $script check $RunDir
Write-Output "x2 check exit=$LASTEXITCODE"
