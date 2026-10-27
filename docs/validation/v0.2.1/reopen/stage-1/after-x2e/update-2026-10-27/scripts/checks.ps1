# The checks of the dependency update of 2026-10-27 (dependencies-reachability.md, "The update of
# 2026-10-27, checked in full"), one after the other, on logical processors 8 to 31:
# 1. the full suite in the updated environment (JUnit);
# 2. the acceptance population of population_v4 generated again (one generation, 22 workers), its
#    manifest compared with aee9ecac...12ce2;
# 3. the frozen comparison environment of the earlier lock (79e16fa7...) built in a detached
#    worktree of the commit before the update, with uv sync --frozen;
# 4. the same X2 subset (2 cases per group, 4 realizations: 32 tasks) in both environments, the
#    records compared byte for byte.
$ErrorActionPreference = 'Stop'
[System.Diagnostics.Process]::GetCurrentProcess().ProcessorAffinity = [IntPtr][int64]4294967040
$root = 'C:/Projetos/refute/.cache/wt-merge-check'
$out = "$root/.cache/deps-1027"
Set-Location -LiteralPath $root
function Stamp($m) { Write-Output ((Get-Date).ToUniversalTime().ToString('u') + ' ' + $m) }

Stamp 'suite'
powershell -NoProfile -ExecutionPolicy Bypass -File scripts/run_tests_affinity.ps1 -Junit .cache/deps-1027/suite.xml
& .venv/Scripts/python.exe scripts/junit_counts.py .cache/deps-1027/suite.xml

Stamp 'acceptance population'
& .venv/Scripts/python.exe docs/validation/v0.2.1/population/population_v4_check.py run --population acceptance --generation after-update --workers 22 --order index --out-dir .cache/deps-1027/acceptance *> "$out/acceptance.log"
Write-Output "acceptance exit=$LASTEXITCODE"
$new = (Get-FileHash -Algorithm SHA256 -LiteralPath "$out/acceptance/manifest-after-update.json").Hash.ToLower()
$ref = (Get-FileHash -Algorithm SHA256 -LiteralPath docs/validation/v0.2.1/population/v4-acceptance/manifest-1.json).Hash.ToLower()
Write-Output "manifest after the update $new; reference $ref; equal=$($new -eq $ref)"

Stamp 'frozen environment'
$frozen = "$root/.cache/frozen-env-79e16fa7"
if (-not (Test-Path -LiteralPath $frozen)) { git worktree add --detach $frozen b929aae8e8272e031cb56a4a5bb8e2ebf7ce8d32 }
Set-Location -LiteralPath $frozen
uv sync --frozen *> "$out/frozen-sync.log"
Write-Output "frozen sync exit=$LASTEXITCODE"
& "$frozen/.venv/Scripts/python.exe" "$root/docs/validation/v0.2.1/reopen/stage-1/after-x2e/scripts/env_record.py" "$out/env-record-frozen.json"
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
