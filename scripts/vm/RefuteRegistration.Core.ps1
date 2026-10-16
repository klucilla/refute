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

function ConvertTo-RefuteSpecificRights {
    # An access mask with its generic rights (bits 28 to 31) replaced by the specific file
    # rights they grant, the FILE_GENERIC_* mapping of
    # https://learn.microsoft.com/en-us/windows/win32/fileio/file-security-and-access-rights
    # (accessed 2026-10-16): GENERIC_ALL gives every right; GENERIC_WRITE gives WriteData,
    # AppendData, WriteAttributes, WriteExtendedAttributes, ReadPermissions and Synchronize;
    # GENERIC_READ and GENERIC_EXECUTE give read and execute rights only. Windows can keep
    # an inherit-only entry with GENERIC_ALL or GENERIC_WRITE unmapped, so without this an
    # entry such as (A;OICIIO;GA;;;BU) would not count as a writer (Codex review of the
    # integrated JEA package). Pure.
    param([int]$Rights)
    $r = [System.Security.AccessControl.FileSystemRights]
    $specific = $Rights -band 0x0FFFFFFF
    if ($Rights -band 0x10000000) { $specific = $specific -bor [int]$r::FullControl }
    if ($Rights -band 0x20000000) {
        $specific = $specific -bor [int]($r::ExecuteFile -bor $r::ReadAttributes -bor $r::ReadPermissions -bor $r::Synchronize)
    }
    if ($Rights -band 0x40000000) {
        $specific = $specific -bor [int]($r::WriteData -bor $r::AppendData -bor $r::WriteAttributes -bor
            $r::WriteExtendedAttributes -bor $r::ReadPermissions -bor $r::Synchronize)
    }
    if ($Rights -band 0x80000000) {
        $specific = $specific -bor [int]($r::ReadData -bor $r::ReadAttributes -bor $r::ReadExtendedAttributes -bor
            $r::ReadPermissions -bor $r::Synchronize)
    }
    return [int]$specific
}

function Test-RefuteRightsWrite {
    # True when the rights of one access entry allow any change, generic rights included
    # (ConvertTo-RefuteSpecificRights).
    param([int]$Rights)
    return (((ConvertTo-RefuteSpecificRights $Rights) -band (Get-RefuteWriteRightsMask)) -ne 0)
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

function ConvertTo-RefuteWindowsFullPath {
    # A fully qualified Windows path, normalised with Windows rules written out here, so
    # that the result is the same on every OS (on Linux, .NET's GetFullPath does not know
    # 'C:\' and would prefix the current folder). '/' is read as '\'; the root is a drive
    # ('C:') or a UNC share ('\\server\share'); empty and '.' segments are dropped; '..'
    # removes the previous segment and never goes above the root. A device path
    # ('\\?\', '\\.\'), a segment ending in '.' or ' ' (which Windows would trim), and a
    # character Windows does not accept in a path ('<', '>', '"', '|', '?', '*', a control
    # character, or ':' anywhere but after the drive letter, which would name an alternate
    # data stream) are refused instead of imitated. Pure: no access to the disk.
    param([string]$Path)
    $p = $Path.Replace('/', '\')
    $afterRoot = if ($p -match '^[A-Za-z]:') { $p.Substring(2) } else { $p }
    if ($afterRoot -match '[<>"|?*:\x00-\x1F]' -and -not ($p -match '^\\\\[?.]\\')) {
        throw "the path '$Path' has a character Windows does not accept in a path"
    }
    if ($p -match '^([A-Za-z]:)\\(.*)$') {
        $root = $Matches[1]
        $rest = $Matches[2]
    } elseif ($p -match '^(\\\\([^\\]+)\\([^\\]+))(.*)$') {
        if ($Matches[2] -eq '?' -or $Matches[2] -eq '.') {
            throw "the path '$Path' is a device path"
        }
        $root = $Matches[1]
        $rest = $Matches[4]
    } else {
        throw "the path '$Path' is not a fully qualified path"
    }
    $parts = @()
    foreach ($segment in $rest.Split('\')) {
        if ($segment -eq '' -or $segment -eq '.') { continue }
        if ($segment -eq '..') {
            if ($parts.Count -le 1) { $parts = @() } else { $parts = @($parts[0..($parts.Count - 2)]) }
            continue
        }
        if ($segment.EndsWith('.') -or $segment.EndsWith(' ')) {
            throw "the path '$Path' has a segment ending in '.' or ' '"
        }
        $parts += $segment
    }
    if ($parts.Count -eq 0) { return $root + '\' }
    return $root + '\' + ($parts -join '\')
}

function ConvertTo-RefuteModuleRoot {
    # One module path entry as a root, with its meaning kept: the final '\' characters are
    # removed, and a volume root keeps one ('C:\' and 'C:\\' give 'C:\'; 'C:' would mean
    # the current folder of drive C). Only fully qualified paths are accepted (a drive
    # letter and '\', or a UNC path '\\server\share'); a relative or drive-relative entry
    # ('Modules', 'C:Modules') would depend on each process's current folder, so it is
    # refused (Codex review of #102). '/' is read as '\', and '.', '..' and repeated
    # separators are normalised by ConvertTo-RefuteWindowsFullPath, with no access to the
    # disk and the same result on every OS (Codex review of #114).
    param([string]$Entry)
    $e = $Entry.Replace('/', '\')
    if ($e -notmatch '^([A-Za-z]:\\|\\\\[^\\]+\\[^\\]+)') {
        throw "the module path entry '$Entry' is not a fully qualified path"
    }
    $root = (ConvertTo-RefuteWindowsFullPath $e).TrimEnd('\')
    if ($root -match '^[A-Za-z]:$') { return $root + '\' }
    return $root
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

function Resolve-RefuteSessionEntry {
    # One module path entry as a JEA session resolves it. A fully qualified entry is a root
    # (ConvertTo-RefuteModuleRoot). A relative entry ('WindowsPowerShell\Modules', the user
    # entry of a virtual account whose Documents path is empty, as the integration test of
    # #99 observed on the CI runner) resolves against the session's current folder,
    # CurrentFolder, which must be fully qualified. A drive-relative ('C:Modules') or
    # root-relative ('\Modules') entry depends on per-drive state no one can read here, so
    # it is refused. The entry is joined to the folder and normalised with Windows rules
    # (ConvertTo-RefuteWindowsFullPath: '..' never goes above the drive or the UNC share),
    # with no access to the disk and the same result on every OS (Codex review of #114).
    # Pure.
    param([string]$Entry, [string]$CurrentFolder)
    $e = $Entry.Replace('/', '\')
    if ($e -match '^([A-Za-z]:\\|\\\\[^\\]+\\[^\\]+)') { return ConvertTo-RefuteModuleRoot $e }
    if ($e -match '^[A-Za-z]:' -or $e.StartsWith('\')) {
        throw "the module path entry '$Entry' is drive-relative or root-relative"
    }
    $base = ConvertTo-RefuteModuleRoot $CurrentFolder
    return ConvertTo-RefuteModuleRoot ($base.TrimEnd('\') + '\' + $e)
}

function Join-RefuteDiscoveryRoots {
    # The folders where a JEA session discovers role capabilities: every entry of the given
    # PSModulePath values and every extra folder (fully qualified), and every relative entry
    # resolved against the session's current folder (Resolve-RefuteSessionEntry); without
    # repeats (compared without case), sorted. Folders that do not exist are kept: the
    # caller checks who could create them. Pure.
    param([string[]]$PathValues, [string[]]$Extra, [string[]]$RelativeEntries, [string]$CurrentFolder)
    $roots = @(Join-RefuteModuleRoots -PathValues $PathValues -Extra $Extra)
    foreach ($entry in @($RelativeEntries)) {
        if ($entry) { $roots += Resolve-RefuteSessionEntry -Entry $entry -CurrentFolder $CurrentFolder }
    }
    $seen = @{}
    $out = @()
    foreach ($root in $roots) {
        if ($seen.ContainsKey($root.ToLowerInvariant())) { continue }
        $seen[$root.ToLowerInvariant()] = $true
        $out += $root
    }
    return @($out | Sort-Object)
}

function Get-RefuteJeaDiscoveryRoots {
    # The effective discovery set of the RefuteVm session on this machine (the maintainer's
    # item 9, 2026-10-16): the machine PSModulePath, Program Files\WindowsPowerShell\Modules
    # and $PSHOME\Modules (PowerShell adds both), and the virtual account's user entry, which
    # is relative ('WindowsPowerShell\Modules') because its Documents path is empty, resolved
    # against the session's current folder, %SystemRoot%\system32 (observed on the CI runner
    # by the integration test of #99). Existing folders or not.
    $extra = @(
        (Join-Path $env:ProgramFiles 'WindowsPowerShell\Modules'),
        (Join-Path $PSHOME 'Modules')
    )
    return @(Join-RefuteDiscoveryRoots -PathValues @([Environment]::GetEnvironmentVariable('PSModulePath', 'Machine')) `
            -Extra $extra -RelativeEntries @('WindowsPowerShell\Modules') -CurrentFolder (Join-Path $env:SystemRoot 'system32'))
}

function Test-RefuteAllowedWriter {
    # Whether an allow entry that grants a change is acceptable on a folder or file of the
    # discovery set: SYSTEM, Administrators or TrustedInstaller; CREATOR OWNER only as an
    # inherit-only entry (it then applies to what someone who could already write creates).
    param([string]$Sid, [bool]$InheritOnly)
    if (@('S-1-5-18', 'S-1-5-32-544', 'S-1-5-80-956008885-3418522649-1831038044-1853292631-2271478464') -contains $Sid) { return $true }
    return ($Sid -eq 'S-1-3-0' -and $InheritOnly)
}

function Get-RefuteAceWriters {
    # From access entries (Sid, Rights as an integer, Type 'Allow' or 'Deny', InheritOnly),
    # the ones that grant a change to an account the discovery set must not let write
    # (Test-RefuteAllowedWriter), as "<sid> <rights>". Pure.
    param([object[]]$Entries)
    return @($Entries | Where-Object {
            [string]$_.Type -eq 'Allow' -and (Test-RefuteRightsWrite ([int]$_.Rights)) -and
            -not (Test-RefuteAllowedWriter -Sid ([string]$_.Sid) -InheritOnly ([bool]$_.InheritOnly))
        } | ForEach-Object { "$($_.Sid) $([int]$_.Rights)" })
}

function Test-RefuteAllowedOwner {
    # The owner of a folder or file of the discovery set, or of one of its ancestors, must
    # be SYSTEM, Administrators or TrustedInstaller: an owner has an implicit right to
    # change the DACL, so a DACL without its writers does not protect an item another
    # account owns (Codex review of #114).
    param([string]$Sid)
    return (@('S-1-5-18', 'S-1-5-32-544', 'S-1-5-80-956008885-3418522649-1831038044-1853292631-2271478464') -contains $Sid)
}

function Get-RefuteAncestorWriters {
    # From the access entries of an ANCESTOR of a discovery folder, the ones that let
    # another account replace or redirect what is below it: delete it or its children,
    # change its permissions or take its ownership. Creating a new child (WriteData,
    # AppendData) does not replace an existing one, and an inherit-only entry does not
    # apply to the ancestor itself, so neither counts. Pure.
    param([object[]]$Entries)
    $rights = [System.Security.AccessControl.FileSystemRights]
    $mask = [int]($rights::Delete -bor $rights::DeleteSubdirectoriesAndFiles -bor $rights::ChangePermissions -bor $rights::TakeOwnership)
    return @($Entries | Where-Object {
            [string]$_.Type -eq 'Allow' -and -not [bool]$_.InheritOnly -and (((ConvertTo-RefuteSpecificRights ([int]$_.Rights)) -band $mask) -ne 0) -and
            -not (Test-RefuteAllowedWriter -Sid ([string]$_.Sid) -InheritOnly $false)
        } | ForEach-Object { "$($_.Sid) $([int]$_.Rights)" })
}

function Get-RefuteDiscoveryProblems {
    # Reads, never writes. For each folder of the discovery set: when it exists, the owner
    # and the access entries of the folder, of every folder directly under it (a writer
    # there could add <folder>\RoleCapabilities), of every existing <folder>\RoleCapabilities
    # and of the .psrc files in it; when it does not exist, those of its nearest existing
    # ancestor (whoever may create it could add role capabilities). Every ancestor of an
    # existing folder, up to its volume root, is checked too: no reparse point (a link or
    # junction could redirect the path), an allowed owner, and no entry that lets another
    # account replace what is below it; for a folder that does not exist, the ancestors
    # above its nearest existing one are checked the same way. Any item that is a reparse
    # point is refused.
    # Returns one problem per finding, and one per item that cannot be read.
    param([string[]]$Roots)
    $problems = @()
    foreach ($root in @($Roots)) {
        $targets = @()
        $ancestors = @()
        try {
            if (Test-Path -LiteralPath $root -PathType Container -ErrorAction Stop) {
                $targets += $root
                foreach ($dir in @(Get-ChildItem -LiteralPath $root -Directory -Force -ErrorAction Stop)) {
                    $targets += $dir.FullName
                    $rc = Join-Path $dir.FullName 'RoleCapabilities'
                    if (Test-Path -LiteralPath $rc -PathType Container -ErrorAction Stop) {
                        $targets += $rc
                        $targets += @(Get-ChildItem -LiteralPath $rc -File -Force -Filter '*.psrc' -ErrorAction Stop | ForEach-Object { $_.FullName })
                    }
                }
                $ancestor = Split-Path -Parent $root
                while ($ancestor) {
                    $ancestors += $ancestor
                    $ancestor = Split-Path -Parent $ancestor
                }
            } else {
                $ancestor = Split-Path -Parent $root
                while ($ancestor -and -not (Test-Path -LiteralPath $ancestor -PathType Container -ErrorAction Stop)) {
                    $ancestor = Split-Path -Parent $ancestor
                }
                if ($ancestor) {
                    # the nearest existing ancestor gets the full check (whoever may write
                    # in it can create the folder), and every folder above it, up to the
                    # volume root, the ancestor rules (Codex review of #114, round 2)
                    $targets += $ancestor
                    $above = Split-Path -Parent $ancestor
                    while ($above) {
                        $ancestors += $above
                        $above = Split-Path -Parent $above
                    }
                }
            }
        } catch {
            $problems += "$root cannot be read: $($_.Exception.Message)"
            continue
        }
        foreach ($item in @($targets) + @($ancestors)) {
            $problems += @(Get-RefuteItemProblems -Item $item -IsAncestor ($ancestors -contains $item))
        }
    }
    return $problems  # callers wrap the call in @(...)
}

function Get-RefuteTreeProblems {
    # Reads, never writes. For each folder of Roots (the folders a role capability's imports
    # load from: the module folders and the folder of an assembly a manifest loads): the
    # folder and every file and folder below it get the full check of Get-RefuteItemProblems,
    # and every ancestor up to the volume root the ancestor check, so that no other account
    # can change, replace or redirect what the imports load (Codex review of #118). A
    # missing folder is a problem. Returns one problem per finding.
    param([string[]]$Roots)
    $problems = @()
    foreach ($root in @($Roots)) {
        $targets = @()
        $ancestors = @()
        try {
            if (-not (Test-Path -LiteralPath $root -PathType Container -ErrorAction Stop)) {
                $problems += "$root does not exist"
                continue
            }
            $targets += $root
            $targets += @(Get-ChildItem -LiteralPath $root -Recurse -Force -ErrorAction Stop | ForEach-Object { $_.FullName })
            $ancestor = Split-Path -Parent $root
            while ($ancestor) {
                $ancestors += $ancestor
                $ancestor = Split-Path -Parent $ancestor
            }
        } catch {
            $problems += "$root cannot be read: $($_.Exception.Message)"
            continue
        }
        foreach ($item in $targets) { $problems += @(Get-RefuteItemProblems -Item $item -IsAncestor $false) }
        foreach ($item in $ancestors) { $problems += @(Get-RefuteItemProblems -Item $item -IsAncestor $true) }
    }
    return $problems  # callers wrap the call in @(...)
}

function ConvertTo-RefuteAclEntries {
    # The owner and the access entries of a security object (from Get-Acl), by the SIDs
    # stored in its security descriptor: GetOwner and GetAccessRules with the
    # SecurityIdentifier type. An account name is never translated back to a SID and never
    # compared: translating the name of ALL APPLICATION PACKAGES (S-1-15-2-1) failed on a
    # Portuguese Windows (measured on 2026-10-16), and a localized name differs from host to
    # host. Pure: it reads only the object it is given. Returns Owner (a SID) and Entries
    # (Sid, Rights as an integer, Type 'Allow' or 'Deny', InheritOnly).
    param([object]$Acl)
    $entries = @($Acl.GetAccessRules($true, $true, [System.Security.Principal.SecurityIdentifier]) | ForEach-Object {
            [ordered]@{
                Sid         = [string]$_.IdentityReference.Value
                Rights      = [int]$_.FileSystemRights
                Type        = [string]$_.AccessControlType
                InheritOnly = ([string]$_.PropagationFlags -match 'InheritOnly')
            }
        })
    return [ordered]@{ Owner = [string]$Acl.GetOwner([System.Security.Principal.SecurityIdentifier]).Value; Entries = $entries }
}

function Get-RefuteItemProblems {
    # Reads, never writes. The checks of one file or folder: not a reparse point, an allowed
    # owner, and no access entry that lets another account write it (for an ancestor: that
    # lets another account replace or redirect what is below it). Returns one problem per
    # finding, or one when the item cannot be read.
    param([string]$Item, [bool]$IsAncestor)
    $problems = @()
    try {
        $info = Get-Item -LiteralPath $Item -Force -ErrorAction Stop
        if (([int]$info.Attributes -band [int][System.IO.FileAttributes]::ReparsePoint) -ne 0) {
            return @("$Item is a reparse point (a link or junction)")
        }
        $acl = ConvertTo-RefuteAclEntries (Get-Acl -LiteralPath $Item -ErrorAction Stop)
    } catch {
        return @("$Item cannot be read: $($_.Exception.Message)")
    }
    if (-not (Test-RefuteAllowedOwner $acl.Owner)) { $problems += "$Item is owned by $($acl.Owner)" }
    if ($IsAncestor) {
        foreach ($w in @(Get-RefuteAncestorWriters $acl.Entries)) { $problems += "$Item (an ancestor) can be changed by $w" }
    } else {
        foreach ($w in @(Get-RefuteAceWriters $acl.Entries)) { $problems += "$Item can be written by $w" }
    }
    return $problems  # callers wrap the call in @(...)
}

function Get-RefuteRegistrationModuleRoots {
    # The module folder roots the registration searches for role capability copies (the
    # registration script and the JEA integration test, tests/vm/jea_integration.ps1, call
    # this same function): the machine and this process's PSModulePath, Program Files,
    # System32, $PSHOME\Modules, and the user module folder of the Default profile
    # (<Default>\Documents\WindowsPowerShell\Modules). A JEA virtual account gets a new
    # profile, created from the Default profile when its session starts, so its own user
    # module folder does not exist at registration; what it can hold comes from there.
    # It also holds every folder of the effective discovery set (Get-RefuteJeaDiscoveryRoots),
    # including the relative user entry resolved against the session's current folder.
    # Only existing folders are returned.
    $default = (Get-ItemProperty -LiteralPath 'HKLM:\SOFTWARE\Microsoft\Windows NT\CurrentVersion\ProfileList' -Name Default).Default
    $extra = @(
        (Join-Path $env:ProgramFiles 'WindowsPowerShell\Modules'),
        (Join-Path $env:SystemRoot 'System32\WindowsPowerShell\v1.0\Modules'),
        (Join-Path $PSHOME 'Modules'),
        (Join-Path ([Environment]::ExpandEnvironmentVariables($default)) 'Documents\WindowsPowerShell\Modules')
    ) + @(Get-RefuteJeaDiscoveryRoots)
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
