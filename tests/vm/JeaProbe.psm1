# The probe module of the JEA integration test (tests/vm/jea_integration.ps1 copies it into
# each disposable probe module; tests/vm/vm_cases.ps1 checks Get-RefuteJeaModuleRoots on
# synthetic folders). It uses .NET only: no cmdlet, which a restricted session may not have
# (cause 3 of the maintainer's diagnosis of 2026-10-16).

function Get-RefuteJeaProbe { 'probe-ok' }

function Get-RefuteJeaInspection {
    # The folders (or files) under a path, and how the reading went: 'present', 'absent'
    # (the path does not exist: DirectoryNotFoundException) or 'error' (any other failure,
    # an access denial included). Directory.Exists is not used: it answers false for an
    # access denial too, which would look like an absence (Codex review of #99).
    param([string]$Path, [string]$Pattern, [bool]$Files)
    try {
        if ($Files) { $items = [System.IO.Directory]::GetFiles($Path, $Pattern) }
        else { $items = [System.IO.Directory]::GetDirectories($Path) }
        return @('present', '', $items)
    } catch {
        $ex = $_.Exception
        if ($ex -is [System.Management.Automation.MethodInvocationException] -and $ex.InnerException) { $ex = $ex.InnerException }
        if ($ex -is [System.IO.DirectoryNotFoundException]) { return @('absent', '', @()) }
        $text = ($ex.GetType().FullName + ': ' + $ex.Message).Replace("`t", ' ').Replace("`r", ' ').Replace("`n", ' ')
        return @('error', $text, @())
    }
}

function Get-RefuteJeaModuleRoots {
    # For each entry of this process's PSModulePath, one line
    # "<state><TAB><entry as written><TAB><root><TAB><full path><TAB><error><TAB><psrc files
    # joined by |>": state 'present', 'absent' or 'error' (Get-RefuteJeaInspection); the
    # root is the entry normalised like ConvertTo-RefuteModuleRoot of the registration (the
    # final '\' characters dropped, a volume root keeping one: 'C:' would be the current
    # folder of drive C); the full path is the root as this process resolves it (a
    # relative entry against its current folder), and it is the folder inspected; the
    # files are every <full path>\<folder>\RoleCapabilities\*.psrc, what JEA could select
    # there. A RoleCapabilities folder that cannot be read makes the root 'error'. The first
    # line is "cwd<TAB><current folder>".
    $lines = [System.Collections.Generic.List[string]]::new()
    $lines.Add([string]::Join("`t", @('cwd', [System.IO.Directory]::GetCurrentDirectory())))
    foreach ($entry in [Environment]::GetEnvironmentVariable('PSModulePath').Split(';')) {
        if (-not $entry) { continue }
        $root = $entry.TrimEnd('\')
        if ($root -match '^[A-Za-z]:$') { $root = $root + '\' }
        $files = [System.Collections.Generic.List[string]]::new()
        try { $full = [System.IO.Path]::GetFullPath($root) } catch { $full = '' }
        if (-not $full) {
            $lines.Add([string]::Join("`t", @('error', $entry, $root, '', 'the entry cannot be resolved', '')))
            continue
        }
        $state, $err, $dirs = Get-RefuteJeaInspection -Path $full -Pattern '' -Files $false
        if ($state -eq 'present') {
            foreach ($dir in $dirs) {
                $folder = [System.IO.Path]::Combine($dir, 'RoleCapabilities')
                $sub, $subErr, $found = Get-RefuteJeaInspection -Path $folder -Pattern '*.psrc' -Files $true
                if ($sub -eq 'present') { $files.AddRange([string[]]$found) }
                elseif ($sub -eq 'error') { $state = 'error'; $err = $subErr }
            }
        }
        $lines.Add([string]::Join("`t", @($state, $entry, $root, $full, $err, [string]::Join('|', $files.ToArray()))))
    }
    [string]::Join("`n", $lines.ToArray())
}

Export-ModuleMember -Function Get-RefuteJeaProbe, Get-RefuteJeaModuleRoots
