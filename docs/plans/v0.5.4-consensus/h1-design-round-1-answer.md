**The approach remains viable, but the design and ledger need corrections before being frozen.** This was a static, read-only review at `d423adc`. I ran no validation code and did not access the prohibited directory.

1. **I1: the classes need a corrected enforcement sequence.**

   - **Coverage currently causes a false class (iii).** [design:82](C:/Projetos/refute/docs/plans/v0.5.4-h1-design.md:82) compares the enforced status with `enforce_sensitivity(raw)`. Actual execution applies coverage first, then sensitivity, then stage deferral ([paired.py:51](C:/Projetos/refute/src/refute/packs/tess/discover/paired.py:51), [forecast_v4.py:83](C:/Projetos/refute/docs/validation/v0.5.2/stage2/forecast_v4.py:83)). A raw PASS with zero coverage can therefore satisfy both the present defect row and the intended procedure row. **Compare against the complete pipeline**, retaining each intermediate result.
   - Validate **every supplied block, including “not applicable” blocks**, against `registry_for(plan)`. The exemption at [design:82](C:/Projetjetos/refute/docs/plans/v0.5.4-h1-design.md:82) misses malformed or forbidden applicability declarations that `block_problem` explicitly rejects ([sensitivity.py:116](C:/Projetos/refute/src/refute/core/sensitivity.py:116)). Missing blocks from a genuinely unrun check remain procedural, rather than automatically becoming defects.
   - After those checks, the intended order is sound: raw INCONCLUSIVE → (ii); coverage refusal → (ii); sensitivity refusal of the remaining PASS → (i); another refusal → (ii); unmatched cases → unresolved. `systematics` gives FAIL precedence over an unrun sub-check, then INCONCLUSIVE, then PASS ([battery_v51_diff.py:557](C:/Projetos/refute/src/refute/packs/tess/battery_v51_diff.py:557)).
   - Listing **all** non-detectable blocks is necessary: `_refusal` returns at the first such block ([sensitivity.py:163](C:/Projetos/refute/src/refute/core/sensitivity.py:163)). However, `dumps` is a categorical `fraction` block, without probability or `detectable`; SAP and background carry statistical sensitivity ([power.py:64](C:/Projetos/refute/src/refute/packs/tess/power.py:64)). Freeze that distinction explicitly.

   **B-only rerunning is faithful:** B1 reuses `v4A` through four sectors; otherwise its B outcome uses `v4C` through twenty, with the refusal override restored afterward ([b1_b14.py:155](C:/Projetos/refute/docs/validation/v0.5.3/stageB/b1_b14.py:155)). Separate `Version5` contexts reset their counters, so the omitted A attack is not a required precursor.

   **The reproduction check is necessary but insufficient for input identity.** Retain B1’s v0.4 compatibility check and final-candidate equality check ([b1_b14.py:143](C:/Projetos/refute/docs/validation/v0.5.3/stageB/b1_b14.py:143), [b1_b14.py:173](C:/Projetos/refute/docs/validation/v0.5.3/stageB/b1_b14.py:173)). Freeze input hashes, decisive-test membership and stage handling before reading. Also resolve the population wording: class-(i) D2 cases are a diagnostic subgroup; **I4’s L must still use all 178 eligible planets**, as specified at [design:112](C:/Projetos/refute/docs/plans/v0.5.4-h1-design.md:112).

2. **I4: the Fisher structure is right; the numerical derivative rule needs repair.**

   The two depth columns, four shared shape derivatives, sector intercepts, known multiplicative trend and per-sector white-plus-exponential covariance match the stated model ([c1.py:371](C:/Projetos/refute/src/refute/packs/tess/calib05/c1.py:371), [d2_bounds.py:131](C:/Projetos/refute/docs/validation/v0.5.3/stageA/d2_bounds.py:131)). Freeze the mean explicitly as
   `μ = trend × (1 − d_odd q_odd − d_even q_even) + sector levels`,
   evaluated at both depths equal to truth. No additional common-depth column is needed.

   With depths first, partitioning F gives `S = Fdd − Fdn Fnn⁻¹ Fnd` and **variance** `(1,−1) S⁻¹ (1,−1)ᵀ`; its square root is σ. Thus [design:135](C:/Projetos/refute/docs/plans/v0.5.4-h1-design.md:135) has the correct formula, but “this is the inverse” needs that qualification.

   **The frozen period step is unsafe.** At `hP/P = 10⁻⁴`, distant transit centers move approximately `10⁻⁴ × baseline`. The generator permits roughly 800 days of separation, hence about 0.08 day, enough to cross trapezoid contacts ([c1.py:50](C:/Projetos/refute/src/refute/packs/tess/calib05/c1.py:50), [synthetic.py:91](C:/Projetos/refute/src/refute/packs/tess/synthetic.py:91)). Freeze analytic derivatives or a baseline-aware step and predetermined convergence check; failed convergence enters E. Do not select a step after inspecting L.

   **E and the unresolved band are logically sound**, provided invalid cases are excluded from L. Add non-positive variance, non-finite power/F entries, failure of positive definiteness and derivative instability. Specify column scaling before the condition-number test: raw F’s condition number depends on parameter units ([design:147](C:/Projetos/refute/docs/plans/v0.5.4-h1-design.md:147)).

   **The integer threshold is correct:** `173 − 0.10×178 = 155.2`, requiring 156 kept; 23 losses leave at most 155. Excluding sinusoid from L also faithfully preserves stage A’s optimistic recoverability treatment ([d2_bounds.py:30](C:/Projetos/refute/docs/validation/v0.5.3/stageA/d2_bounds.py:30)). This does not mean warning INCONCLUSIVE is harmless in actual aggregation.

   **Version 5’s final attack candidate is the correct depth source**, rather than truth depth or the search candidate ([power.py:97](C:/Projetos/refute/src/refute/packs/tess/power.py:97)). Keep the conclusion conditional on the stated Fisher/Gaussian model; Fisher covariance calculations do not establish universal finite-sample power. [Carter et al.](https://arxiv.org/abs/0805.0238) likewise presents uncertainty approximations under specified transit assumptions.

3. **Ledger: two material defects and one incomplete safeguard.**

   - **Import-order hazard:** `ledger_i` binds shared `budgeted` globals at [ledger_i.py:62](C:/Projetos/refute/docs/validation/v0.5.4/ledger_i.py:62), but subsequently importing `b1_forecast` imports `ledger_b`, rebinding them to stage B ([b1_forecast.py:29](C:/Projetos/refute/docs/validation/v0.5.3/stageB/b1_forecast.py:29)). Import helpers before the final binding, then assert ledger path, limits and save implementation before every mutation.
   - **Independent-review tokens are recorded but ignored by enforcement** ([ledger_i.py:295](C:/Projetos/refute/docs/validation/v0.5.4/ledger_i.py:295), [ledger_i.py:304](C:/Projetos/refute/docs/validation/v0.5.4/ledger_i.py:304)). Stage B adds them before checking ([ledger_b.py:302](C:/Projetos/refute/docs/validation/v0.5.3/stageB/ledger_b.py:302)). Count ordinary independent sessions in their scopes; separately identify and enforce the expressly additional final 0.35 M allowance.
   - **Disk checking measures current usage only.** Reserve bounded output before dispatch and check afterward, as B1 did ([b1_forecast.py:322](C:/Projetos/refute/docs/validation/v0.5.3/stageB/b1_forecast.py:322)). Otherwise a run starting below 5 GB can exceed it.

   Allocations, CPU sub-cap arithmetic, attempt accounting and hard-cap reserve preserve stage B’s behavior. Locks also preserve it **provided the future caller holds `Exclusive` throughout execution**. Token conversation grouping and agent-day accounting otherwise retain the reviewed convention.

4. **Prices: plausible estimates, with one definite counting error.**

   B1 measured about 64 CPU-s per T2a record through four sectors and 288 for five to twenty, across their respective complete workloads. Completed D2 cost 7.80 CPU-h for 200 records, about 140 CPU-s each ([ledger.json:124](C:/Projetos/refute/docs/validation/v0.5.3/stageB/ledger.json:124), [complete.json:57](C:/Projetos/refute/docs/validation/v0.5.3/stageB/b1-forecast-d2d4-complete.json:57)). These support the proposed order of magnitude, without measuring isolated attacks.

   **I1’s 3–8 CPU-h is plausible. I4’s 3–5 is provisional:** its assumed attacks alone total about 4.03 CPU-h. Moreover, stage A’s polarization makes **k² calls**, hence 100 for ten columns, not 55, before the separate known-template and sinusoid calculations ([d2_bounds.py:104](C:/Projetos/refute/docs/validation/v0.5.3/stageA/d2_bounds.py:104)). Correct the estimate and retain the binding budget stop.

WEAKENED, with corrections to I1 enforcement and identity checks, I4 derivatives and numerical validity, ledger binding and token accounting, disk reservations, and Fisher cost counting.