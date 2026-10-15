# Pure decisions of Register-RefuteVmEndpoint.ps1, kept apart so tests/vm/vm_cases.ps1
# checks them on synthetic inputs. Windows PowerShell 5.1 and PowerShell 7.

Set-StrictMode -Version 2.0

function Get-RefuteWriteRightsMask {
    # Only the rights that change a file or folder, or its permissions or owner. The
    # composite rights (Modify, FullControl) also contain read bits, so they are never
    # used as a mask: a read-only entry must not count as a writer.
    $rights = [System.Security.AccessControl.FileSystemRights]
    return [int]($rights::WriteData -bor $rights::AppendData -bor $rights::WriteExtendedAttributes -bor
        $rights::WriteAttributes -bor $rights::DeleteSubdirectoriesAndFiles -bor $rights::Delete -bor
        $rights::ChangePermissions -bor $rights::TakeOwnership)
}

function Test-RefuteRightsWrite {
    # True when the rights of one access entry allow any change.
    param([int]$Rights)
    return (($Rights -band (Get-RefuteWriteRightsMask)) -ne 0)
}

function Find-RefuteHyperVManifest {
    # The Hyper-V module manifest under ModuleFolder, found by reading the folder only (no
    # module discovery, which could write the module analysis cache). Version subfolders
    # (Hyper-V\<version>\Hyper-V.psd1, as on Windows 10 and 11) are preferred, the highest
    # version first: the version Import-Module uses when no version is asked for. A
    # manifest directly in ModuleFolder (the older layout) is the fallback. Returns the
    # path, or $null when there is none.
    param([string]$ModuleFolder)
    if (-not (Test-Path -LiteralPath $ModuleFolder -PathType Container)) { return $null }
    $versions = @()
    foreach ($dir in @(Get-ChildItem -LiteralPath $ModuleFolder -Directory -Force)) {
        $parsed = $null
        if ([System.Version]::TryParse($dir.Name, [ref]$parsed) -and
            (Test-Path -LiteralPath (Join-Path $dir.FullName 'Hyper-V.psd1') -PathType Leaf)) {
            $versions += , @($parsed, (Join-Path $dir.FullName 'Hyper-V.psd1'))
        }
    }
    if ($versions.Count) {
        return @($versions | Sort-Object { $_[0] } -Descending)[0][1]
    }
    $flat = Join-Path $ModuleFolder 'Hyper-V.psd1'
    if (Test-Path -LiteralPath $flat -PathType Leaf) { return $flat }
    return $null
}

function Get-RefuteListenerRemoval {
    # What removing the listener key Target leaves, from the names of every key under
    # WSMAN\Listener ("<address>+<transport>", for example "*+HTTP" or "IP:127.0.0.1+HTTP").
    # Only HTTP listeners on 127.0.0.1 or ::1 are allowed to remain.
    param([string[]]$Names, [string]$Target)
    $loopback = @('IP:127.0.0.1', 'IP:::1')
    $all = @($Names | Where-Object { $_ })
    $remaining = @($all | Where-Object { $_ -cne $Target })
    $foreign = @($remaining | Where-Object {
            $cut = $_.LastIndexOf('+')
            $address = $_.Substring(0, [Math]::Max($cut, 0))
            $transport = $_.Substring($cut + 1)
            $loopback -notcontains $address -or $transport -ne 'HTTP'
        })
    return [ordered]@{
        TargetPresent    = ($all -ccontains $Target)
        Remaining        = $remaining
        ForeignRemaining = $foreign
    }
}

function Test-RefuteRegExport {
    # True when the text of a .reg export holds exactly the header of KeyPath (for example
    # "HKEY_LOCAL_MACHINE\SOFTWARE\...\Listener\*+HTTP") and no other key header outside it.
    param([string]$Text, [string]$KeyPath)
    $headers = @($Text -split "`r?`n" | Where-Object { $_.StartsWith('[') -and $_.EndsWith(']') } |
            ForEach-Object { $_.Substring(1, $_.Length - 2) })
    if (@($headers | Where-Object { $_ -ceq $KeyPath }).Count -ne 1) { return $false }
    return (@($headers | Where-Object { $_ -cne $KeyPath -and -not $_.StartsWith("$KeyPath\") }).Count -eq 0)
}

function Find-RefuteBlockOverrides {
    # The names of the enabled inbound rules whose security filter overrides block rules
    # (authenticated bypass). Each entry: Name, Enabled, Direction (from
    # Get-NetFirewallRule) and OverrideBlockRules (from its Get-NetFirewallSecurityFilter).
    param([object[]]$Rules)
    return @($Rules | Where-Object {
            [string]$_.Enabled -eq 'True' -and [string]$_.Direction -eq 'Inbound' -and [bool]$_.OverrideBlockRules
        } | ForEach-Object { [string]$_.Name } | Sort-Object)
}
