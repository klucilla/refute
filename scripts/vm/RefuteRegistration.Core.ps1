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

function Find-RefuteJeaRoleCapability {
    # The role capability files JEA can load for RoleName, with the structure of the search
    # JEA makes: for each module folder root, each folder directly under it, then
    # <root>\<folder>\RoleCapabilities\<RoleName>.psrc; JEA takes the first one found
    # (GetRoleCapabilityPath in
    # https://github.com/PowerShell/PowerShell/blob/master/src/System.Management.Automation/engine/remoting/fanin/InitialSessionStateProvider.cs,
    # accessed 2026-10-16). Unlike JEA, it returns every match (folders sorted by name), so
    # that the caller can require a single one over the roots it is given
    # (Get-RefuteRegistrationModuleRoots). A copy in a version subfolder
    # (<folder>\<version>\RoleCapabilities) is never found by this search. Read-only.
    param([string[]]$ModuleRoots, [string]$RoleName)
    $found = @()
    foreach ($root in $ModuleRoots) {
        if (-not (Test-Path -LiteralPath $root -PathType Container)) { continue }
        foreach ($dir in @(Get-ChildItem -LiteralPath $root -Directory -Force | Sort-Object Name)) {
            $file = Join-Path (Join-Path $dir.FullName 'RoleCapabilities') "$RoleName.psrc"
            if (Test-Path -LiteralPath $file -PathType Leaf) { $found += $file }
        }
    }
    return $found  # callers wrap the call in @(...): an empty result arrives as $null
}

function Find-RefuteVersionedRoleCapability {
    # Copies of the role capability one level deeper, in a version subfolder
    # (<root>\<folder>\<version>\RoleCapabilities\<RoleName>.psrc): JEA never loads them, and
    # the registration refuses them so that no stale copy stays next to the one it loads.
    param([string[]]$ModuleRoots, [string]$RoleName)
    $found = @()
    foreach ($root in $ModuleRoots) {
        if (-not (Test-Path -LiteralPath $root -PathType Container)) { continue }
        foreach ($dir in @(Get-ChildItem -LiteralPath $root -Directory -Force | Sort-Object Name)) {
            foreach ($sub in @(Get-ChildItem -LiteralPath $dir.FullName -Directory -Force | Sort-Object Name)) {
                $file = Join-Path (Join-Path $sub.FullName 'RoleCapabilities') "$RoleName.psrc"
                if (Test-Path -LiteralPath $file -PathType Leaf) { $found += $file }
            }
        }
    }
    return $found  # callers wrap the call in @(...)
}

function ConvertTo-RefuteModuleRoot {
    # One module path entry as a root, with its meaning kept: a final '\' is removed except
    # from a volume root ('C:\' stays 'C:\'; 'C:' would mean the current folder of drive
    # C). Only fully qualified paths are accepted (a drive letter and '\', or a UNC path
    # '\\server\share'); a relative or drive-relative entry ('Modules', 'C:Modules') would
    # depend on each process's current folder, so it is refused (Codex review of #102).
    param([string]$Entry)
    if ($Entry -match '^[A-Za-z]:\\$') { return $Entry }
    if ($Entry -notmatch '^([A-Za-z]:\\|\\\\[^\\]+\\[^\\]+)') {
        throw "the module path entry '$Entry' is not a fully qualified path"
    }
    return $Entry.TrimEnd('\')
}

function Join-RefuteModuleRoots {
    # The module folder roots named by the given PSModulePath values (';'-separated) and
    # extra folders, each through ConvertTo-RefuteModuleRoot (a relative entry is refused),
    # without empty entries or repeats (compared without case), sorted. Pure: the caller
    # reads the values.
    param([string[]]$PathValues, [string[]]$Extra)
    $all = @()
    foreach ($value in @($PathValues)) {
        if ($value) { $all += @($value.Split(';')) }
    }
    $all += @($Extra)
    $seen = @{}
    $roots = @()
    foreach ($entry in $all) {
        if (-not $entry) { continue }
        $root = ConvertTo-RefuteModuleRoot $entry
        if ($seen.ContainsKey($root.ToLowerInvariant())) { continue }
        $seen[$root.ToLowerInvariant()] = $true
        $roots += $root
    }
    return @($roots | Sort-Object)
}

function Get-RefuteRegistrationModuleRoots {
    # The module folder roots the registration searches for role capability copies (the
    # registration script and the JEA integration test, tests/vm/jea_integration.ps1, call
    # this same function): the machine and this process's PSModulePath, Program Files,
    # System32, $PSHOME\Modules, and the user module folder of the Default profile
    # (<Default>\Documents\WindowsPowerShell\Modules). A JEA virtual account gets a new
    # profile, created from the Default profile when its session starts, so its own user
    # module folder does not exist at registration; what it can hold comes from there.
    # Only existing folders are returned.
    $default = (Get-ItemProperty -LiteralPath 'HKLM:\SOFTWARE\Microsoft\Windows NT\CurrentVersion\ProfileList' -Name Default).Default
    $extra = @(
        (Join-Path $env:ProgramFiles 'WindowsPowerShell\Modules'),
        (Join-Path $env:SystemRoot 'System32\WindowsPowerShell\v1.0\Modules'),
        (Join-Path $PSHOME 'Modules'),
        (Join-Path ([Environment]::ExpandEnvironmentVariables($default)) 'Documents\WindowsPowerShell\Modules')
    )
    $values = @(
        [Environment]::GetEnvironmentVariable('PSModulePath', 'Machine'),
        [Environment]::GetEnvironmentVariable('PSModulePath', 'Process')
    )
    return @(Join-RefuteModuleRoots -PathValues $values -Extra $extra | Where-Object { Test-Path -LiteralPath $_ -PathType Container })
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
