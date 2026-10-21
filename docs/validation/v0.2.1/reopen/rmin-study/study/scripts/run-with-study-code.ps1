# Run a Python script with the R_min study's own code and environment (.cache/wt-v021 at
# 2e4ff99, its venv, the study's M4 configuration), on processors 0 to 7, writing no bytecode
# there (PYTHONDONTWRITEBYTECODE). Outputs go only where the arguments say (outside wt-v021).
#   -Script <path> -ArgList <args...>
param(
    [Parameter(Mandatory = $true)][string]$Script,
    [string[]]$ArgList = @()
)
$ErrorActionPreference = 'Stop'
$wt = 'C:/Projetos/refute/.cache/wt-v021'
$head = git -C $wt rev-parse HEAD
if ($head -ne '2e4ff998ca1596c281abf915222714e1276173f3') { throw "wt-v021 is at $head, not 2e4ff99" }
$dirty = git -C $wt status --porcelain --untracked-files=no
if ($dirty) { throw "wt-v021 has tracked changes: $dirty" }
[System.Diagnostics.Process]::GetCurrentProcess().ProcessorAffinity = [IntPtr][int64]255
$env:PYTHONDONTWRITEBYTECODE = '1'
$env:REFUTE_M4_CONFIGURATION = "$wt/docs/validation/v0.2.1/population/m4-configurations/rmin-study.json"
Remove-Item Env:REFUTE_M4_EXPECTED_IDENTITY -ErrorAction SilentlyContinue
Set-Location -LiteralPath 'C:/Projetos/refute/.cache/merge-v021/rmin'
$argv = @($ArgList | ForEach-Object { $_.Split(',') } | Where-Object { $_ })  # -File passes one string
& "$wt/.venv/Scripts/python.exe" $Script @argv
Write-Output "python exit=$LASTEXITCODE"
