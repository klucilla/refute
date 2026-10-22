# X2's resumption check on the real configuration (x2-execution-package.md, section 4), before the lot:
# a subset run continuously (A); the same subset started (B), stopped by its own PID and its workers'
# PIDs once at least 3 records exist, then relaunched to completion; A's and B's records compared
# byte for byte. Processors 8 to 31. Writes resume-check.json beside this script.
param([string]$Subset = '1 3')
$ErrorActionPreference = 'Stop'
[System.Diagnostics.Process]::GetCurrentProcess().ProcessorAffinity = [IntPtr][int64]4294967040
$root = 'C:/Projetos/refute/.cache/wt-merge-check'
$here = 'C:/Projetos/refute/.cache/merge-v021/x2'
$python = "$root/.venv/Scripts/python.exe"
$script = "$root/docs/validation/v0.2.1/population/x2_study.py"
$env:PYTHONDONTWRITEBYTECODE = '1'
$env:REFUTE_M4_CONFIGURATION = "$root/docs/validation/v0.2.1/population/m4-configurations/rmin-study.json"
Remove-Item Env:REFUTE_M4_EXPECTED_IDENTITY -ErrorAction SilentlyContinue
$stamp = Get-Date -Format 'yyyyMMddTHHmmss'
$base = "$root/.cache/x2-resume-check/$stamp"
$a = "$base/continuous"; $b = "$base/interrupted"
New-Item -ItemType Directory -Force "$root/.cache/x2-resume-check" | Out-Null
$sub = $Subset.Split(' ')
Set-Location -LiteralPath $root
$t0 = Get-Date
& $python $script run $a --workers 22 --subset $sub[0] $sub[1] | Out-File "$base-a.txt" -Encoding utf8
$aSeconds = ((Get-Date) - $t0).TotalSeconds
$p = Start-Process -FilePath $python -ArgumentList @($script, 'run', $b, '--workers', '22', '--subset', $sub[0], $sub[1]) -PassThru -NoNewWindow -RedirectStandardOutput "$base-b1.txt" -RedirectStandardError "$base-b1.err.txt"
$deadline = (Get-Date).AddMinutes(10)
do {
    Start-Sleep -Milliseconds 500
    $n = @(Get-ChildItem -LiteralPath "$b/records" -Recurse -Filter '*.json' -ErrorAction SilentlyContinue | Where-Object { -not $_.Name.StartsWith('.') }).Count
} while ($n -lt 3 -and -not $p.HasExited -and (Get-Date) -lt $deadline)
function Get-Tree([int]$id) {
    $kids = @(Get-CimInstance Win32_Process -Filter "ParentProcessId=$id" | ForEach-Object { [int]$_.ProcessId })
    $all = @()
    foreach ($k in $kids) { $all += Get-Tree $k; $all += $k }
    return $all
}
$killed = @()
if (-not $p.HasExited) {
    $tree = @(Get-Tree $p.Id)
    Stop-Process -Id $p.Id -Force
    $killed += $p.Id
    foreach ($k in $tree) { try { Stop-Process -Id $k -Force -ErrorAction Stop; $killed += $k } catch {} }
}
Start-Sleep -Seconds 2
$atKill = @(Get-ChildItem -LiteralPath "$b/records" -Recurse -Filter '*.json' | Where-Object { -not $_.Name.StartsWith('.') }).Count
& $python $script run $b --workers 22 --subset $sub[0] $sub[1] | Out-File "$base-b2.txt" -Encoding utf8
& $python "$here/compare_lots.py" $a $b "$here/resume-check.json" $atKill ($killed -join ',') $aSeconds
Write-Output "resume check: $base"
