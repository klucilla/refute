# Run the audit tests on the code before the fixes (the code files of d8c2de3), then restore the
# fixed files, each checked by SHA-256. The tests themselves stay the current ones.
$ErrorActionPreference = 'Stop'
$root = 'C:/Projetos/refute/.cache/wt-merge-check'
Set-Location -LiteralPath $root
$files = @(
    'src/refute/packs/tess/adapter.py', 'src/refute/core/dossier.py', 'src/refute/core/run.py',
    'src/refute/core/pack.py', 'src/refute/cli.py', 'src/refute/packs/ml/production.py',
    'src/refute/packs/ml/integration.py', 'src/refute/core/review.py', '.claude/settings.json'
)
$backup = 'C:/Projetos/refute/.cache/audit/fixed'
New-Item -ItemType Directory -Force $backup | Out-Null
$hashes = @{}
foreach ($f in $files) {
    $dest = Join-Path $backup ($f -replace '/', '__')
    Copy-Item -LiteralPath $f -Destination $dest -Force
    $hashes[$f] = (Get-FileHash -Algorithm SHA256 -LiteralPath $f).Hash
}
try {
    git checkout d8c2de3 -- @files
    powershell -NoProfile -ExecutionPolicy Bypass -File scripts/run_tests_affinity.ps1 -Junit .cache/audit/before.xml -Tests tests/test_audit_fixes.py,tests/test_hook_settings.py
} finally {
    foreach ($f in $files) {
        Copy-Item -LiteralPath (Join-Path $backup ($f -replace '/', '__')) -Destination $f -Force
        $now = (Get-FileHash -Algorithm SHA256 -LiteralPath $f).Hash
        if ($now -ne $hashes[$f]) { throw "restore failed: $f" }
    }
    git reset -q -- @files
    Write-Output 'restored and checked'
}
