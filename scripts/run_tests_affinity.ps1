# Run pytest from the project's virtual environment with CPU affinity on threads 8 to 31
# (mask 0xFFFFFF00), and write a JUnit XML file (test counts are read from it, never
# from the console; CLAUDE.md). The command guard hook (.claude/hooks/command_guard.py)
# allows pytest only through this script.
#
# Usage:
#   powershell -NoProfile -ExecutionPolicy Bypass -File scripts/run_tests_affinity.ps1 `
#       -Junit .cache/<task>/junit.xml [-Out .cache/<task>/out.txt] [-Tests a.py,b.py] [-K expr]
# Without -Tests the whole suite runs. Prints "pytest exit=<code>".
param(
    [Parameter(Mandatory = $true)][string]$Junit,
    [string]$Out = '',
    [string[]]$Tests = @(),
    [string]$K = ''
)
$ErrorActionPreference = 'Stop'
$root = Split-Path -Parent $PSScriptRoot
[System.Diagnostics.Process]::GetCurrentProcess().ProcessorAffinity = [IntPtr][int64]4294967040
Set-Location -LiteralPath $root
$python = Join-Path $root '.venv\Scripts\python.exe'
if (-not (Test-Path -LiteralPath $python)) { throw "project venv not found: $python" }
if (-not $Out) { $Out = [System.IO.Path]::ChangeExtension($Junit, '.out.txt') }
foreach ($file in @($Junit, $Out)) {
    $dir = Split-Path -Parent ([System.IO.Path]::GetFullPath((Join-Path $root $file)))
    if (-not (Test-Path -LiteralPath $dir)) { New-Item -ItemType Directory -Path $dir | Out-Null }
}
$files = @($Tests | ForEach-Object { $_.Split(',') } | Where-Object { $_ })  # -File passes one string
$argv = @('-m', 'pytest', '-q', '-p', 'no:cacheprovider', "--junitxml=$Junit") + $files
if ($K) { $argv += @('-k', $K) }
# Start-Process joins its arguments with spaces: quote each one that needs it.
$quoted = $argv | ForEach-Object {
    if ($_ -match '[\s"]') { '"' + ($_ -replace '"', '\"') + '"' } else { $_ }
}
$p = Start-Process -FilePath $python -ArgumentList ($quoted -join ' ') -NoNewWindow -Wait -PassThru `
    -RedirectStandardOutput $Out -RedirectStandardError ([System.IO.Path]::ChangeExtension($Out, '.err.txt'))
Write-Output ("pytest exit=" + $p.ExitCode)
exit $p.ExitCode
