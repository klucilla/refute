# Run pytest from the project's virtual environment with CPU affinity on threads 8 to 31
# (mask 0xFFFFFF00) by default, and write a JUnit XML file (test counts are read from it,
# never from the console; CLAUDE.md). The command guard hook (.claude/hooks/command_guard.py)
# allows pytest only through this script.
#
# Usage:
#   powershell -NoProfile -ExecutionPolicy Bypass -File scripts/run_tests_affinity.ps1 `
#       -Junit .cache/<task>/junit.xml [-Out .cache/<task>/out.txt] [-Tests a.py,b.py] [-K expr] `
#       [-Threads <first>-<last>] [-Workers <n>]
# Without -Tests the whole suite runs. Prints "pytest exit=<code>".
# -Junit and -Out are relative to the project root, or absolute; without -Out, the output
# goes next to the JUnit file (<junit>.out.txt and <junit>.out.err.txt).
# -Threads pins the run to another contiguous range of logical processors (for example
# 0-7, the range given to the v0.2.1 work while v0.3 runs on 8-31); the default is 8-31.
# -Workers sets REFUTE_WORKERS for the run (the analysis worker count); without it the
# inherited value, or the default of refute.core.runner.default_workers, applies.
param(
    [Parameter(Mandatory = $true)][string]$Junit,
    [string]$Out = '',
    [string[]]$Tests = @(),
    [string]$K = '',
    [string]$Threads = '8-31',
    [int]$Workers = 0
)
$ErrorActionPreference = 'Stop'
$root = Split-Path -Parent $PSScriptRoot
if ($Threads -notmatch '^(\d+)-(\d+)$') { throw "-Threads must be <first>-<last>, got '$Threads'" }
$first = [int]$Matches[1]
$last = [int]$Matches[2]
if ($first -gt $last -or $last -ge [Environment]::ProcessorCount) {
    throw "-Threads $Threads is outside 0-$([Environment]::ProcessorCount - 1)"
}
$mask = [int64]0
for ($i = $first; $i -le $last; $i++) { $mask = $mask -bor ([int64]1 -shl $i) }
[System.Diagnostics.Process]::GetCurrentProcess().ProcessorAffinity = [IntPtr]$mask
if ($Workers -lt 0) { throw "-Workers must be a positive integer, got $Workers" }
if ($Workers -gt 0) { $env:REFUTE_WORKERS = [string]$Workers }
Set-Location -LiteralPath $root
$python = Join-Path $root '.venv\Scripts\python.exe'
if (-not (Test-Path -LiteralPath $python)) { throw "project venv not found: $python" }
function Resolve-RunPath([string]$Path) {
    # an absolute path is kept; a relative one is taken from the project root (Join-Path
    # with an absolute path would join the two, and GetFullPath would then fail)
    if ([System.IO.Path]::IsPathRooted($Path)) { return [System.IO.Path]::GetFullPath($Path) }
    return [System.IO.Path]::GetFullPath((Join-Path $root $Path))
}
$Junit = Resolve-RunPath $Junit
if ($Out) { $Out = Resolve-RunPath $Out } else { $Out = [System.IO.Path]::ChangeExtension($Junit, '.out.txt') }
foreach ($file in @($Junit, $Out)) {
    $dir = Split-Path -Parent $file
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
