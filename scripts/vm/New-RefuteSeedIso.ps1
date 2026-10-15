<#
.SYNOPSIS
Builds the NoCloud seed ISO (volume label CIDATA) of the Refute VM from the templates
in scripts/vm/seed and the VM's own SSH public key. Runs as the maintainer's account;
it needs no administrator or Hyper-V rights and uses only components of Windows
(IMAPI2FS through COM, and the .NET compiler of Windows PowerShell for one small
helper).

.DESCRIPTION
- The public key must be an ssh-ed25519 key; its comment (which may hold a user or host
  name) is replaced by "refute-vm".
- The rendered files (user-data, meta-data) are kept next to the ISO, in
  <OutputPath>.content, as the record of what the ISO holds.
- Nothing is overwritten: the ISO and its content folder must not exist.
- The SHA-256 of the ISO is printed; ImportSeedIso takes that value.
cloud-init NoCloud: a vfat or iso9660 volume labelled CIDATA with user-data and
meta-data in its root (https://docs.cloud-init.io/en/latest/reference/datasources/nocloud.html,
retrieved 2026-10-15).
#>
[CmdletBinding()]
param(
    [string]$PublicKeyPath = 'C:\Projetos\refute\.cache\vm\ssh\refute_vm_ed25519.pub',
    [string]$OutputPath = 'C:\Projetos\refute\.cache\vm\media\refute-vm-seed.iso'
)
$ErrorActionPreference = 'Stop'
Set-StrictMode -Version 2.0

$templates = Join-Path $PSScriptRoot 'seed'
$contentDir = "$OutputPath.content"
if (Test-Path -LiteralPath $OutputPath) { throw "the ISO already exists: $OutputPath" }
if (Test-Path -LiteralPath $contentDir) { throw "the content folder already exists: $contentDir" }
if (-not (Test-Path -LiteralPath (Split-Path -Parent $OutputPath) -PathType Container)) { throw 'the output folder does not exist' }

. (Join-Path $PSScriptRoot 'RefuteMedia.Core.ps1')
$keyText = [System.IO.File]::ReadAllText($PublicKeyPath)
if ($keyText.Trim().Contains("`n")) { throw 'the public key file must hold one key' }
$key = ConvertTo-RefuteVmPublicKey $keyText

function Get-RefuteSeedFile {
    param([string]$Name, [string]$Key)
    $text = [System.IO.File]::ReadAllText((Join-Path $templates "$Name.template")).Replace("`r`n", "`n")
    if ($Name -eq 'user-data') {
        $parts = $text.Split(@('{{SSH_PUBLIC_KEY}}'), [System.StringSplitOptions]::None)
        if ($parts.Count -ne 2) { throw 'user-data.template must contain {{SSH_PUBLIC_KEY}} exactly once' }
        $text = $parts[0] + $Key + $parts[1]
    }
    if ($text.Contains('{{')) { throw "$Name.template has an unresolved placeholder" }
    return $text
}

[void][System.IO.Directory]::CreateDirectory($contentDir)
$utf8 = New-Object System.Text.UTF8Encoding($false)
foreach ($name in 'user-data', 'meta-data') {
    [System.IO.File]::WriteAllText((Join-Path $contentDir $name), (Get-RefuteSeedFile -Name $name -Key $key), $utf8)
}

if (-not ('RefuteIsoStreamWriter' -as [type])) {
    Add-Type -TypeDefinition @'
using System;
using System.IO;
using System.Runtime.InteropServices;
using System.Runtime.InteropServices.ComTypes;
public static class RefuteIsoStreamWriter {
    public static void Save(object stream, string path) {
        IStream source = (IStream)stream;
        byte[] buffer = new byte[65536];
        IntPtr readPtr = Marshal.AllocHGlobal(sizeof(int));
        try {
            using (FileStream target = new FileStream(path, FileMode.CreateNew, FileAccess.Write)) {
                while (true) {
                    source.Read(buffer, buffer.Length, readPtr);
                    int read = Marshal.ReadInt32(readPtr);
                    if (read <= 0) { break; }
                    target.Write(buffer, 0, read);
                }
            }
        } finally {
            Marshal.FreeHGlobal(readPtr);
        }
    }
}
'@
}

$image = New-Object -ComObject IMAPI2FS.MsftFileSystemImage
$image.FileSystemsToCreate = 3   # ISO 9660 (1) and Joliet (2), so the names keep their case
$image.VolumeName = 'CIDATA'
$image.Root.AddTree($contentDir, $false)
$result = $image.CreateResultImage()
[RefuteIsoStreamWriter]::Save($result.ImageStream, $OutputPath)

$sha = (Get-FileHash -LiteralPath $OutputPath -Algorithm SHA256).Hash.ToLowerInvariant()
Write-Output "seed ISO: $OutputPath"
Write-Output "sha256: $sha"
