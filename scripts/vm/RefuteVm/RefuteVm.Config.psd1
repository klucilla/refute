# Configuration of the Refute VM (WP6, phase 1). It is installed with the module in
# a folder only administrators can write, so the account that calls the JEA endpoint
# cannot change it; a change means a new reviewed version and a new registration by the
# maintainer (scripts/vm/README.md). Plan section 7.1; docs/validation/v0.3/wp6-acceptance.md.
@{
    ConfigVersion           = 1

    # The only VM these scripts act on. Its VMId is recorded at creation (StateFile) and
    # checked by every later operation.
    VmName                  = 'refute-vm'

    # Host defaults asked by the maintainer (Set-VMHost), never on K:.
    HostVirtualMachinePath  = 'C:\Hyper-V'
    HostVirtualHardDiskPath = 'C:\Hyper-V\Virtual Hard Disks'

    # Explicit paths of this VM, also passed to New-VM and New-VHD.
    VmRoot                  = 'C:\Hyper-V\refute-vm'
    BaseDiskPath            = 'C:\Hyper-V\Virtual Hard Disks\refute-vm-base.vhdx'
    # Dynamic VHDX, maximum size: 100 GiB, decided by the maintainer on 2026-10-16 (it was
    # 200 GiB). Disk budget (C: had 378 GB free on 2026-10-16, plan 7.1): 100 GiB base at
    # most, plus up to 48 GiB of saved memory state (Save-VM). Space estimate:
    # docs/validation/v0.3/wp6-results/disk-space-estimate.md.
    BaseDiskSizeBytes       = 107374182400

    # Install media: verified copies, read by the VM from MediaRoot. The endpoint copies
    # them from MediaSource (inside the project, written by the maintainer's account)
    # only when their SHA-256 equals the value approved in the call.
    MediaRoot               = 'C:\Hyper-V\refute-vm\media'
    MediaSource             = 'C:\Projetos\refute\.cache\vm\media'
    InstallIsoName          = 'ubuntu-26.04.1-live-server-amd64.iso'
    # Filled in a reviewed change after the ISO is checked against SHA256SUMS and its
    # signature (Get-RefuteMedia.ps1), before the endpoint is registered; while empty,
    # ImportInstallIso refuses. Verified on 2026-10-15 (evidence:
    # docs/validation/v0.3/wp6-results/media-verification.json): SHA256SUMS signed by the
    # Ubuntu CD Image Automatic Signing Key (2012), fingerprint
    # 843938DF228D22F7B3742BC0D94AA3F0EFE21092, and this ISO's line in it.
    InstallIsoSha256        = 'cc8a95cde20f6ced61a322420de00f10cc3c90ced545daa46cb9c1a117f1d927'
    SeedIsoName             = 'refute-vm-seed.iso'

    # Hardware (plan 7.1).
    ProcessorCount          = 24
    MemoryBytes             = 51539607552
    SecureBootTemplate      = 'MicrosoftUEFICertificateAuthority'

    # The Guest Service Interface is identified at the call (DisableGuestServiceInterface
    # -ServiceGuid), from the Id that Get-RefuteVmStatus lists on this host: its name
    # depends on the Windows language, and no official page found gives its GUID.

    # Written by the endpoint (virtual account, member of Hyper-V Administrators only).
    StateFile               = 'C:\ProgramData\RefuteVm\State\vm.json'
    OperationLog            = 'C:\ProgramData\RefuteVm\Log\operations.jsonl'
}
