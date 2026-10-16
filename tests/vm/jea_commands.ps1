# Every command the RefuteVm module calls must exist in a RestrictedRemoteServer session
# that imports what the role capability's ModulesToImport names (the maintainer's H.5 of
# 2026-10-16: 'Import-PowerShellDataFile' was not recognized in the real session).
# Windows PowerShell 5.1 on Windows, no administrator rights: it parses the module's files,
# builds an initial session state from InitialSessionState.CreateRestricted(RemoteServer)
# plus the role capability's imports (the installed path of RefuteVm replaced by the
# repository's copy), opens a local runspace and looks each command up. It reaches every
# function of the module, also the paths a host without Hyper-V never runs. It shows that
# the commands exist in such a state, not what the connecting account sees (the real
# endpoint test, tests/vm/jea_integration.ps1, checks that). Calls without a command name
# are listed by their form, so that a new dynamic call cannot hide from the lookup. Prints
# one JSON object; tests/test_vm_scripts.py holds the assertions. It changes nothing on
# the machine.
param([Parameter(Mandatory = $true)][string]$Root)
$ErrorActionPreference = 'Stop'
Set-StrictMode -Version 2.0

$moduleDir = Join-Path $Root 'scripts\vm\RefuteVm'
$psrc = Join-Path $moduleDir 'RoleCapabilities\RefuteVmOperator.psrc'
$installed = 'C:\Program Files\WindowsPowerShell\Modules\RefuteVm\RefuteVm.psd1'
$out = [ordered]@{ Ran = $false; Reason = ''; Imports = @(); Checked = 0; Missing = @(); Defined = 0; Dynamic = [ordered]@{}; HyperV = $null }

if ($PSVersionTable.PSEdition -ne 'Desktop') { $out.Reason = 'not Windows PowerShell 5.1'; $out | ConvertTo-Json -Compress; exit 0 }
$role = Import-PowerShellDataFile -LiteralPath $psrc
$hyperVImport = @(@($role.ModulesToImport) | Where-Object { $_ -like '*\Hyper-V.psd1' })
if ($hyperVImport.Count -ne 1) { throw 'the role capability must import Hyper-V by the path of its manifest' }
if (-not (Test-Path -LiteralPath $hyperVImport[0] -PathType Leaf)) { $out.Reason = "the Hyper-V PowerShell module is not at $($hyperVImport[0])"; $out | ConvertTo-Json -Compress; exit 0 }

# the commands the module calls, the functions it defines, and the calls without a name
$called = @{}
$defined = @{}
$dynamic = @{}
foreach ($file in 'RefuteVm.psm1', 'RefuteVm.Core.ps1', 'RefuteVm.HyperV.ps1') {
    $tokens = $null; $errors = $null
    $ast = [System.Management.Automation.Language.Parser]::ParseFile((Join-Path $moduleDir $file), [ref]$tokens, [ref]$errors)
    if ($errors.Count) { throw "parse errors in $file" }
    foreach ($fn in $ast.FindAll({ param($n) $n -is [System.Management.Automation.Language.FunctionDefinitionAst] }, $true)) {
        $defined[$fn.Name.ToLowerInvariant()] = $true
    }
    foreach ($c in $ast.FindAll({ param($n) $n -is [System.Management.Automation.Language.CommandAst] }, $true)) {
        $name = $c.GetCommandName()
        if ($name) {
            $called[$name.ToLowerInvariant()] = $name
        } else {
            $form = "$($c.InvocationOperator) $($c.CommandElements[0].Extent.Text)"
            if ($dynamic.ContainsKey($form)) { $dynamic[$form]++ } else { $dynamic[$form] = 1 }
        }
    }
}
foreach ($form in (@($dynamic.Keys) | Sort-Object)) { $out.Dynamic[$form] = $dynamic[$form] }

# the session the role capability builds, with the repository's copy of the module
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
    # where the Hyper-V cmdlets come from: the module path the role capability names, and
    # the assembly its manifest loads (NestedModules Microsoft.HyperV.PowerShell.Cmdlets.dll)
    $vmHost = $rs.SessionStateProxy.InvokeCommand.GetCommand('Get-VMHost', [System.Management.Automation.CommandTypes]::Cmdlet)
    if ($vmHost) {
        $assembly = $vmHost.ImplementingType.Assembly
        $out.HyperV = [ordered]@{ ModulePath = [string]$vmHost.Module.Path; AssemblyLocation = [string]$assembly.Location; GlobalAssemblyCache = [bool]$assembly.GlobalAssemblyCache }
    }
    $out.Ran = $true
} finally { $rs.Dispose() }
$out | ConvertTo-Json -Compress
