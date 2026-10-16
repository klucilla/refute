# Sandbox for third-party code (v0.3)

How Refute runs the code of a paper's repository. This document follows
[docs/plans/v0.3-plan.md](plans/v0.3-plan.md), sections 6.1 and 7.

**Not yet validated.** Everything below is a set of **requirements**. The isolation
is validated only by the acceptance tests of the VM work package (WP6), before any
third-party code runs. Until then no third-party code is executed, and nothing here
describes a tested setup.

## Where code runs

- Third-party code runs only inside a dedicated Hyper-V VM on the maintainer's PC,
  with Docker inside. Docker Desktop on Windows is used only for Refute's own tests.
  Third-party code never runs on any other server of the maintainer.
- The VM: generation 2, Ubuntu Server LTS from the official image (SHA-256 checked),
  24 virtual processors, 48 GB of static memory, one VHDX for the system, images and
  cache, and a differencing disk per paper so that every paper starts from the same
  clean state. No shared folders; Enhanced Session off; Guest Service Interface off.
  Results are pulled by the host over SSH with a key used only for this VM.
- **The VM is built and operated through the approved JEA model**
  ([scripts/vm/README.md](../scripts/vm/README.md)).
  - **The endpoint:** versioned scripts are run by a local JEA endpoint, `RefuteVm`. It
    is a restricted session that exposes two functions and runs as a virtual account in
    Hyper-V Administrators only.
  - **Operations:** each operation is simulated first and runs only with the
    maintainer's explicit approval of that operation, given by its plan hash.
  - **The maintainer's steps:** the maintainer registers the endpoint and runs every
    step that needs administrator rights; the agent's account has no Hyper-V rights.
  - **No validation by construction:** building the VM does not validate its isolation.
    That is the work of the WP6 acceptance tests (W6.4 to W6.6).
- Every sandboxed run is started by the maintainer, or with the maintainer's explicit
  approval for that paper. An agent never executes repository code on the host.

## Network

- **Blocks enforced outside the guest.** Access from the VM to the Windows host, the
  local network and private or special address ranges (IPv4 RFC 1918 and link-local;
  IPv6 unique-local, link-local and the other special-purpose ranges of the IANA
  registry) is blocked by access control lists on the VM's network adapter port in
  Hyper-V. The maintainer sets them on Windows, as Administrator: this is a step
  outside the endpoint, which has no operation for it. A firewall inside the guest is
  only a second layer, since a compromised guest could change it.
- **Build egress only through an allowlist.** During the build, the VM reaches the
  internet only through a controlled intermediary (a forwarding proxy) with an
  allowlist of declared destinations: package registries and the declared data hosts.
  There is no direct connection to the internet.
- **Run phase without network:** `--network none`, and the VM's network adapter
  disconnected.

## Inputs

- **Declared inputs fetched by Refute.** Declared datasets and model weights are
  downloaded by Refute's own fetcher, not by repository code, and hashed before any
  repository code runs. Downloads made by the repository's own build happen only in
  the build phase and are logged.
- **Repository version:** frozen by commit. The version explicitly associated with
  the result (a tag or commit named in the paper or README) is used; without one, the
  latest commit on the draw date. The paper version, the chosen commit and the latest
  commit are recorded; tags are resolved to commits. An alternative version may be
  evaluated only as a separate experiment defined beforehand; the main version is
  never replaced after a result is seen.
- **Datasets and model weights:** their reference, version, license, retrieval date
  and hashes are published; a local copy is kept for execution and reproduction only
  when the license allows; the license is checked even when the download is open.

## Containers

- **One container per run**, base image pinned by digest; Python version from the
  repository or from a fixed ladder.
- **Limits per container:** CPU, memory, process count, active-time limit, disk quota;
  `--cap-drop ALL`, `--security-opt no-new-privileges`, non-root user, read-only root
  filesystem with a writable work volume.
- **No mounts and no credentials.** No folder of the Windows host and no folder of
  the guest is mounted into a container, except one output directory of that
  container. Never mounted or passed: the Docker socket, devices (`--device`),
  `--privileged`, an SSH agent, credentials, git configuration or host environment
  variables.
- **Builder configuration, verifiable.** The BuildKit entitlements `network.host`,
  `security.insecure` and `device` are forbidden; the builder configuration file is
  recorded in every dossier.
- **Thread counts** inside the containers (`OMP_NUM_THREADS`, `MKL_NUM_THREADS`,
  `OPENBLAS_NUM_THREADS` and similar) are fixed by the claim, so changing the CPU
  limit never changes how a computation is split.

## Build ladder and patches

The environment is built by a deterministic ladder, fixed before the lock, with no
free-form fixes by an agent:

1. the repository's own Dockerfile or `environment.yml` / lock file, as is;
2. its `requirements.txt` resolved with `uv pip compile --exclude-newer <date of the
   pinned commit>`;
3. step 2 with the next Python version of the ladder.

The first rung that builds is used; all attempts are logged. When no rung builds, the
attribution rule of [verdicts.md](verdicts.md) decides between `NOT_REPRODUCIBLE` and
`INCONCLUSIVE`.

Allowed patches: only a list fixed and hashed before the lock (for example forcing CPU
through an environment variable). Every patch is a diff in the dossier. Source edits
after the lock are forbidden.

## Machine, CPU and budget

- CPU only; at most 24 of the 32 threads. Hyper-V limits the number of virtual
  processors; it does not pin specific cores.
- The budget is counted in CPU-hours over every process of every container of the
  paper. The rules (limit per paper, split between base reproduction and attacks,
  setup account, reserves, attack order, partial results) are in the plan, section
  7.3 and 7.4; they are not repeated here.
- Operational guards are separate from the budget: a run stops after 2 hours of active
  time without verifiable progress, and after a separate limit on active time; the
  values and the progress signals of each stage are fixed before the lock.
- Experimental work is never moved to the host to escape the accounting.

## Capacity control while runs are in progress

- **Containers (inside the VM):** `docker update --cpus N` changes only the CPU quota,
  never `--cpuset-cpus`; `docker pause` and `docker unpause` freeze and resume the
  processes.
- **Whole VM:** through the operations of the JEA endpoint: `SetProcessorMaximum`
  (`Set-VMProcessor -Maximum`), `SuspendVm` / `ResumeVm` and `SaveVm` / `StartVm`.
  Each is simulated first and runs with the maintainer's explicit approval of that
  operation (scripts/vm/README.md). Whether `-Maximum` can change while the VM runs is
  to be verified on the VM before the protocol.
- **Planned commands:** `refute throttle --cpus N`, `refute throttle --reset`,
  `refute pause`, `refute resume`, `refute status`. Every throttle, pause and resume
  is to be recorded as an event with a UTC timestamp in `run/events.jsonl`; a
  heartbeat every 10 s inside the VM records gaps longer than 30 s as pauses.
- CPU-hours do not grow during a pause. Throttling keeps the budget from being
  consumed only because more wall-clock time passed; it does not guarantee identical
  consumption, since efficiency can change. A claim whose code depends on wall-clock
  time is flagged at triage.
- **Pre-run memory check:** before each run and each container, Refute checks that
  enough memory is free for the containers' limits plus a margin, and refuses to start
  otherwise, with a clear message. A refusal is logged and never counts against the
  budget.

## Testing without the VM

CI cannot pull images (no network), so the container backend is tested locally; CI
tests a `subprocess` backend with the same interface on synthetic repositories.

The `subprocess` backend is not an isolation boundary, so it runs **synthetic fixtures
only** (decided by the maintainer on 2026-10-16, design A'; `src/refute/packs/ml/synthetic.py`):

- a closed catalog in Refute's code names each fixture's code files with their SHA-256,
  the data files the harness may add and the folders its runs may write to; a claim or a
  repository can neither choose an entry nor extend the list;
- the test harness writes a fixture into a new folder and receives an authorization for
  it; the backend is built with those authorizations and, built with none, refuses every
  run;
- before each run the backend refuses, before any process starts, a folder it was not
  given (or given through another path), a command other than its own interpreter in
  isolated mode (`-I`) running a code file of the fixture named as in the catalog, a
  changed or missing file, a file with a second link, any other file outside the output
  folders, any symbolic link or junction, and a log inside the folder. What it launches is
  the checked command, by the interpreter's and the code file's absolute paths. No mark
  inside a repository can grant this. The harness and Refute's modules are trusted code
  in one process; the guarantee is that nothing a claim or a repository writes makes the
  backend run anything but cataloged code.

Under this backend the build ladder is played by a cataloged fixture, one build per rung.
Only the deliberate failure the harness declared before the run, recognised by its exit
code and its line in the log, counts as an error of the procedure; a stop by the threshold
or a guard keeps its own cause, and any other outcome, an unexpected success included, is
undetermined (`INCONCLUSIVE`). This exercises the ladder's rules end to end; Docker, the
resolution of dependencies and a real change of the Python version are not shown by it.
