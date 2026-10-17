# WP6: disk space estimate for a base disk of 100 GiB (2026-10-17)

The maintainer decided on 2026-10-16 that the base disk of the Refute VM is 100 GiB
instead of 200 GiB (`BaseDiskSizeBytes` from 214748364800 to 107374182400 in
`scripts/vm/RefuteVm/RefuteVm.Config.psd1`). This record estimates whether that is
enough for v0.3. It is an **estimate**: nothing was installed or measured in the VM, which
does not exist yet. Every external fact gives its source and the date it was read
(2026-10-17).

## 1. What the plan provides

- **Disks** (plan section 7.1, [v0.3-plan.md](../../../plans/v0.3-plan.md)): one VHDX for
  the system, images and cache, and a differencing disk per paper, so that every paper
  starts from the same clean state.
- **Papers that run in the VM in v0.3:** the 5 papers of the main sample (D-19, section
  10.4; no additional papers are planned) and the 2 development papers (D-3, section 4.5),
  so **7 papers**, plus the controlled tests (artifacts built for the purpose, small). The
  20 pilot papers are read only (metadata and README) and never run.
- **Triage caps per paper** (section 4.4): declared datasets at most **5 GB**, declared
  model weights at most **2 GB**. Compute is limited to CPU (section 7.1).
- **Assumption of this estimate:** what a paper writes (its images, its data, its outputs)
  lives in its differencing disk, and the base disk holds only what every paper shares
  (system, Docker, the pinned base images of the build ladder, shared caches). If the
  design changes so that per-paper images stay in the base, this estimate must be redone.

## 2. Where the differencing disks are, and what they count against

- **No operation creates them yet.** Phase 1 (operations 1 to 16) creates only the base
  disk; the differencing disks come with a later operation, still to be written.
- **On the host they are separate files**, outside the base disk's file. Hyper-V creates
  a child with `New-VHD -ParentPath <base> -Path <child> -Differencing`; `-SizeBytes` is
  optional in that parameter set (https://learn.microsoft.com/en-us/powershell/module/hyper-v/new-vhd,
  read 2026-10-17). Each child is a file that grows with what the paper writes, so it
  counts against the free space of C: **in addition** to the base disk, the saved state and
  the media copies.
- **In the guest they share the base's capacity.** The guest sees one disk: the base's
  content plus the child's changes. So a paper can write at most the disk's virtual size
  minus what the base already holds. This estimate assumes a child created without
  `-SizeBytes` has the parent's virtual size (100 GiB); the reference page does not state
  the default, so this is checked when the operation that creates children is written.
- **Papers do not add up in the guest:** each paper starts from a new child of the clean
  base, so the guest only has to fit the base plus **one** paper.

## 3. The base disk (inside the 100 GiB)

| Item | Estimate | Source |
|---|---|---|
| Ubuntu Server 26.04 installed | **10 GB** budgeted. The official page gives "Minimum storage: 5 GB (ISO installs)" and a suggested minimum of 25 GB for the whole machine, for 24.04 LTS amd64 ("Other releases and architectures might differ slightly") | https://ubuntu.com/server/docs/reference/installation/system-requirements/ (read 2026-10-17) |
| Swap file made by the installer | **8 GiB** at most. The seed (`scripts/vm/seed/user-data.template`) does not set `swap`, so curtin suggests the size: half the memory up to 64 GiB of RAM (8 GiB for the 16 GiB of 2026-10-17; it was 24 GiB for 48 GiB), capped at the lesser of 8 GiB and 25% of the free space | https://raw.githubusercontent.com/canonical/curtin/master/curtin/swap.py, `suggested_swapsize` (read 2026-10-17) |
| Docker Engine and containerd | **0.3 GB**. Ubuntu 26.04 (`resolute`), amd64: `docker.io` 29.1.3, installed size 134,196 kB; `containerd` 2.2.2, installed size 100,946 kB | https://packages.ubuntu.com/resolute/docker.io and https://packages.ubuntu.com/resolute/containerd (read 2026-10-17) |
| Pinned base images of the build ladder | **2 GB** budgeted for up to 3 Python images. `python:3.12-slim` for linux/amd64 is 41.26 MB compressed. With Docker Engine 29 on a fresh install the default store is the containerd image store, which "uses more disk space than the legacy storage drivers" because it keeps images "in both compressed and uncompressed formats" | https://hub.docker.com/_/python/tags?name=3.12-slim and https://docs.docker.com/engine/storage/containerd/ (read 2026-10-17) |
| Shared caches (package indexes, tools) | **10 GB** budgeted | assumption |
| **Base, total** | **about 31 GB** (10 + 8.6 + 0.3 + 2 + 10; the swap file of 8 GiB is 8.6 GB) | |

## 4. One paper (in its differencing disk)

Three cases: **typical**, a **heavy** case, and a **stacked** case that piles up every
large item at once. Several items are assumptions with no cap in the plan; they are marked.

| Item | Stacked | Heavy | Typical | Basis |
|---|---|---|---|---|
| Image of the paper | **12 GB** | 12 GB | 3 GB | A repository that installs `torch` from PyPI on Linux also gets its CUDA packages, which the wheel declares for Linux with no GPU check: `torch` 2.14.1 for cp312 manylinux x86_64 is 554.6 MB, and five of its CUDA dependencies measured 1,423 MB together (`nvidia-cudnn-cu13` 553.1 MB, `nvidia-cublas` 423.1 MB, `nvidia-nccl-cu13` 216.0 MB, `nvidia-cusparselt-cu13` 170.1 MB, `nvidia-nvshmem-cu13` 60.4 MB), so 1,977 MB of wheels for six packages, before the other CUDA packages (`cuda-toolkit` components, `triton`). Budget: about 3 GB downloaded, about 8 GB installed with the Python stack, plus the compressed copy the containerd store keeps. The installed size is an estimate, not a measurement. The typical case is a repository on a CPU-only stack | https://pypi.org/pypi/torch/2.14.1/json and the JSON pages of each package on pypi.org (read 2026-10-17) |
| Build ladder | **24 GB** more | 12 GB more | 0 | Up to 3 rungs (plan 6.1). A rung that fails late can leave almost a whole image; nothing in the plan removes it before the next rung. Stacked: two failed rungs before the one that builds; heavy: one |
| Declared data and weights | **14 GB** | 14 GB | 3 GB | At most 5 GB plus 2 GB (triage caps), counted twice for the archive and its extracted copy. **Assumption:** a dataset that expands more when extracted is not bounded by the caps |
| Outputs, logs, predictions | **5 GB** | 5 GB | 1 GB | **Assumption.** The attacks rerun experiments (5 extra seeds, up to 3 re-splits; plan 6.3) within the paper's 384 CPU-hours, so the outputs can be several times those of the base runs. The plan gives each container a disk quota (plan 6.1) but no value yet |
| Build caches | **5 GB** | 5 GB | 1 GB | **Assumption** |
| **One paper, total** | **60 GB** | **48 GB** | **8 GB** | |

## 5. Against 100 GiB (107.4 GB)

ext4 reserves 5% of the blocks for the super-user by default ("The default percentage is
5%", https://manpages.ubuntu.com/manpages/resolute/man8/mke2fs.8.html, read 2026-10-17),
about 5.4 GB of a 100 GiB disk; the containers write as a non-root user (plan 6.1), so the
last column subtracts it. The EFI partition and file system metadata are left out.

| Case | Base | One paper | Total | Free in the guest | Free for non-root writers |
|---|---|---|---|---|---|
| Typical | 30.9 GB | 8 GB | 38.9 GB | 68.5 GB | about 63 GB |
| Heavy | 30.9 GB | 48 GB | 78.9 GB | 28.5 GB | about 23 GB |
| Stacked | 30.9 GB | 60 GB | 90.9 GB | 16.5 GB | about 11 GB |

**Conclusion for the guest.**
- **Under the assumptions of sections 3 and 4, 100 GiB fits:** a typical paper uses about a
  third of the disk, and even the stacked case fits.
- **The margin of the heavy and stacked cases is not established.** The stacked case leaves
  about 11 GB for non-root writers, and several of its items have no cap in the plan
  (how much a dataset expands, the outputs of the attacks, the build caches). Each of them
  could exceed its assumption.
- **So the estimate does not show that 100 GiB fits every case of v0.3 with margin.** That
  margin depends on rules still to be defined: a control of the space that failed rungs
  occupy, and the value of the disk quota per container (plan 6.1).
- Since each paper starts from a new child of the clean base, the 7 papers never add up in
  the guest.

## 6. On the host (C:)

C: had 378 GB free on 2026-10-16 (the maintainer), and 403.7 GB on 2026-10-17 at 04:09 UTC
(`Get-PSDrive C`, read only, by the agent).

| Item | Estimate | Upper bound |
|---|---|---|
| Base disk file (dynamic VHDX: it grows with what is written) | 30.9 GB | 107.4 GB (100 GiB) |
| Saved memory state (`Save-VM`) | | 17.2 GB (16 GiB, since 2026-10-17; it was 51.5 GB for 48 GiB) |
| Media copies in `C:\Hyper-V\refute-vm\media` | 2.9 GB (the ISO is 2,927,861,760 bytes; the seed 55,296 bytes) | 2.9 GB |
| One differencing disk | 8 GB typical, 48 GB heavy, 60 GB stacked | 107.4 GB |

**Update of 2026-10-17 (the maintainer's decision: 16 GiB of static memory).** The base disk
measured **6.50 GB** after the installation (the maintainer), below the 30.9 GB budgeted;
the figures below keep the budget.

- **One child at a time:** 30.9 + 17.2 + 2.9 + 60 = 111.0 GB in the stacked case, and
  234.9 GB with every upper bound; both fit in 378 GB. (With 48 GiB: 145 GB and 269 GB.)
- **Seven children kept at once:** typical, 30.9 + 17.2 + 2.9 + 7 × 8 = 107.0 GB, which
  fits; heavy, 387.0 GB, and stacked, 471.0 GB, which do **not** fit in 378 GB. (With
  48 GiB: 141, 421 and 505 GB.)
- **How many children are kept at once is still to be decided**, with the operation that
  creates them; it does not depend on the base being 100 GiB.
- **The maximum size costs nothing until it is written.** A dynamic VHDX takes on the host
  about what the guest has written (and does not give it back, see below), so a smaller maximum lowers the upper bound of a disk that
  fills up; it does not lower the typical use.
- A dynamic VHDX does not give space back by itself: `Resize-VHD` "does not remove empty
  blocks from a dynamically-expanding virtual hard disk file"; `Optimize-VHD` does
  (https://learn.microsoft.com/en-us/powershell/module/hyper-v/resize-vhd, read
  2026-10-17). The estimate treats every file as never shrinking.

## 7. If the disk is too small later (recorded, not implemented)

Growing a disk is a **new operation**, outside operations 1 to 16, and needs the
maintainer's OK. It runs as Administrator, with the VM off.
- **Growing the base** also needs a reviewed change of `BaseDiskSizeBytes` and the update of
  the installed configuration, because `CreateBaseDisk` and `AttachBaseDisk` refuse a base
  disk whose size differs from the configuration (`RefuteVm.Core.ps1`).
- **Growing one child** does not change `BaseDiskSizeBytes`, which describes the parent; how
  a child's size is checked belongs to the operation that creates the children.

1. **On the host:** `Resize-VHD -Path <disk> -SizeBytes <new size>`. The cmdlet "can expand
   both VHD and VHDX files"; a disk on a SCSI chain can even be resized online, but the VM
   stays off here (https://learn.microsoft.com/en-us/powershell/module/hyper-v/resize-vhd,
   read 2026-10-17).
   - **The base, only while no child depends on it.** The reference page does not describe
     growing a parent that has children; this record treats it as unsafe. Grow the base before any
     child exists, or create the children again afterwards.
   - **Or one child alone.** A differencing VHDX can be expanded "without impacting the
     base or parent hard disk or any siblings" (Microsoft, 2012-10-09,
     https://learn.microsoft.com/en-us/archive/blogs/taylorb/expanding-differencing-virtual-hard-disks,
     read 2026-10-17). That would give one paper more room without touching the base.
2. **In Ubuntu:** the seed uses the `direct` storage layout (no LVM), so the root file system
   is one ext4 partition. After the VM starts: find the partition number with `lsblk`,
   extend it with `growpart <disk> <partition number>` ("extend a partition in a partition
   table to fill available space",
   https://manpages.ubuntu.com/manpages/resolute/man1/growpart.1.html), then
   `resize2fs <partition>`, which grows a mounted ext4 file system and, without a size,
   uses "the size of the partition"
   (https://manpages.ubuntu.com/manpages/resolute/man8/resize2fs.8.html, both read
   2026-10-17).

## 8. Decision, and the rules still open

**Decided by the maintainer on 2026-10-17:** the base disk stays at 100 GiB (option A), with
the margin of sections 5 and 6 as it is. Three rules remain open. Each is **decided before
any paper runs**, with the operation or work package it belongs to; none is implemented
here.

1. **The space that failed rungs of the build ladder occupy** (sections 4 and 5): how it is
   controlled, so that the stacked case cannot happen unnoticed.
2. **The value of the disk quota per container** (plan 6.1, "Limits per container"): the
   plan names the quota but gives no value.
3. **How many differencing disks are kept at the same time** (section 6). The maintainer's
   preference: one at a time, with the evidence extracted to the dossier before the child is
   removed. It is decided with the operation that creates the children.
