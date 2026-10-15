@{
    RootModule           = 'RefuteVm.psm1'
    ModuleVersion        = '0.1.0'
    GUID                 = 'b2713b52-46f8-4c00-a4bf-2b940708587a'
    Author               = 'Refute contributors'
    Description          = 'Operations of the Refute VM (WP6 phase 1), exposed only through the JEA endpoint RefuteVm.'
    PowerShellVersion    = '5.1'
    CompatiblePSEditions = @('Desktop')
    FunctionsToExport    = @('Get-RefuteVmStatus', 'Invoke-RefuteVmOperation')
    CmdletsToExport      = @()
    VariablesToExport    = @()
    AliasesToExport      = @()
}
