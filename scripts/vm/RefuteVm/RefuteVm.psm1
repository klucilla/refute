# RefuteVm: the operations of the Refute VM (WP6, phase 1), exposed only through the
# JEA endpoint "RefuteVm" (scripts/vm/README.md). Two functions are visible:
#   Get-RefuteVmStatus          read only
#   Invoke-RefuteVmOperation    one administrative action per call: first with
#                               -Simulate (no change to the managed state), then with
#                               the PlanSha256 the simulation printed.
# No parameter takes a path or a VM name: they all come from RefuteVm.Config.psd1,
# installed with the module where only administrators can write.

Set-StrictMode -Version 2.0
. (Join-Path $PSScriptRoot 'RefuteVm.Core.ps1')
. (Join-Path $PSScriptRoot 'RefuteVm.HyperV.ps1')

function Get-RefuteVmModuleConfig {
    $config = Import-PowerShellDataFile -LiteralPath (Join-Path $PSScriptRoot 'RefuteVm.Config.psd1')
    $problems = Test-RefuteVmConfig $config
    if ($problems.Count) { throw ('invalid configuration: ' + ($problems -join '; ')) }
    return $config
}

function Get-RefuteVmModuleFiles {
    # SHA-256 of every file of the installed module, by path relative to the module.
    $root = (Resolve-Path -LiteralPath $PSScriptRoot).Path
    $map = [ordered]@{}
    $files = @(Get-ChildItem -LiteralPath $root -Recurse -File | Sort-Object FullName)
    foreach ($file in $files) {
        $relative = $file.FullName.Substring($root.Length + 1).Replace('\', '/')
        $map[$relative] = (Get-FileHash -LiteralPath $file.FullName -Algorithm SHA256).Hash.ToLowerInvariant()
    }
    return $map
}

function Get-RefuteVmCaller {
    $sender = $null
    if (Get-Variable -Name PSSenderInfo -ErrorAction SilentlyContinue) { $sender = $PSSenderInfo }
    return Get-RefuteVmCallerRecord -SenderInfo $sender -RunAsUser ([System.Security.Principal.WindowsIdentity]::GetCurrent().Name)
}

function Get-RefuteVmStatus {
    <#
    .SYNOPSIS
    Read-only state of the host, of the Refute VM and of the media, with the module and
    configuration hashes. Changes nothing.
    #>
    [CmdletBinding()]
    param([switch]$IncludeMedia)
    $config = Get-RefuteVmModuleConfig
    # everything that does not need Hyper-V first, so that a host without it still
    # exercises the rest of the call before the Hyper-V step
    $module = Get-RefuteVmModuleFiles
    $configSha = Get-RefuteSha256Text (ConvertTo-RefuteCanonicalJson $config)
    $caller = Get-RefuteVmCaller
    $observed = Get-RefuteVmObserved -Config $config -IncludeMedia:$IncludeMedia
    $status = [ordered]@{
        Module       = $module
        ConfigSha256 = $configSha
        Config       = $config
        Observed     = $observed
        Caller       = $caller
    }
    return ConvertTo-RefuteCanonicalJson $status
}

function Invoke-RefuteVmOperation {
    <#
    .SYNOPSIS
    One administrative action on the Refute VM or its host settings.
    .DESCRIPTION
    With -Simulate: computes the plan from the configuration and the observed state,
    writes a log record marked simulated, and returns the plan and its PlanSha256; the
    managed state is not changed. Without -Simulate: requires -PlanSha256, computes the
    plan again, refuses if it differs (the state or the configuration changed since the
    simulation), logs the intent, performs the one action, checks that the planned state
    is reached, and logs the result.
    #>
    [CmdletBinding()]
    param(
        [Parameter(Mandatory = $true)]
        [ValidateSet('SetHostPaths', 'DisableEnhancedSessionHost', 'CreateBaseDisk', 'CreateVm',
            'SetMemory', 'SetProcessor', 'SetSecureBoot', 'DisableCheckpoints',
            'DisableGuestServiceInterface', 'DisconnectNetwork', 'AttachBaseDisk',
            'ImportInstallIso', 'ImportSeedIso', 'AttachInstallMedia', 'SetBootFromInstallMedia',
            'StartVm', 'StopVm', 'DetachInstallMedia', 'SetProcessorMaximum', 'SuspendVm',
            'ResumeVm', 'SaveVm', 'SetPortProfile', 'ConnectNetwork')]
        [string]$Operation,
        [switch]$Simulate,
        [ValidatePattern('^[0-9a-f]{64}$')]
        [string]$PlanSha256 = '',
        [ValidatePattern('^[0-9a-f]{64}$')]
        [string]$MediaSha256 = '',
        [ValidateRange(0, 100)]
        [int]$Percent = 0,
        [ValidatePattern('^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$')]
        [string]$ServiceGuid = '',
        [ValidateSet('', 'build', 'pull')]
        [string]$Profile = ''
    )
    $config = Get-RefuteVmModuleConfig
    $operationId = [guid]::NewGuid().ToString()
    $includeMedia = @('ImportInstallIso', 'ImportSeedIso', 'AttachInstallMedia') -contains $Operation
    # computed before the Hyper-V step, as in Get-RefuteVmStatus; the same values go into
    # the records below
    $caller = Get-RefuteVmCaller
    $moduleFiles = Get-RefuteVmModuleFiles
    # A real call holds the lock from the observation to the final check, so the guards
    # are evaluated on the state the action meets and no other session acts meanwhile.
    $lock = $null
    if (-not $Simulate) { $lock = Enter-RefuteVmLock -Config $config }
    try {
        $observed = Get-RefuteVmObserved -Config $config -IncludeMedia:$includeMedia
        $plan = New-RefuteVmPlan -Operation $Operation -Config $config -Observed $observed -MediaSha256 $MediaSha256 -Percent $Percent -ServiceGuid $ServiceGuid -Profile $Profile
        $planSha = Get-RefuteVmPlanSha256 $plan
        $record = [ordered]@{
            Utc         = [DateTime]::UtcNow.ToString('yyyy-MM-ddTHH:mm:ss.fffZ')
            OperationId = $operationId
            Operation   = $Operation
            Mode        = $(if ($Simulate) { 'simulated' } else { 'intent' })
            PlanSha256  = $planSha
            Plan        = $plan
            Caller      = $caller
            Module      = $moduleFiles
        }
        if ($Simulate) {
            Write-RefuteVmLog -Config $config -Record $record
            return ConvertTo-RefuteCanonicalJson ([ordered]@{ Mode = 'simulated'; PlanSha256 = $planSha; Plan = $plan })
        }
        $refusal = $null
        if (-not $PlanSha256) { $refusal = 'no PlanSha256: run the operation with -Simulate first and pass its PlanSha256' }
        elseif ($plan.Refusal) { $refusal = $plan.Refusal }
        elseif ($planSha -cne $PlanSha256) { $refusal = 'the plan differs from the simulated one (state or configuration changed); simulate again' }
        if ($refusal) {
            $record.Mode = 'refused'
            $record['Reason'] = $refusal
            Write-RefuteVmLog -Config $config -Record $record
            throw "refused: $refusal"
        }
        Write-RefuteVmLog -Config $config -Record $record
        $outcome = 'already done'
        $failure = $null
        if (-not $plan.AlreadyDone) {
            # the text of a failure this module raises itself (Stop-RefuteVmOperation)
            $script:RefuteVmFailureReason = ''
            try {
                Invoke-RefuteVmMutation -Config $config -Observed $observed -Plan $plan -MediaSha256 $MediaSha256 -Percent $Percent -ServiceGuid $ServiceGuid -Profile $Profile
                $after = Get-RefuteVmObserved -Config $config -IncludeMedia:$includeMedia
                $notReached = Get-RefuteVmPlanReachedProblem -Plan $plan -Config $config -ObservedAfter $after -MediaSha256 $MediaSha256 -Percent $Percent -ServiceGuid $ServiceGuid -Profile $Profile
                if (-not $notReached) {
                    $outcome = 'done'
                } else {
                    # the reason goes to the result record and to the error (never empty)
                    $outcome = 'not reached'
                    $failure = $notReached
                }
            } catch {
                $outcome = 'failed'
                $failure = Get-RefuteVmFailureText -ErrorRecord $_ -ModuleReason $script:RefuteVmFailureReason
            }
        }
        $result = [ordered]@{
            Utc         = [DateTime]::UtcNow.ToString('yyyy-MM-ddTHH:mm:ss.fffZ')
            OperationId = $operationId
            Operation   = $Operation
            Mode        = 'result'
            PlanSha256  = $planSha
            Outcome     = $outcome
            Error       = $failure
            Caller      = $caller
        }
        Write-RefuteVmLog -Config $config -Record $result
        if ($outcome -eq 'failed' -or $outcome -eq 'not reached') { throw "$Operation ${outcome}: $failure" }
        return ConvertTo-RefuteCanonicalJson ([ordered]@{ Mode = 'result'; Outcome = $outcome; PlanSha256 = $planSha; Plan = $plan })
    } finally {
        if ($lock) { $lock.Dispose() }
    }
}

Export-ModuleMember -Function Get-RefuteVmStatus, Invoke-RefuteVmOperation
