# The records of Get-RefuteVmStatus and Invoke-RefuteVmOperation -Simulate, without Hyper-V
# (Codex review of #118: the caller and the module hashes are now computed before the
# Hyper-V step; this checks the records on any Windows machine, with or without Hyper-V).
# Windows PowerShell 5.1, no administrator rights: it imports the repository's copy of the
# module, replaces inside the module the observation (a synthetic host with no VM) and the
# log writer (records kept in memory), calls both functions, and compares the Caller and
# Module of their output and records with what the module's own functions give. Prints one
# JSON object; tests/test_vm_scripts.py holds the assertions. It changes nothing on the
# machine.
param([Parameter(Mandatory = $true)][string]$Root)
$ErrorActionPreference = 'Stop'
Set-StrictMode -Version 2.0

$out = [ordered]@{ Ran = $false; Reason = ''; Status = $null; Simulate = $null; Records = @(); Expected = $null }
if ($PSVersionTable.PSEdition -ne 'Desktop') { $out.Reason = 'not Windows PowerShell 5.1'; $out | ConvertTo-Json -Compress -Depth 20; exit 0 }

$module = Import-Module (Join-Path $Root 'scripts\vm\RefuteVm\RefuteVm.psd1') -Force -PassThru
try {
    & $module {
        $script:SyntheticRecords = New-Object System.Collections.Generic.List[object]
        function script:Get-RefuteVmObserved {
            param([System.Collections.IDictionary]$Config, [switch]$IncludeMedia)
            return [ordered]@{
                Host                  = [ordered]@{ VirtualMachinePath = 'C:\ProgramData\Microsoft\Windows\Hyper-V'; VirtualHardDiskPath = 'C:\Users\Public\Documents\Hyper-V\Virtual Hard Disks'; EnableEnhancedSessionMode = $true }
                Vms                   = @()
                Files                 = [ordered]@{ BaseDisk = [ordered]@{ Exists = $false; Format = ''; Type = ''; SizeBytes = 0 }; InstallIsoMediaSha256 = ''; InstallIsoSourceSha256 = ''; SeedIsoMediaSha256 = ''; SeedIsoSourceSha256 = '' }
                RecordedVmId          = ''
                RecordedSeedIsoSha256 = ''
            }
        }
        function script:Write-RefuteVmLog {
            param([System.Collections.IDictionary]$Config, [System.Collections.IDictionary]$Record)
            $script:SyntheticRecords.Add((ConvertTo-RefuteCanonicalJson $Record))
        }
    }
    $out.Status = Get-RefuteVmStatus
    $out.Simulate = Invoke-RefuteVmOperation -Operation SetHostPaths -Simulate
    $out.Records = @(& $module { $script:SyntheticRecords.ToArray() })
    $out.Expected = & $module {
        [ordered]@{
            Caller       = ConvertTo-RefuteCanonicalJson (Get-RefuteVmCaller)
            Module       = ConvertTo-RefuteCanonicalJson (Get-RefuteVmModuleFiles)
            ConfigSha256 = Get-RefuteSha256Text (ConvertTo-RefuteCanonicalJson (Get-RefuteVmModuleConfig))
        }
    }
    $out.Ran = $true
} finally {
    Remove-Module $module
}
$out | ConvertTo-Json -Compress -Depth 20
