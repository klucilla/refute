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

function Find-RefuteBlockOverrides {
    # The names of the enabled inbound rules whose security filter overrides block rules
    # (authenticated bypass). Each entry: Name, Enabled, Direction (from
    # Get-NetFirewallRule) and OverrideBlockRules (from its Get-NetFirewallSecurityFilter).
    param([object[]]$Rules)
    return @($Rules | Where-Object {
            [string]$_.Enabled -eq 'True' -and [string]$_.Direction -eq 'Inbound' -and [bool]$_.OverrideBlockRules
        } | ForEach-Object { [string]$_.Name } | Sort-Object)
}
