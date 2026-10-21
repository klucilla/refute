# Launch the R_min study's lot (map Amendment 27; the maintainer's decisions of 2026-10-19),
# detached, on logical processors 0 to 7, with its own ceiling left as the deadline.
$ErrorActionPreference = 'Stop'
$root = 'C:/Projetos/refute/.cache/wt-v021'
[System.Diagnostics.Process]::GetCurrentProcess().ProcessorAffinity = [IntPtr][int64]255
$env:REFUTE_M4_CONFIGURATION = "$root/docs/validation/v0.2.1/population/m4-configurations/rmin-study.json"
Remove-Item Env:REFUTE_M4_EXPECTED_IDENTITY -ErrorAction SilentlyContinue
$log = "$root/.cache/v021/rmin/study-run.log"
$err = "$root/.cache/v021/rmin/study-run.err.log"
$argv = @(
    "$root/docs/validation/v0.2.1/population/rmin_study.py",
    'lot', '--lot', 'study',
    '--run', "$root/.cache/v021/rmin-study-run",
    '--deadline-hours', '254.815'
)
$p = Start-Process -FilePath "$root/.venv/Scripts/python.exe" -ArgumentList $argv -WindowStyle Hidden `
    -RedirectStandardOutput $log -RedirectStandardError $err -PassThru
"pid=$($p.Id) started=$((Get-Date).ToUniversalTime().ToString('o'))" | Out-File -Encoding utf8 "$root/.cache/v021/rmin/study-run.pid"
"pid=$($p.Id)"
