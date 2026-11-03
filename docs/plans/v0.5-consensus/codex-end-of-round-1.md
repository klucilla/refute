## Round verdict: WEAKENED

Reviewed `main` at `0deb97fe1c8c5221e6926a2313c654d096fd8684`, covering the three commits after `1ffe0e5`. **No files were modified and pytest was not run.** Small, in-memory Python probes confirmed the sensitivity bypasses below.

The phase structure survives, but the cleanup safety claim and sensitivity enforcement need repairs.

## Findings

### 1. Critical: a redirected `.cache` defeats repository containment

**Location:** [tests/conftest.py:105](C:/Projetos/refute/tests/conftest.py:105)

Both the deletion root and target are resolved. If the repository’s `.cache` is a symlink or junction to an external directory, `base` becomes that external directory. Its `test-name/<uuid>` descendants then pass the guard and can be recursively deleted.

Other path cases:

- With an ordinary, stable `.cache`, a group or leaf link resolving outside it is rejected.
- A leaf link resolving to another valid UUID directory inside `.cache` can delete that destination, despite it not being the allocated directory.
- Relative paths are accepted whenever their resolved destination matches the pattern. Allocation ownership is not checked.
- Nonexistent paths are resolved non-strictly. That alone does not escape containment, but it does not validate ownership either. The function can subsequently remove an empty group directory.
- Validation and deletion are separate operations, leaving a path-replacement race.

**Concrete fix:** anchor containment to the repository root, reject symlinks/junctions in the cache ancestry, verify exact allocation ownership, and delete the validated literal allocation rather than substituting its resolved destination. Protect against path replacement during deletion where supported.

This violates CLAUDE.md’s required protection against deletion outside the project.

### 2. Important: results can lower their own required detection probability

**Location:** [sensitivity.py:78](C:/Projetos/refute/src/refute/core/sensitivity.py:78)

The validator accepts any positive `required_probability` up to 1. A result with:

```text
probability = 0.10
required_probability = 0.05
detectable = true
```

retains **PASS**, confirmed by a probe. The declared engine requirement is 0.95.

**Concrete fix:** enforce `REQUIRED_PROBABILITY` centrally, or obtain the requirement from trusted registry configuration. Reject a result block that disagrees.

### 3. Important: an empty registry entry bypasses all sensitivity checks

**Location:** [sensitivity.py:94](C:/Projetos/refute/src/refute/core/sensitivity.py:94)

With `registry = {"x": {}}`, a fatal PASS without any sensitivity block remains **PASS**, confirmed by a probe. `_refusal()` rejects `None`, but an empty mapping executes no checks.

`registry_problems()` catches this separately, but enforcement should not depend on callers having performed that validation.

**Concrete fix:** reject empty entries in `_refusal()` and validate registry structure before enforcement. Add fatal and warning cases for empty entries.

### 4. Important: malformed blocks are not fully rejected

**Location:** [sensitivity.py:65](C:/Projetos/refute/src/refute/core/sensitivity.py:65)

Only three numeric fields and `detectable` receive substantive validation. A block containing `effect=NaN`, `unit=None`, and an empty `rule_id` retains **PASS**, confirmed by a probe. Category reasons may likewise be empty or malformed.

A truthy non-mapping outer `sensitivity` value instead crashes at `.get()`.

**Concrete fix:** validate the outer mapping, require nonempty strings for descriptive identifiers and reasons, and reject malformed blocks with an INCONCLUSIVE result rather than an exception.

### 5. Important: simulation silently turns invalid rejection outputs into detections

**Location:** [sensitivity.py:194](C:/Projetos/refute/src/refute/core/sensitivity.py:194)

Casting rejection outputs directly to Boolean hides invalid values. A rejection callback returning an array of NaNs produces **probability 1.0**, confirmed by a probe.

`gaussian_probability()` also omits threshold validation: `threshold=-inf` returns 1.0. Its formula is otherwise correct for its documented one-sided Gaussian model. `1.645` is a rounded power quantile, so the stated equivalence is approximate.

**Concrete fix:** require an actual Boolean rejection array before conversion, validate a positive integer draw count, and require finite Gaussian inputs, including the threshold.

### 6. Important: cleanup ownership does not reliably follow fixture lifetime

**Location:** [tests/conftest.py:129](C:/Projetos/refute/tests/conftest.py:129)

Ordinary module/session fixtures initialized before the function autouse fixture are retained until session finish. That normal ordering is safe.

However, a wider-scoped fixture requested dynamically during a test can allocate after `start` was captured. Its directory is then deleted at that test’s teardown although the fixture remains alive for later tests.

There is also no final failure check after five unsuccessful deletion attempts. The allocation has already been popped, so session finish cannot retry it and the suite can finish with leftovers.

**Concrete fix:** attach cleanup to the owning fixture’s finalizer, with explicit function/module/session ownership. Keep failed removals registered and report unresolved cleanup failures.

### 7. Important: C1’s generator is not fully frozen

**Location:** [v0.5-acceptance.md:341](C:/Projetos/refute/docs/plans/v0.5-acceptance.md:341), [line 358](C:/Projetos/refute/docs/plans/v0.5-acceptance.md:358)

The target-SNR depth calculation is circular as specified:

- Depth determines radius ratio.
- Radius ratio determines duration.
- Duration determines cadence count and correlated-noise variance.
- Those quantities determine the depth needed for target SNR.

Calling this a closed-form depth solution does not supply a deterministic procedure. Partial-window treatment is also unspecified. EB1/EB2 do not fully define their geometry, PX lacks explicit period/geometry inheritance, and PA’s brightening duration and peak do not define its time profile.

**Concrete fix:** specify a bounded deterministic numerical solution with tolerance and failure handling, or an explicitly defined reference-duration approximation. Define partial-window weighting and complete each family’s parameter inheritance and artifact profile before C1 implementation.

## Round-3 corrections A to H

These ratings concern **revision 1’s specification**, separately from implementation defects.

| Correction | Status | Assessment |
|---|---|---|
| **A** | **APPLIED** | Full rejection regions, alternatives beyond effect boundaries, simulations and worst eligible locations are specified. |
| **B** | **APPLIED** | Malformed-block rejection, registered categories, background-rise sensitivity and both plausibility branches are required. Implementation remains incomplete, findings 2 to 4. |
| **C** | **APPLIED** | Secondary dips and sinusoid failures are warning-only in v0.5. Historical fatal behavior is isolated. |
| **D** | **APPLIED** | Controls measure centroid shifts, use actual transit depth, exclude overlaps, require enough controls and retain sky-frame covariance. |
| **E** | **APPLIED** | Low-power cases allow detected failures; boundary case 1.9 exists; measured-window distinctions and statistical requirements were added. |
| **F** | **APPLIED** | Conventions and adaptations are labelled; the beyond-ten-event extension receives explicit cases. This is specification adoption, not scientific validation. |
| **G** | **PARTLY** | Most generator and cost-projection details were added, but finding 7 prevents a fully deterministic freeze. |
| **H** | **APPLIED** | PA is a planet family; identity matching, paired eligibility, denominators, high-SNR subset size and NOT DECIDABLE outcomes are defined. Both survival endpoints are reported. |

**Minor finding:** [v0.5-acceptance.md:9](C:/Projetos/refute/docs/plans/v0.5-acceptance.md:9) and [consensus/README.md:20](C:/Projetos/refute/docs/plans/v0.5-consensus/README.md:20) overstate that A to H were applied “in full.” Correct that record and track the remaining G clarification under the existing escalation rule.

## ROADMAP and compatibility checks

**ROADMAP preservation passes.** The diff removes no substantive previous-phase or future-phase content. The replaced lines are the three renumbered headings and the cross-cutting Refute@Home reference, with historical numbering notes added.

The current phase is clearly v0.5. The previous v0.4 block is explicitly historical, with a later release-completion note. Its retained “release pending” wording is therefore contextualized rather than silently rewritten. The release’s actual publication was not independently verified outside the repository.

**Earlier `TestResult.to_dict()` output structure is preserved when `sensitivity is None`.** Existing keys, values and insertion order remain unchanged, and the new field is omitted. This supports byte identity under the same serializer. It does not establish end-to-end historical dossier compatibility.

Cases **1.1 to 1.4 and 1.9** have corresponding engine tests, but the probes expose additional untested bypasses. **Case 1.5 is currently a validation helper, not load-time integration.** The commit explicitly acknowledges that TESS/schema wiring comes next, so this is unfinished WP1 work rather than an undisclosed completed feature.

## CLAUDE.md assessment

The cleanup containment defect is the concrete rule violation identified. Protected published records and dependencies were not changed, and the implementation remains within the current phase.

Commit contents alone cannot establish whether required pre-commit checks or maintainer escalation occurred. No test-suite outcome or operational approval is inferred here.

**WEAKENED:** retain the round’s work, but repair deletion containment and sensitivity enforcement before treating either as accepted infrastructure.