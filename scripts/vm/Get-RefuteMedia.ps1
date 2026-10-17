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
GnuPG is not part of Windows: the gpg and gpgv of Git for Windows, already installed,
are used, with a folder of their own inside the project (.cache/vm/gnupg). curl.exe is
part of Windows. Nothing is overwritten: every destination must not exist. The evidence
goes to .cache/vm/media/media-verification.json; the ISO's SHA-256 then goes into
RefuteVm.Config.psd1 (InstallIsoSha256) in a reviewed change, before the endpoint is
registered.

No GnuPG daemon is started (#59, Codex review; the first run of 2026-10-15 left dirmngr
and gpg-agent running). The key is fetched over HTTPS by curl from the keyserver's HKP
lookup ("get" with options "mr": https://datatracker.ietf.org/doc/html/draft-shaw-openpgp-hkp-00,
section 3), not by gpg --recv-keys, which uses dirmngr. Every gpg call has --no-autostart
("Do not start the gpg-agent or the dirmngr": the GnuPG manual, GPG Configuration Options,
accessed 2026-10-17); it does not stop a daemon that is already running from answering.

The keyring gpgv reads is the output of gpg's own import processing of the key file
(--import-options import-export: "Run the entire import code but instead of storing the
key to the local keyring write it to the output ... can for example be used to remove all
invalid parts from a key", GPG Input and Output, same date), not a plain --dearmor of it
(Codex review of #154: a listing shows what the import keeps, --dearmor keeps every
packet). That keyring itself is then checked twice: listed with --import-options
show-only, it must hold exactly one primary key, with the expected fingerprint
(Test-RefuteKeyListing); and its packets, listed with --list-packets ("List only the
sequence of packets", Operational GPG Commands, same date; the format "may change with new
releases", so the gpg version is recorded), must hold exactly one public key packet
(Test-RefuteKeyPackets). gpgv "assumes that all keys in the keyring are trustworthy" (the
gpgv page of the same manual), which is why the keyring must hold that key only.
#>
[CmdletBinding()]
param(
    [switch]$Apply,
    [string]$GpgPath = 'C:\Program Files\Git\usr\bin\gpg.exe',
    [string]$GpgvPath = 'C:\Program Files\Git\usr\bin\gpgv.exe'
)
$ErrorActionPreference = 'Stop'
Set-StrictMode -Version 2.0

$BaseUrl = 'https://releases.ubuntu.com/26.04/'
$IsoName = 'ubuntu-26.04.1-live-server-amd64.iso'
$Fingerprint = '843938DF228D22F7B3742BC0D94AA3F0EFE21092'
$KeyUrl = "https://keyserver.ubuntu.com/pks/lookup?op=get&options=mr&search=0x$Fingerprint"
$MediaDir = 'C:\Projetos\refute\.cache\vm\media'
$GnupgHome = 'C:\Projetos\refute\.cache\vm\gnupg'
$KeyFile = Join-Path $GnupgHome 'ubuntu-cdimage-key.asc'
$Keyring = Join-Path $GnupgHome 'ubuntu-cdimage-keyring.gpg'
$Curl = Join-Path $env:SystemRoot 'System32\curl.exe'
$Files = @('SHA256SUMS', 'SHA256SUMS.gpg', $IsoName)

Write-Output "Download from $BaseUrl : $($Files -join ', ') -> $MediaDir"
Write-Output "Key: $Fingerprint from $KeyUrl into $KeyFile, keyring $Keyring (gpg: $GpgPath; gpgv: $GpgvPath; no daemon)"
foreach ($name in $Files) { if (Test-Path -LiteralPath (Join-Path $MediaDir $name)) { throw "already exists: $name" } }
if (Test-Path -LiteralPath $GnupgHome) { throw "the key ring folder already exists: $GnupgHome" }
if (-not (Test-Path -LiteralPath $GpgPath -PathType Leaf)) { throw "gpg not found: $GpgPath" }
if (-not (Test-Path -LiteralPath $GpgvPath -PathType Leaf)) { throw "gpgv not found: $GpgvPath" }
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
$ringDir = ConvertTo-RefuteMsysPath $GnupgHome
# the key over HTTPS, without dirmngr; the listing and the conversion start no daemon
Invoke-Checked $Curl @('--fail', '--location', '--proto', '=https', '--silent', '--show-error',
    '--output', $KeyFile, $KeyUrl) | Out-Null
$keyPath = ConvertTo-RefuteMsysPath $KeyFile
$ringPath = ConvertTo-RefuteMsysPath $Keyring
# the keyring is what gpg's import processing keeps of the key file; nothing is stored
Invoke-Checked $GpgPath @('--homedir', $ringDir, '--no-autostart', '--batch', '--import-options', 'import-export',
    '--output', $ringPath, '--import', $keyPath) | Out-Null
# the keyring gpgv will read, checked as it is: one primary key, the expected one, and one
# public key packet
$listing = Invoke-Checked $GpgPath @('--homedir', $ringDir, '--no-autostart', '--batch', '--with-colons',
    '--import-options', 'show-only', '--import', $ringPath)
Test-RefuteKeyListing -Lines $listing -Fingerprint $Fingerprint | Out-Null
$packets = Invoke-Checked $GpgPath @('--homedir', $ringDir, '--no-autostart', '--batch', '--list-packets', $ringPath)
Test-RefuteKeyPackets -Lines $packets | Out-Null

$sums = ConvertTo-RefuteMsysPath (Join-Path $MediaDir 'SHA256SUMS')
$status = Invoke-Checked $GpgvPath @('--homedir', $ringDir, '--keyring', $ringPath, '--status-fd', '1', "$sums.gpg", $sums)
$validsig = Test-RefuteGpgStatus -Lines $status -Fingerprint $Fingerprint
$expected = Get-RefuteSumsHash -Lines ([System.IO.File]::ReadAllLines((Join-Path $MediaDir 'SHA256SUMS'))) -Name $IsoName
$actual = (Get-FileHash -LiteralPath (Join-Path $MediaDir $IsoName) -Algorithm SHA256).Hash.ToLowerInvariant()
if ($actual -cne $expected) { throw "the ISO's SHA-256 $actual differs from SHA256SUMS ($expected)" }

$evidence = [ordered]@{
    RetrievedUtc       = $retrieved
    BaseUrl            = $BaseUrl
    Fingerprint        = $Fingerprint
    ValidSig           = $validsig
    # @(...): one line of output would otherwise come back as a string, and [0] its first character
    GpgVersion         = @(Invoke-Checked $GpgPath @('--version'))[0]
    GpgvVersion        = @(Invoke-Checked $GpgvPath @('--version'))[0]
    KeyUrl             = $KeyUrl
    KeyFileSha256      = (Get-FileHash -LiteralPath $KeyFile -Algorithm SHA256).Hash.ToLowerInvariant()
    KeyringSha256      = (Get-FileHash -LiteralPath $Keyring -Algorithm SHA256).Hash.ToLowerInvariant()
    KeyringPackets     = @($packets | Where-Object { $_.StartsWith(':') })
    Sha256SumsSha256   = (Get-FileHash -LiteralPath (Join-Path $MediaDir 'SHA256SUMS') -Algorithm SHA256).Hash.ToLowerInvariant()
    SignatureSha256    = (Get-FileHash -LiteralPath (Join-Path $MediaDir 'SHA256SUMS.gpg') -Algorithm SHA256).Hash.ToLowerInvariant()
    IsoName            = $IsoName
    IsoSha256          = $actual
}
$utf8 = New-Object System.Text.UTF8Encoding($false)
[System.IO.File]::WriteAllText((Join-Path $MediaDir 'media-verification.json'), (ConvertTo-Json $evidence), $utf8)
Write-Output (ConvertTo-Json $evidence)
