# Launch a Python script of this project from its virtual environment, pinned to a contiguous
# range of logical processors (8 to 31 by default), and record its PID.
#
# Usage:
#   powershell -NoProfile -ExecutionPolicy Bypass -File scripts/launch_affinity.ps1 `
#       -Script calibration/v0.4/run_selection.py -Arguments 'assemble','--approval','<url>' `
#       -Log .cache/<task>/run [-Threads <first>-<last>]
#   powershell -NoProfile -ExecutionPolicy Bypass -File scripts/launch_affinity.ps1 -Threads 8-31 -MaskOnly
# Writes <log>.out.txt, <log>.err.txt and <log>.pid; prints "pid=<n>" and "exit=<code>".
# The mask is built in 64 bits: 0xFFFFFF00 (threads 8 to 31) does not fit a signed 32-bit
# integer, and a PowerShell hex literal such as [IntPtr]0xFFFFFF00 is read as the int32 -256,
# which Windows refuses ("Parameter is incorrect"; the slip of 2026-10-30, attempt 5).
# This process takes the affinity before it starts Python, so Python and every process it
# starts inherit it from their creation; -MaskOnly prints the mask and starts nothing.
param(
    [string]$Script = '',
    [string[]]$Arguments = @(),
    [string]$Log = '',
    [string]$Threads = '8-31',
    [switch]$MaskOnly
)
$ErrorActionPreference = 'Stop'
if ($Threads -notmatch '^(\d+)-(\d+)$') { throw "-Threads must be <first>-<last>, got '$Threads'" }
$first = [int]$Matches[1]
$last = [int]$Matches[2]
if ($first -gt $last -or $last -gt 63) { throw "-Threads $Threads is not a range within 0-63" }
$mask = [int64]0
for ($i = $first; $i -le $last; $i++) { $mask = $mask -bor ([int64]1 -shl $i) }
if ($MaskOnly) { Write-Output ('0x{0:X}' -f $mask); exit 0 }
if ($last -ge [Environment]::ProcessorCount) {
    throw "-Threads $Threads is outside 0-$([Environment]::ProcessorCount - 1)"
}
if (-not $Script -or -not $Log) { throw '-Script and -Log are required' }
$root = Split-Path -Parent $PSScriptRoot
Set-Location -LiteralPath $root
$python = Join-Path $root '.venv\Scripts\python.exe'
if (-not (Test-Path -LiteralPath $python)) { throw "project venv not found: $python" }
[System.Diagnostics.Process]::GetCurrentProcess().ProcessorAffinity = [IntPtr]$mask
# the mask read back from this process, which the child inherits at its creation; it is not read
# from the child, which may already have exited (the race seen in CI on 2026-10-31, run 41193622198)
$inherited = [System.Diagnostics.Process]::GetCurrentProcess().ProcessorAffinity.ToInt64()
$argv = @($Script) + ($Arguments | ForEach-Object { $_.Split(',') } | Where-Object { $_ })
# Start-Process joins its arguments with spaces: quote each one that needs it.
$quoted = $argv | ForEach-Object {
    if ($_ -match '[\s"]') { '"' + ($_ -replace '"', '\"') + '"' } else { $_ }
}
# an absolute path is kept; a relative one is taken from the project root
if (-not [System.IO.Path]::IsPathRooted($Log)) { $Log = Join-Path $root $Log }
$Log = [System.IO.Path]::GetFullPath($Log)
$dir = Split-Path -Parent $Log
if (-not (Test-Path -LiteralPath $dir)) { New-Item -ItemType Directory -Path $dir | Out-Null }
$p = Start-Process -FilePath $python -ArgumentList ($quoted -join ' ') -NoNewWindow -PassThru `
    -RedirectStandardOutput "$Log.out.txt" -RedirectStandardError "$Log.err.txt"
# without an open handle, PowerShell 5.1 leaves ExitCode empty for a process started without -Wait
$null = $p.Handle
Set-Content -LiteralPath "$Log.pid" -Value $p.Id -Encoding ascii
Write-Output ("pid=" + $p.Id + " affinity=" + ('0x{0:X}' -f $inherited))
$p.WaitForExit()
Write-Output ("exit=" + $p.ExitCode)
exit $p.ExitCode
