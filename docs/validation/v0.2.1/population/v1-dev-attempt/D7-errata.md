# D7 — Errata (2026-10-12)

Corrections to `D7-report.md` (the SHA-256 of the report is unchanged; it was not edited) and to
the conclusion message of D7 in the session. Source of the corrections: the consultation of
Codex (`codex-D7.md`, SHA-256 `e3e4dfbd2188510177aec31ac9f4c1756c117fa0e7c30d748de5ca0c56548491`,
not published) and the maintainer's review.

1. **D4** (`D7-report.md`, line 31). Where it reads "No dependence on the history", read:
   **"no dependence was observed in the sequences tested"** (3 cases × 5 declared
   sequences; 1786 sequence cases). The result does not exclude dependence on other
   sequences, other states of the process or of the allocator.

2. **"Only the sha256 differs"** (lines 19 and 22, and the D7 message). The statement holds for
   the **fields of the manifest entry** (seeds, parameters, expected SNRs, draws, size in
   bytes). It does **not** hold for the serialized header of the case: the header also includes
   the catalog of condition (ii), the star, the sectors, the product, the data manifest and the
   auxiliary scalars, which are not in the manifest entry. A difference in those fields
   would not have been seen by the comparison of the manifests.

3. **`d3_compare.py`** (not published). The inequality of the blobs is detected correctly by
   bytes (line 21, `a_blob == b_blob`). The defect is in the **localization**: the numerical
   comparison of the arrays (line 53) treats `0.0` and `-0.0` as equal and treats any two NaN as
   equal, hiding the sign of the zero and the content (payload) of a NaN. A divergence only in
   those bits would be detected in the blob and not located in the array. The localization must
   start from the bytes (offset, segment, field); the numerical and ULP analysis comes after,
   only as an explanation.

4. **Cause.** The cause remains **unknown**. A transient hardware fault **was not
   demonstrated**: it is a hypothesis, not a result. The tests T2a (allocation sentinel) and T2b
   (SIMD and address) found no differences, but **do not rule out these mechanisms in general**:
   T2a does not cover internal allocations of the libraries nor the path of the 3 divergent
   cases; T2b covers only the functions, lengths and offsets exercised. The same holds for the
   tests T3a (floating-point state) and T3b (SHA-256 by an independent implementation).
