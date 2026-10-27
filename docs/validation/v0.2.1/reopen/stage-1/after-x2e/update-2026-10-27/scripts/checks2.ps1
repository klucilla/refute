# The checks of the dependency update of 2026-10-27, continued from step 3 (checks.ps1 stopped
# there: under $ErrorActionPreference = 'Stop', Windows PowerShell 5.1 turns uv's first stderr line
# into a terminating NativeCommandError). Steps 1 and 2 passed (suite 3934/0/0/89; acceptance
# manifest equal to aee9ecac...12ce2). Native commands run with 'Continue'; their exit codes are
# printed and checked. On logical processors 8 to 31.
# 3. the frozen comparison environment of the earlier lock (79e16fa7...), uv sync --frozen;
# 4. the same X2 subset (2 cases per group, 4 realizations: 32 tasks) in both environments.
$ErrorActionPreference = 'Continue'
[System.Diagnostics.Process]::GetCurrentProcess().ProcessorAffinity = [IntPtr][int64]4294967040
$root = 'C:/Projetos/refute/.cache/wt-merge-check'
$out = "$root/.cache/deps-1027"
$frozen = "$root/.cache/frozen-env-79e16fa7"
function Stamp($m) { Write-Output ((Get-Date).ToUniversalTime().ToString('u') + ' ' + $m) }

Stamp 'frozen environment'
Set-Location -LiteralPath $frozen
uv sync --frozen *> "$out/frozen-sync.log"
$code = $LASTEXITCODE
Write-Output "frozen sync exit=$code"
if ($code -ne 0) { exit 1 }
& "$frozen/.venv/Scripts/python.exe" "$root/docs/validation/v0.2.1/reopen/stage-1/after-x2e/scripts/env_record.py" "$out/env-record-frozen.json"
Write-Output "frozen env record exit=$LASTEXITCODE"
Set-Location -LiteralPath $root

Stamp 'x2 subset, both environments'
$env:PYTHONDONTWRITEBYTECODE = '1'
foreach ($pair in @(@('updated', $root), @('frozen', $frozen))) {
    $name, $tree = $pair
    $env:REFUTE_M4_CONFIGURATION = "$tree/docs/validation/v0.2.1/population/m4-configurations/rmin-study.json"
    & "$tree/.venv/Scripts/python.exe" "$tree/docs/validation/v0.2.1/population/x2_study.py" run "$out/x2-subset-$name" --workers 22 --subset 2 4 *> "$out/x2-subset-$name.log"
    Write-Output "x2 subset $name exit=$LASTEXITCODE"
}
Stamp 'done'
