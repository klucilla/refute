<#
.SYNOPSIS
Downloads the Ubuntu Server 26.04.1 live ISO with SHA256SUMS and SHA256SUMS.gpg, and
verifies them: the signature of SHA256SUMS by the Ubuntu CD image key (by its full
fingerprint), the single line of the ISO in SHA256SUMS, and the ISO's SHA-256. Runs as
the maintainer's account. Without -Apply it only prints what it would do.

.DESCRIPTION
Sources (retrieved 2026-10-15):
  - files: https://releases.ubuntu.com/26.04/ (ubuntu-26.04.1-live-server-amd64.iso,
    SHA256SUMS, SHA256SUMS.gpg);
  - key and commands: https://ubuntu.com/tutorials/how-to-verify-ubuntu ("Ubuntu CD
    Image Automatic Signing Key (2012)", fingerprint
    8439 38DF 228D 22F7 B374 2BC0 D94A A3F0 EFE2 1092).
GnuPG is not part of Windows: the gpg of Git for Windows, already installed, is used,
with a key ring of its own inside the project (.cache/vm/gnupg). curl.exe is part of
Windows. Nothing is overwritten: every destination must not exist. The evidence goes
to .cache/vm/media/media-verification.json; the ISO's SHA-256 then goes into
RefuteVm.Config.psd1 (InstallIsoSha256) in a reviewed change, before the endpoint is
registered.
#>
[CmdletBinding()]
param(
    [switch]$Apply,
    [string]$GpgPath = 'C:\Program Files\Git\usr\bin\gpg.exe'
)
$ErrorActionPreference = 'Stop'
Set-StrictMode -Version 2.0

$BaseUrl = 'https://releases.ubuntu.com/26.04/'
$IsoName = 'ubuntu-26.04.1-live-server-amd64.iso'
$Fingerprint = '843938DF228D22F7B3742BC0D94AA3F0EFE21092'
$Keyserver = 'hkps://keyserver.ubuntu.com'
$MediaDir = 'C:\Projetos\refute\.cache\vm\media'
$GnupgHome = 'C:\Projetos\refute\.cache\vm\gnupg'
$Curl = Join-Path $env:SystemRoot 'System32\curl.exe'
$Files = @('SHA256SUMS', 'SHA256SUMS.gpg', $IsoName)

Write-Output "Download from $BaseUrl : $($Files -join ', ') -> $MediaDir"
Write-Output "Key: $Fingerprint from $Keyserver into $GnupgHome (gpg: $GpgPath)"
foreach ($name in $Files) { if (Test-Path -LiteralPath (Join-Path $MediaDir $name)) { throw "already exists: $name" } }
if (Test-Path -LiteralPath $GnupgHome) { throw "the key ring folder already exists: $GnupgHome" }
if (-not (Test-Path -LiteralPath $GpgPath -PathType Leaf)) { throw "gpg not found: $GpgPath" }
if (-not $Apply) { Write-Output 'Preview only. Run with -Apply to download and verify.'; exit 0 }

. (Join-Path $PSScriptRoot 'RefuteMedia.Core.ps1')

function Invoke-Checked {
    # Runs an external program and stops on a non-zero exit code. Inside this function
    # stderr text is collected, not raised: gpg writes its progress to stderr, and
    # Windows PowerShell 5.1 would otherwise stop on the first such line. The exit code
    # decides.
    param([string]$File, [string[]]$Arguments)
    $ErrorActionPreference = 'Continue'
    $output = & $File @Arguments 2>&1
    $code = $LASTEXITCODE
    $text = @($output | ForEach-Object { [string]$_ })
    if ($code -ne 0) { throw "$([System.IO.Path]::GetFileName($File)) failed with exit code $code`n$($text -join "`n")" }
    return $text
}

[void][System.IO.Directory]::CreateDirectory($MediaDir)
$retrieved = [DateTime]::UtcNow.ToString('yyyy-MM-ddTHH:mm:ssZ')
foreach ($name in $Files) {
    Invoke-Checked $Curl @('--fail', '--location', '--proto', '=https', '--silent', '--show-error',
        '--output', (Join-Path $MediaDir $name), ($BaseUrl + $name)) | Out-Null
}

[void][System.IO.Directory]::CreateDirectory($GnupgHome)
$ringDir = $GnupgHome.Replace('\', '/')
Invoke-Checked $GpgPath @('--homedir', $ringDir, '--batch', '--keyserver', $Keyserver, '--recv-keys', $Fingerprint) | Out-Null
$colons = Invoke-Checked $GpgPath @('--homedir', $ringDir, '--batch', '--with-colons', '--fingerprint', $Fingerprint)
$fprs = @($colons | Where-Object { $_.StartsWith('fpr:') } | ForEach-Object { $_.Split(':')[9] })
if ($fprs.Count -lt 1 -or $fprs[0] -cne $Fingerprint) { throw "the imported key's fingerprint is not $Fingerprint" }

$sums = (Join-Path $MediaDir 'SHA256SUMS').Replace('\', '/')
$status = Invoke-Checked $GpgPath @('--homedir', $ringDir, '--batch', '--status-fd', '1', '--verify', "$sums.gpg", $sums)
$validsig = Test-RefuteGpgStatus -Lines $status -Fingerprint $Fingerprint
$expected = Get-RefuteSumsHash -Lines ([System.IO.File]::ReadAllLines((Join-Path $MediaDir 'SHA256SUMS'))) -Name $IsoName
$actual = (Get-FileHash -LiteralPath (Join-Path $MediaDir $IsoName) -Algorithm SHA256).Hash.ToLowerInvariant()
if ($actual -cne $expected) { throw "the ISO's SHA-256 $actual differs from SHA256SUMS ($expected)" }

$evidence = [ordered]@{
    RetrievedUtc       = $retrieved
    BaseUrl            = $BaseUrl
    Fingerprint        = $Fingerprint
    ValidSig           = $validsig
    GpgVersion         = (Invoke-Checked $GpgPath @('--version'))[0]
    Sha256SumsSha256   = (Get-FileHash -LiteralPath (Join-Path $MediaDir 'SHA256SUMS') -Algorithm SHA256).Hash.ToLowerInvariant()
    SignatureSha256    = (Get-FileHash -LiteralPath (Join-Path $MediaDir 'SHA256SUMS.gpg') -Algorithm SHA256).Hash.ToLowerInvariant()
    IsoName            = $IsoName
    IsoSha256          = $actual
}
$utf8 = New-Object System.Text.UTF8Encoding($false)
[System.IO.File]::WriteAllText((Join-Path $MediaDir 'media-verification.json'), (ConvertTo-Json $evidence), $utf8)
Write-Output (ConvertTo-Json $evidence)
