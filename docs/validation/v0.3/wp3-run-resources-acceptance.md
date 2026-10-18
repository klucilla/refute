# WP3 addendum: the resources of a container (shared memory, out of memory, base image)

Addendum to [wp3-acceptance.md](wp3-acceptance.md) (W3.8 to W3.10b, the docker backend and
the build ladder), committed before its tests and code (plan section 11). Three generic
rules of the engine, the same for every paper, found by the budget measurements of the main
sample on the VM (2026-10-18; the maintainer's decision 5: generic, deterministic rules,
written before the code freeze, never a choice per paper). The design was reviewed by Codex
before the code; its objections are in the text below.

## 1. Shared memory (`/dev/shm`)

Docker gives a container 64 MiB of `/dev/shm`. The measurement of 2305.19518 ended at once
with "DataLoader worker is killed by signal: Bus error ... out of shared memory": PyTorch
data loaders with workers pass batches through `/dev/shm`. A limit of the isolation, not of
the artifact.

- **Rule.** Every container gets `--shm-size` equal to a quarter of its memory limit (3 GiB
  of 12). This is a ceiling of `/dev/shm` of its own; nothing is reserved in advance, and
  the pages used count in the container's memory cgroup, shared with the rest of the run
  (and with the 1 GiB `/tmp` tmpfs of a run).
- **Boundary.** A run that fills `/dev/shm` (or `/tmp`) without an OOM kill fails with a bus
  error or "no space left" and `oom_kill 0`: rule 2 does not cover it, and no specific
  evidence lets the engine tell it from the artifact's own failure; it follows the existing
  rules. Recorded as a limitation (#59).
- Implemented in 2ce9a5b (`docker_backend._create_args`); its test checks the flag.

## 2. A kill for memory is a guard of Refute, never the artifact's failure

The measurement of 2305.19518 then reached the memory limit at the start of its second epoch
(peak 12,885,000,192 bytes; `memory.events`: `oom_kill 1`) and ended with exit code 137.
Today a run that ends with a non-zero exit code is `Outcome.FAILED`
(`orchestrate._outcome`), which counts as the artifact's failed procedure. The memory limit
is Refute's (V4 terms).

- **Preconditions** (checked, otherwise a Refute error): cgroup v2 with the systemd driver,
  the memory controller enabled in the container's slice, and `memory.events` aggregating
  its descendants (no `memory_localevents` mount option); the container's slice is new and
  exclusive (`refute-<paper>-cNNNN.slice`, refused when it exists, as today).
- **Rule.** After the container ends and its slice holds no process (the point of the final
  `cpu.stat` reading), the backend reads `oom_kill` in the slice's `memory.events`. When the
  run was not stopped by another guard, ended with a non-zero exit code, and `oom_kill` is
  above 0, the result is stopped with the reason `out_of_memory`, a known stop: its outcome
  is `OPERATIONAL_GUARD`, never `FAILED`. For this stop only, the observed exit code is kept
  in `exit_code` (for the other stops it stays `None`), and no detection delay or stop
  latency is recorded (the stop was not Refute's request). The `oom_kill` count is recorded.
- This does not show that the kill caused the exit; it prevents a run touched by a kill for
  memory from counting as the artifact's failure. It classifies that run only: a negative
  conclusion already established with its prerequisites stays (docs/verdicts.md).
- A run that ends with exit code 0 although a process of it was killed for memory keeps
  `COMPLETED` (the command ended); the count is recorded.
- An unreadable `memory.events`, a missing `oom_kill` key or an invalid count, after a
  non-zero exit, is a Refute error, never read as 0.
- **Builds.** `classify_build` treats the `out_of_memory` stop as an operational guard, as
  it already treats exit 137. A run ending with 137 and `oom_kill 0` stays `FAILED`: 137
  alone is not evidence of a kill for memory (a build keeps its existing rule for 137).
- **Cases.** Must pass: exit 137 and `oom_kill 1` → stopped `out_of_memory`,
  `OPERATIONAL_GUARD`, exit code 137 kept; exit 1 and `oom_kill 1` (a worker killed, the
  main process raised) → the same; exit 1 and `oom_kill 0` → `FAILED`; exit 0 and
  `oom_kill 1` → `COMPLETED`, the count recorded; a build stopped `out_of_memory` →
  operational. Must fail: a non-zero exit with an unreadable `memory.events`, a missing key
  or an invalid count → a Refute error.

## 3. The base image is the engine's single pinned image

The pinned images of the claims so far are Debian trixie (glibc 2.41). Older PyTorch wheels
(1.7.1 for 2305.19518, 1.12.1 for 2302.12465) mark `libtorch_cpu.so` as needing an
executable stack, which glibc 2.41 refuses ("cannot enable executable stack"); on Debian
bookworm (glibc 2.36) they load.

- **Rule.** The base image of the `requirements_compiled` rungs is the engine's single
  pinned image, `python:3.12-slim-bookworm` by digest
  `sha256:34386ef0cb081344d7ec1c103ba398e6e9f64e9ab3a1509accc92a4e24a07258` (pushed
  2026-10-06, over 7 days before it was pinned; read from the Docker Hub API on
  2026-10-18); `uv` installs the rung's Python version into it, as today. A claim's
  `build.base_image` must equal it (refused otherwise, at validation). A change of the image
  is a change of the engine (its code hash), made before a code freeze, never per paper.
  The `own_environment` rung keeps the pinned micromamba image.
- **Limit of support.** The platform is glibc 2.36: a wheel tagged `manylinux_2_38` or later
  cannot be installed, and installing another Python with `uv` does not change the system's
  glibc. A build that fails because no distribution matches the platform is a limitation of
  Refute, not the artifact's failed procedure: when the resolver's message names the
  platform (uv's "no wheels with a matching platform tag" or a hint listing the platforms
  that have wheels), the rung ends as a Refute error (the ladder stops, the gate
  `INCONCLUSIVE`); an ambiguous resolver failure stays as today. A wider platform comes
  through this table, versioned, before another code freeze.
- **Written claims.** A claim already written keeps its bytes. The current code validates a
  claim when it loads it, so the development claim of 2304.14390 (a trixie image) no longer
  validates under this rule; it is a closed development record, verified with the code of
  its own commit, and no claim of the main sample has been locked.
- **Cases.** Must pass: a claim with the engine's digest; a resolver failure naming the
  platform → a Refute error. Must fail: a claim with another image; with no image.

## 4. Regression

Every existing backend, orchestrator and production test passes, with the stand-in cgroup
tree given a `memory.events` file where a test needs one.
