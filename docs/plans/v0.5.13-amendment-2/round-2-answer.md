## 1. Verdict

**`NOT_APPROVABLE` for submission to blind review, round 2.** The fresh-child design fixes the in-process and parent-environment problems from round 1. The remaining blockers are worker evidence, verification of the installed code and numerical stack, test coverage, the missing v5 integration diff, and how new margin evidence would be joined to the historical goldens.

I verified all four patch hashes and reconstructed the proposed files in memory from the patch hunks. I did not run the tests, apply patches, modify files, or access the network.

## 2. Blocking items

### 1. Bind each result to the actual child and retain failure evidence

**Where:** [Proposed runner, lines 228–268](C:/Projetos/refute/.cache/v0513/d1b2/src/refute/core/runner.py:228), [proposed worker, lines 66–89](C:/Projetos/refute/.cache/v0513/d1b2/src/refute/core/pinned_worker.py:66), [amendment §4.2](C:/Projetos/refute/docs/plans/v0.5.13-charter-amendment-2.md:181).

The runner records `proc.pid` as `launcher_pid` but never checks it against `out["pid"]`. It accepts any value under `startup`, including an empty list. Fixed shard filenames allow overlapping batches to overwrite one another. The parent skips the child’s refusal record on a nonzero exit, and malformed output can escape as an exception other than `BlasPinError`. The first `pickle.load` also has no plain-data restriction.

**Replace the implementation contract in §4.2 with:**

> Each call creates an exclusive batch directory under the supplied work directory. The protocol carries a run ID, batch ID, shard index and one-time shard nonce. Use JSON for the launch header and for startup, refusal and result-index metadata. Read the task pickle only after writing the verified startup record. Restrict task and result pickles to trusted local inputs and children in that batch directory.
>
> The parent requires exactly one valid startup record per launched child. Its run ID, batch ID, shard index and nonce must match the launch record, and its PID must equal `proc.pid`. Require the exact launch variables, a complete verified library inventory, exit status zero, and the exact ordered shard task indexes, each attached to the same PID. Require distinct child PIDs and full task coverage. Decode results only after validating the corresponding metadata.
>
> Persist startup and failure evidence independently of successful results. A missing or malformed record, refusal, launch failure, or partial result rejects the batch with `BlasPinError`. On orchestration failure, terminate and reap any children still running. Accept no result from an incomplete batch.

A nonce identifies a shard. **A shared run and batch ID** is required to join the records across shards and to the v5 execution manifest.

### 2. Bind the isolated interpreter to the reviewed code and a nonempty BLAS inventory

**Where:** [Proposed runner, lines 233–242](C:/Projetos/refute/.cache/v0513/d1b2/src/refute/core/runner.py:233), [proposed worker, lines 26–81](C:/Projetos/refute/.cache/v0513/d1b2/src/refute/core/pinned_worker.py:26), [amendment §4.4, lines 221–224](C:/Projetos/refute/docs/plans/v0.5.13-charter-amendment-2.md:221).

`-I -B -m` is sound **with a verified installation**. `-I` ignores `PYTHONPATH` and the working directory for module discovery, so a staged file alone does not select the reviewed package. It still runs normal site initialization. The explicit child environment is present from process creation, but the worker’s first check cannot establish that it preceded a numerical import during site startup. Separately, `check([])` succeeds if the inspector returns `[]`. The current identity tuple also omits the threading layer and cannot distinguish different binaries reporting the same prefix and version.

**Replace §4.2’s launch and inventory bullets with:**

> Launch the isolated interpreter from the frozen v5 environment. Bind its executable, installed Refute artifact, worker module and approved task modules to the reviewed source and artifact hashes. Verify the resolved installed code before dispatch and include its identity in the child evidence. An isolated environment containing a verified installation of the proposed package can exercise the patch from any checkout.
>
> Pass the pin variables at process creation. At worker entry, before reading the task payload or loading the numerical stack, verify the variables and refuse an environment that has already imported the numerical stack during startup. Load NumPy and `scipy.linalg` explicitly. Require a nonempty frozen manifest that identifies the approved BLAS provider for each numerical path and the expected loaded libraries. Bind each reported library by backend, prefix, version, threading layer and binary identity. Refuse an absent, unexpected or unverifiable library, or any count other than integer one. Recheck after task deserialization and before and after every task.
>
> The initial supported numerical paths are NumPy and SciPy. Before accepting a v5 task path, bind its numerical providers in the manifest. If it needs another provider, extend and verify the manifest before accepting that path.

The lack of additional providers is **not itself blocking** if the actual v5 path is shown to use only the supported providers.

### 3. Make the tests exercise the launched-child contract

**Where:** [Proposed tests, lines 19–67](C:/Projetos/refute/.cache/v0513/d1b2/tests/test_runner_blas_pin.py:19), [negative tests, lines 75–130](C:/Projetos/refute/.cache/v0513/d1b2/tests/test_runner_blas_pin.py:75), [amendment §4.4](C:/Projetos/refute/docs/plans/v0.5.13-charter-amendment-2.md:210).

The positive test compares the recorded and task-reported PIDs but omits `launcher_pid`. Its inventory assertion repeats the same discovery mechanism and can pass on an empty inventory. There is no import-time child fixture. Three negative cases patch functions in the pytest process and never reach the isolated child. The `os._exit(0)` test is useful, but any earlier child failure also satisfies its generic `pytest.raises`.

**Replace the claim that the patch has one test for each requirement with:**

> The dedicated v5 test manifest selects `blas-pin`, verifies the installed proposed artifact, and requires every pin test to run without a skip. Use a fixture importable in that isolated child to report the launch variables at its first import. Assert one startup record per launched PID, equality of launched, recorded and task-executing PID sets, exact task-index coverage and result order, and a nonempty inventory covering the independently identified NumPy and SciPy providers. With conflicting variables and loaded BLAS in the parent, verify that the single-task child is pinned and that the parent environment, loaded BLAS counts and legacy runner behavior are preserved.
>
> Through a real child running the worker entry point, exercise missing verification support, an absent or wrong-count second library, and invalid launch variables. Require the expected refusal, no accepted results, and evidence that task execution did not begin. Separately exercise a clean child exit without a startup acknowledgement. Keep the `os._exit(0)` case and require a verified startup record and exit status zero followed by rejection specifically for the missing result. Also test a reported PID that differs from the launched PID.

### 4. Resolve the v5 integration and sequencing before calling the package complete

**Where:** [Amendment §4.2, lines 164–192](C:/Projetos/refute/docs/plans/v0.5.13-charter-amendment-2.md:164), [§5, lines 242–267](C:/Projetos/refute/docs/plans/v0.5.13-charter-amendment-2.md:242), [§7](C:/Projetos/refute/docs/plans/v0.5.13-charter-amendment-2.md:276), [approved charter, Part A order](C:/Projetos/refute/docs/plans/v0.5.13-charter.md:44).

The four patches provide a runner and worker, with no actual version-gated v5 dispatch, durable evidence sink, or v5 acceptance fixture. Deferring persistence to Part B leaves criterion 1 dependent on work deferred until after criterion 1 passes. The charter puts calibration and the frozen candidate in Part B. It does not expressly assign every v5 caller to Part B. The blocker is the absence of an authorized and prepared route to the required verification.

**Replace §4.2’s persistence deferral, §5’s sequencing note and the corresponding §7 entry with:**

> The runner protocol is preparation only. The package for blind review must include the exact diff for the actual version-gated v5 entry point, its durable startup, task and failure evidence, and the synthetic acceptance fixture and alternate-setting verification harness identified in criterion 1. The source and execution stops apply to those artifacts. The alternate-setting harness supplies its own effective-count evidence while using the same frozen scientific code, inputs and configuration.
>
> The maintainer must resolve whether this limited synthetic v5 verification may be prepared and run during Step 1 under separately authorized exact diffs and manifests. If that route is unavailable, #226 remains stopped and a separate sequencing proposal requires fresh blind review. Part B calibration remains behind Part A. Runner tests, a proposed persistence contract or a planned Part B caller cannot satisfy criterion 1.

### 5. Bind newly measured margin operands to the golden outputs they certify

**Where:** [Amendment §3.3, lines 121–132](C:/Projetos/refute/docs/plans/v0.5.13-charter-amendment-2.md:121), [§5 item 2, lines 237–241](C:/Projetos/refute/docs/plans/v0.5.13-charter-amendment-2.md:237).

The revision correctly preserves missing operands as an unmet check. It still requires the *existing* records to pass while allowing operands from a new measurement, with no rule binding those operands to the golden bytes they would certify. This applies to the ID-BEFORE side as well as the 1-thread and 4-thread sides.

**Append to §3.3 and cross-reference it in §5 item 2:**

> Where a historical golden omits a required operand, any separately approved supplemental execution must capture the trace and its corresponding golden outputs together. Freeze the case, scientific source, resolved configuration, numerical environment and trace instrumentation in the order-proof manifest. Use the trace to assess a historical golden only when its corresponding raw output matches the historical output byte for byte at that setting. Apply this binding to the reference and each comparison setting. A missing trace or mismatch leaves the historical check unmet. Preserve all original records and report supplemental evidence separately.

## 3. Non-blocking items

- **The dependency diff is correct as prepared.** It adds the pinned `blas-pin` extra and the corresponding lock metadata. It leaves the existing `threadpoolctl` resolution and other package versions intact. The exact §12 exception and execution approvals remain separate stops. [Dependency patch](C:/Projetos/refute/docs/plans/v0.5.13-amendment-2/r2-dependency.patch:1), [exception request](C:/Projetos/refute/docs/plans/v0.5.13-charter-amendment-2.md:194)
- **Keep the round 1 scientific wording.** The typed comparator, disclosed post-hoc `1e-6` engineering budget, threshold rule, and historical F-1 limit are carried forward. I found no change to amendment 1’s population or gate. In §3.2, say “the first amendment draft proposed `1e-6`” to avoid attributing that value to the maintainer’s D1b decision. [Tolerance wording](C:/Projetos/refute/docs/plans/v0.5.13-charter-amendment-2.md:80), [amendment 1](C:/Projetos/refute/docs/plans/v0.5.13-charter-amendment-1.md:72)
- **Pin the review index to an immutable patch base.** The full patch hashes match. Record the generation commit beside them so `HEAD` cannot become ambiguous when the proposal is committed. [Review index](C:/Projetos/refute/docs/plans/v0.5.13-amendment-2/README.md:10)