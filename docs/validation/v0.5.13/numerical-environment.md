# The numerical environment of versions 1 to 4's byte identity (sidecar, dated 2026-11-27)

Amendment 2, revision 4 (adopted, #218 comment 7222329150, item I1), section 2; prepared under
decision I2(b). Labels: `exploratory`, `method_status: not_validated`.

**What this is.** Versions 1 to 4 get no change of code, pin or configuration. Their byte-for-byte
identity was observed in two executions on one machine:
- ID-BEFORE;
- NR-A1's inherited default.

It is asserted for those executions' recorded numerical environment, and for no other. This sidecar
enters the reproduction recipe of each locked claim.

**How each value got here.** Every value below is copied from an existing committed record, named
with the SHA-256 of its committed blob. A value the record does not hold is written as "not
recorded by ID-BEFORE". Nothing was measured again or inferred. No lock, dossier, tag or recorded
byte is edited.

## The records

| Record | Role | SHA-256 of the committed blob |
| --- | --- | --- |
| `docs/validation/v0.5.13/step0/golden-before.json` | ID-BEFORE's golden record: payload and `provenance` | `5eaf5424df933682d881c83abc0938de7f237a68f2b40f1a3ddcbf1f4b5229a8` |
| `docs/validation/v0.5.13/step0/claim-hashes-before.json` | ID-BEFORE's claim-hash record | `581234e23531d2369397c3c5b1e15699346a2ac64219cfde9596f6a569485a5f` |
| `docs/validation/v0.5.13/manifests/id-before.json` | ID-BEFORE's manifest | `da4bec38b14f0cea40bfbb783ac2223469c1527e1170fcd43b4b2231a5e1bfc3` |
| `docs/validation/v0.5.13/step1/golden-nr-a1-default.json` | NR-A1's inherited-default golden record | `c467c67237a7a36e36a18eb8ee0057d89de1ee80526403a0ce194ca8d963ea89` |
| `docs/validation/v0.5.13/log.jsonl`, line 59 (append-only) | the `after` entry of the unit `id-before-tags` (attempt `57d208ff628d4a2e8dd43a381550d02d`, 2026-11-27T00:28:10Z): its stdout, with the joint PASS of the ten checks, by SHA-256 | stdout SHA-256 `d28e95717652d4bbd056ef404f3cfc7fd38f41e6b42d80e08e557189d2edf642` |

The raw goldens of both executions are committed under `docs/validation/v0.5.13/goldens/before/`
and `goldens/nr-a1-default/`. Each file's SHA-256 equals its record (unit `golden-commit`, I2(a)).

## The environment (copied from `provenance` of `golden-before.json`)

| Item | ID-BEFORE | NR-A1 inherited default |
| --- | --- | --- |
| Source commit (`head`) | `a150096de04e4caae9ef0042e6ae4c458823ac9e` | `ce154119c7f05ee4d317e13eecc9b0fd0edb9476` |
| Python | 3.13.16 | 3.13.16 |
| NumPy | 2.5.3 | 2.5.3 |
| SciPy | 1.18.1 | 1.18.1 |
| `system` | Windows | Windows |
| The identity script's SHA-256 (`script_sha256`) | `3109ed581c8dfc8db58461dd9bd8ae8371f093f23a5915e40de0678074d29450` | the same |
| Inherited thread variables (`OMP_NUM_THREADS`, `OPENBLAS_NUM_THREADS`, `MKL_NUM_THREADS`) | all unset (`null`) | all unset (`null`) |
| BLAS library 1 (`child_threadpool_info`) | `openblas`, `libscipy_openblas`, version `0.3.34.106.0`, `pthreads`, 24 threads | the same |
| BLAS library 2 (`child_threadpool_info`) | `openblas`, `libscipy_openblas`, version `0.3.31.dev`, `pthreads`, 24 threads | the same |
| `NUMEXPR_NUM_THREADS` | not recorded by ID-BEFORE | not recorded |
| OS version | not recorded by ID-BEFORE (`provenance` holds `system` only) | not recorded |
| Processor affinity | not recorded by ID-BEFORE | not recorded |
| Processor model | not recorded by ID-BEFORE | not recorded |
| OpenBLAS kernel | not recorded by ID-BEFORE | not recorded |

**Two notes, from the records themselves:**
- **The effective thread counts come from a companion process.** `child_threadpool_info` is read by
  a child interpreter that imports NumPy and `scipy.linalg` under the same thread variables
  (`docs/validation/v0.5.13/tools/identity.py`, lines 37 to 55). They do not come from the process
  that produced the goldens (amendment 2, decision H2(h)).
- **The affinity is planned, not recorded.** ID-BEFORE's manifest states the planned environment of
  the golden unit: "processors 8 to 31, BelowNormal (the job object)". That is the plan, not a
  value the execution recorded, so the table keeps "not recorded by ID-BEFORE".

## Each locked claim and tag, mapped to ID-BEFORE

The resolved claim hashes are copied from `claim-hashes-before.json`
(`581234e2…`, full above). The ten locked checks are those of `scripts/verify_locked_tags.py`. Their
joint PASS is the stdout of `id-before-tags`, by its SHA-256 (journal line 59).

| Locked tag | Claim | Resolved claim SHA-256 (ID-BEFORE) |
| --- | --- | --- |
| `v0.1.0` | `calibration/self_claim.yaml` | `f88521edaa2bb645f2aa890dc3a0c23bcbd405611582444e983b485be13232dc` |
| `v0.2.0-calibration-lock` | `calibration/v0.2/self_claim.yaml` | `3bfa36a392089040385c187155cae5bc1a41dece42e928a8b38654f7c37a5514` |
| `v0.3.0-main-lock` | `calibration/v0.3/main/claims/2302.12465/claim/claim.yaml` | `cb7720a2fd3dc4d95315bc2ea04829c10060992f1f3c6739d30ce24e614cd6c6` |
| `v0.3.0-main-lock` | `calibration/v0.3/main/claims/2305.19518/claim/claim.yaml` | `ff1ac0933507882c63178a9fa7e7d5b0c82279a7ee758b9ac6bdbec9e8403424` |
| `v0.3.0-main-lock` | `calibration/v0.3/main/claims/2309.15704/claim/claim.yaml` | `598543893374b9c4742d44f25bbaf7fa89cbc3f2faf7f4e857c2359a91b34957` |
| `v0.3.0-main-lock` | `calibration/v0.3/main/claims/2407.11735/claim/claim.yaml` | `dcea7ed105a99f336a124db706d1683d058b12fb8b1a2979bc838ede9a25a34f` |
| `v0.3.0-main-lock` | `calibration/v0.3/main/claims/2502.16782/claim/claim.yaml` | `3e59b8353da037e57d03b68817c7b01c947e06ef113555c8b79f4ec842b857ab` |
| `v0.4.0-pilot-lock` | `calibration/v0.4/claim.yaml` | `d2ce83808eb026189fa76b83533aeca8b98e81ad5dff92b17e4cfa7a83eb61d5` |
| `v0.5.0-calibration-lock` | `calibration/v0.5/claim.yaml` | `48acfe245a7231c35353319212324574d408be493c3c53d062ea02adfbd00210` |
| `v0.5.6-partb-lock` | `calibration/v0.5.6/claim.yaml` | `d451e995eae3f12afda0e5d807f5c5516c16c8bc1094b6d72c1623e5528b749f` |

**The baseline exception** (amendment 2, section 3.1): `calibration/v0.5/deviation/claim.generated.yaml`
has an error record instead of a hash, line 18 of `claim-hashes-before.json`. It supplies no claim
hash and is kept byte for byte.

**To reproduce a locked claim's verdict byte for byte,** use the recorded environment above. In
any other numerical environment, the reproducibility criterion is decision identity (amendment 2,
sections 3 and 4).
