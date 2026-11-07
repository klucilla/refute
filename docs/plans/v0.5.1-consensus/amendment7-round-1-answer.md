## A. Amendment 7 and acceptance wording

**Verdict: WEAKENED**

1. **Major.** The plan states the byte-identity exception for processor-time and task-identity fields, but acceptance row 5.2 says simply “byte-identical.” That leaves the gate’s actual pass criterion ambiguous.  
   **Evidence:** Amendment 7, plan lines 564–569; acceptance row 5.2.  
   **Required change:** Put the exception directly in row 5.2, and say that `check-dossier --against` is also reported.

2. **Minor.** The locked-tag reproduction requirement is coherent across the documents, but the plan alternates between “locked commit” and “locked tag.” The decision requires the proof to be run at the locked tag using that dossier’s `REPRODUCE.md` procedure.  
   **Evidence:** Amendment 7, plan lines 557–563; acceptance row 5.2.  
   **Required change:** Use the same formulation in both places: reproduce v0.1 at its locked tag, following its `REPRODUCE.md` procedure, and report the comparison.

The decision itself is represented correctly: v0.1 is reported separately, row 5.2 covers v0.2, v0.4 and v0.5, and the stop-and-separate-cause rule is present.

## B. v0.2 result

**Verdict: SURVIVED**

Claude’s classification is right, with one distinction to keep explicit: **v0.2 fails the byte-identity criterion, so the stop rule applies; the 13 added keys are not changes introduced by v0.5.1.**

The two retrieval-time differences reflect today’s TIC query. The other 13 differences are defaults and their output fields: the five plan defaults, holdout validity metrics, and TESS-EB downgrade metrics and thresholds. The cited commits date to October 10 and 18, before the v0.5.0 lock. The `src` changes after `b6249b5` add the v0.5.1 plan section and discovery version 3 behavior; they do not change those five defaults.

`check-dossier --against` passing confirms that the verdict, statuses, key values and input hashes match under that comparison rule. It does **not** satisfy the separate byte-identity requirement. The appropriate disposition is to stop before running v0.4 or v0.5 and send the v0.2 failure and its cause to the maintainer. Call the 13 fields **pre-existing default reinterpretation**, not a v0.5.1 code change.

## C. Issue #213, silent reinterpretation

**Verdict: WEAKENED**

1. **High.** Three of the five v0.2 defaults can affect test status, and some can affect the verdict. `same_photometry_catalogs` can downgrade a matching TESS-EB result from a fatal warning to a non-independent-evidence warning. `require_valid_train` can make a holdout round INCONCLUSIVE; the duration-period and hidden-window-fraction limits can also change whether the train candidate is valid and the holdout status. The recorded v0.2 dossier’s verdict reason is `holdout_by_year`, so these fields are relevant to the result, even though this run’s comparison reports matching statuses. `corrections: enabled: false` adds configuration data but does not, by itself, change the v0.2 result.  
   **Evidence:** `issue-reinterpretation.md` lists the five defaults; current `params.py` documents their roles; the v0.2 dossier comparison reports matching verdict and statuses.  
   **Required change:** In #213, distinguish fields that can change results from fields that only add bytes, and preserve the actual dossier’s observed result separately from the general risk.

2. **High.** “No added defaults” for v0.4 and v0.5 is supported only for the sampled test plans, not for every claim field or every claim. The checked-in v0.4 and v0.5 C3 claims explicitly specify `data`, `detrend`, `search`, `gauntlet`, `discovery`, and, for v0.5, `stronger`. But `default_drift.py` compares one dossier per version and focuses on the resolved test plan; it does not establish the absence of additions elsewhere in the top-level claim schema or across all v0.5 C2/C3 claim instances. I found a checked-in v0.5 C3 `claim.yaml`, but no separate checked-in C2 `claim.yaml` to inspect.  
   **Evidence:** The two checked-in claim files; `src/refute/core/claim.py` defines defaults for fields including `definitions`, `data_sources`, `attachments`, `targets`, `test_plan`, and `pass_criteria`; the issue’s evidence says its drift check uses one dossier per version.  
   **Required change:** Narrow the issue’s claim to “no additions found in the sampled test plans,” or compare each locked claim’s full canonical form with its current resolution, including the claim schema and each C2/C3 claim, before asserting broader absence.

No files were modified and no tests or write operations were run.

