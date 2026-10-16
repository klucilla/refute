# Every command the RefuteVm module calls must exist in a RestrictedRemoteServer session
# that imports what the role capability's ModulesToImport names (the maintainer's H.5 of
# 2026-10-16: 'Import-PowerShellDataFile' was not recognized in the real session).
# Windows PowerShell 5.1 on Windows, no administrator rights: it parses the module's files,
# builds an initial session state from InitialSessionState.CreateRestricted(RemoteServer)
# plus the role capability's imports (the installed path of RefuteVm replaced by the
# repository's copy), opens a local runspace and looks each command up. It reaches every
# function of the module, also the paths a host without Hyper-V never runs. Prints one JSON
# object; tests/test_vm_scripts.py holds the assertions. It changes nothing on the machine.
param([Parameter(Mandatory = $true)][string]$Root)
$ErrorActionPreference = 'Stop'
Set-StrictMode -Version 2.0

$moduleDir = Join-Path $Root 'scripts\vm\RefuteVm'
$psrc = Join-Path $moduleDir 'RoleCapabilities\RefuteVmOperator.psrc'
$installed = 'C:\Program Files\WindowsPowerShell\Modules\RefuteVm\RefuteVm.psd1'
$out = [ordered]@{ Ran = $false; Reason = ''; Imports = @(); Checked = 0; Missing = @(); Defined = 0 }

if ($PSVersionTable.PSEdition -ne 'Desktop') { $out.Reason = 'not Windows PowerShell 5.1'; $out | ConvertTo-Json -Compress; exit 0 }
if (-not (Get-Module -ListAvailable -Name Hyper-V)) { $out.Reason = 'the Hyper-V PowerShell module is not installed'; $out | ConvertTo-Json -Compress; exit 0 }

# the commands the module calls, and the functions it defines
$called = @{}
$defined = @{}
foreach ($file in 'RefuteVm.psm1', 'RefuteVm.Core.ps1', 'RefuteVm.HyperV.ps1') {
    $tokens = $null; $errors = $null
    $ast = [System.Management.Automation.Language.Parser]::ParseFile((Join-Path $moduleDir $file), [ref]$tokens, [ref]$errors)
    if ($errors.Count) { throw "parse errors in $file" }
    foreach ($fn in $ast.FindAll({ param($n) $n -is [System.Management.Automation.Language.FunctionDefinitionAst] }, $true)) {
        $defined[$fn.Name.ToLowerInvariant()] = $true
    }
    foreach ($c in $ast.FindAll({ param($n) $n -is [System.Management.Automation.Language.CommandAst] }, $true)) {
        $name = $c.GetCommandName()
        if ($name) { $called[$name.ToLowerInvariant()] = $name }
    }
}

# the session the role capability builds, with the repository's copy of the module
$role = Import-PowerShellDataFile -LiteralPath $psrc
$imports = @(@($role.ModulesToImport) | ForEach-Object { if ($_ -eq $installed) { Join-Path $moduleDir 'RefuteVm.psd1' } else { $_ } })
$out.Imports = $imports
$iss = [System.Management.Automation.Runspaces.InitialSessionState]::CreateRestricted([System.Management.Automation.SessionCapabilities]::RemoteServer)
$iss.ThrowOnRunspaceOpenError = $true
$iss.ImportPSModule([string[]]$imports)
$rs = [System.Management.Automation.Runspaces.RunspaceFactory]::CreateRunspace($iss)
$rs.Open()
try {
    $missing = [System.Collections.Generic.List[string]]::new()
    foreach ($key in (@($called.Keys) | Sort-Object)) {
        if ($defined.ContainsKey($key)) { continue }
        $out.Checked++
        $cmd = $rs.SessionStateProxy.InvokeCommand.GetCommand($called[$key], [System.Management.Automation.CommandTypes]::All)
        if (-not $cmd) { $missing.Add($called[$key]) }
    }
    $out.Missing = @($missing)
    $out.Defined = $defined.Count
    $out.Ran = $true
} finally { $rs.Dispose() }
$out | ConvertTo-Json -Compress
