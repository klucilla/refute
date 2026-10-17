# Pure decisions of the media verification (Get-RefuteMedia.ps1) and of the seed key
# (New-RefuteSeedIso.ps1), kept apart so tests/vm/vm_cases.ps1 checks them on synthetic
# inputs. Windows PowerShell 5.1 and PowerShell 7.

Set-StrictMode -Version 2.0

function Test-RefuteGpgStatus {
    # From the lines of `gpg --status-fd 1 --verify`, the single VALIDSIG line whose
    # primary-key fingerprint (its last field) is the expected one; a signature by a
    # subkey of that key is accepted, any other key is refused. Requires one GOODSIG.
    param([string[]]$Lines, [string]$Fingerprint)
    $valid = @($Lines | Where-Object { $_ -like '`[GNUPG:`] VALIDSIG *' })
    if ($valid.Count -ne 1) { throw "expected one VALIDSIG line, found $($valid.Count)" }
    $fields = $valid[0].Split(' ')
    if ($fields[-1] -cne $Fingerprint) { throw "signed by another primary key: $($fields[-1])" }
    $good = @($Lines | Where-Object { $_ -like '`[GNUPG:`] GOODSIG *' })
    if ($good.Count -ne 1) { throw "expected one GOODSIG line, found $($good.Count)" }
    foreach ($bad in 'BADSIG', 'ERRSIG', 'EXPSIG', 'EXPKEYSIG', 'REVKEYSIG', 'NO_PUBKEY') {
        if (@($Lines | Where-Object { $_ -like "``[GNUPG:``] $bad *" }).Count) { throw "gpg reported $bad" }
    }
    return $valid[0]
}

function Test-RefuteKeyListing {
    # From the lines of `gpg --with-colons --import-options show-only --import <key file>`,
    # the key file holds exactly one primary key ("pub"), whose fingerprint (the first
    # "fpr" line after it, field 10) is the expected one. gpgv trusts every key of its
    # keyring, so the keyring must hold that key only (#59, Codex review).
    param([string[]]$Lines, [string]$Fingerprint)
    $pubs = @($Lines | Where-Object { $_.StartsWith('pub:') })
    if ($pubs.Count -ne 1) { throw "expected one primary key in the key file, found $($pubs.Count)" }
    $seenPub = $false
    foreach ($line in $Lines) {
        if ($line.StartsWith('pub:')) { $seenPub = $true; continue }
        if ($seenPub -and $line.StartsWith('fpr:')) {
            $fpr = $line.Split(':')[9]
            if ($fpr -cne $Fingerprint) { throw "the key file's primary key is $fpr, not $Fingerprint" }
            return $fpr
        }
    }
    throw 'the key file lists no fingerprint for its primary key'
}

function Test-RefuteKeyPackets {
    # From the lines of `gpg --list-packets <keyring>`: exactly one public key packet (a
    # primary key; subkeys are "public sub key" packets), so the keyring gpgv reads holds one
    # primary key, whatever the listing of the import showed (#59, Codex review of #154).
    # Returns the number of packets listed.
    param([string[]]$Lines)
    $primary = @($Lines | Where-Object { $_.StartsWith(':public key packet:') })
    if ($primary.Count -ne 1) { throw "expected one public key packet in the keyring, found $($primary.Count)" }
    return @($Lines | Where-Object { $_.StartsWith(':') }).Count
}

function Get-RefuteSumsHash {
    # The SHA-256 of Name in the lines of a SHA256SUMS file: exactly one line
    # "<64 hex> <space or *><Name>".
    param([string[]]$Lines, [string]$Name)
    $found = @()
    foreach ($line in $Lines) {
        if ($line.Length -lt 67) { continue }
        $hash = $line.Substring(0, 64)
        $sep = $line.Substring(64, 2)
        $file = $line.Substring(66)
        if ($hash -cmatch '^[0-9a-f]{64}$' -and ($sep -ceq ' *' -or $sep -ceq '  ') -and $file -ceq $Name) { $found += $hash }
    }
    if ($found.Count -ne 1) { throw "expected one line for $Name in SHA256SUMS, found $($found.Count)" }
    return $found[0]
}

function ConvertTo-RefuteMsysPath {
    # An absolute Windows path on a drive ("C:\a\b") in the form the MSYS programs of Git
    # for Windows (gpg) read when started from PowerShell ("/c/a/b"). Started outside an
    # MSYS shell, they get no automatic path conversion, and "C:/a/b" is read as a
    # relative path. Refuses relative, UNC and ".." paths.
    param([string]$Path)
    if ($Path -cnotmatch '^[A-Za-z]:\\' -or $Path.Contains('..') -or $Path.Contains('/')) {
        throw "not an absolute Windows path on a drive: $Path"
    }
    $rest = $Path.Substring(3).TrimEnd('\').Replace('\', '/')
    $drive = '/' + $Path.Substring(0, 1).ToLowerInvariant()
    if ($rest) { return "$drive/$rest" }
    return $drive
}

function ConvertTo-RefuteVmPublicKey {
    # "ssh-ed25519 <base64> [comment]" -> "ssh-ed25519 <base64> refute-vm", after checking
    # the blob: the string "ssh-ed25519" then a 32-byte key (RFC 8709 wire format).
    param([string]$Text)
    $parts = $Text.Trim().Split(' ')
    if ($parts.Count -lt 2 -or $parts[0] -cne 'ssh-ed25519') { throw 'the public key must be one ssh-ed25519 key' }
    try { $blob = [System.Convert]::FromBase64String($parts[1]) } catch { throw 'the public key is not valid base64' }
    $type = [System.Text.Encoding]::ASCII.GetBytes('ssh-ed25519')
    if ($blob.Length -ne 4 + $type.Length + 4 + 32) { throw 'the public key blob does not have the ssh-ed25519 length' }
    $typeLength = ($blob[0] -shl 24) -bor ($blob[1] -shl 16) -bor ($blob[2] -shl 8) -bor $blob[3]
    $keyLength = ($blob[15] -shl 24) -bor ($blob[16] -shl 16) -bor ($blob[17] -shl 8) -bor $blob[18]
    if ($typeLength -ne $type.Length -or $keyLength -ne 32) { throw 'the public key blob is not an ssh-ed25519 key' }
    for ($i = 0; $i -lt $type.Length; $i++) { if ($blob[4 + $i] -ne $type[$i]) { throw 'the public key blob is not an ssh-ed25519 key' } }
    return "ssh-ed25519 $($parts[1]) refute-vm"
}
