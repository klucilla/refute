# v0.5.13 charter: amendment 1 (proposed): the KELT-FP type mix, reported without changing the gate

> **Status** (Codex's round 1 on this amendment, item 4, as written):
>
> > Proposed on 2026-11-26 under #218, comment 7204660147, item 6. Amendment 1 takes effect only
> > after the maintainer's separate #218 approval citing the exact committed amendment SHA, with
> > the amendment linked from the phase record, and before any work that relies on it. Any version
> > that changes an acceptance rule, eligibility or denominator requires a fresh blind review before
> > adoption. This design review is advisory. Part A proceeds under its own charter and stops. Part
> > B and v0.6 require their own authorizations, and the reserved target products remain protected
> > under the approved exposure and lock rules.
>
> - It amends section 5 of the charter approved at `04402e7a` (SHA-256 `2832dc48…c230c813`). The
>   charter file is not edited.
> - **This revision changes no acceptance rule, eligibility or denominator.** It adds a
>   prespecified descriptive report, so a blind review is not triggered by it. Whether that holds
>   is the maintainer's to judge.
> - **Codex:** in a new conversation, with divergence resolved by the more conservative option,
>   recorded in [v0.5.13-amendment-1/](v0.5.13-amendment-1/README.md).
>   - The first draft proposed measuring safety on the 135 non-SB1 FPs only.
>   - Codex found that a relaxation of the approved gate (round 1, `NOT_APPROVABLE`).
>   - Its more conservative replacement is applied below, quoted as written.
> - **Labels:** `exploratory`, `method_status: not_validated`. The counts carry v0.5.10's limits
>   label.

## 1. What was known, and the count (item 6a)

What was known, and the count's provenance (Codex's round 1, item 3, as written):

> The empirical input to this amendment was the catalogue type count from the existing v0.5.10
> census. The preparation log records the count question and counting rules before the count, the
> count afterward, and then the two deterministic planning analyses, first for 124 and then for 135
> FPs. Those planning analyses were available when the recommendation was written. The local
> journal documents the reported sequence. No independent pre-count receipt is supplied in this
> review dossier.
>
> The archived census table was checked against the recorded SHA-256. The tally used arm, TIC, the
> existing SPOC 2-minute and exposure flags, and the catalogue type. It counted distinct TICs and
> logged mixed labels separately. The count used no light curve, pixel file or battery output and
> carries the v0.5.10 limits label. The catalogue tally authorizes no target or product access.

Codex's round 2, integration item 2, as written: "The two analyses above were available to the
first draft. This revision also had the corrected all-307 planning calculation recorded in
`power-a1c.json`. The catalogue type count remained the sole new empirical result."

**No battery result on any KELT-FP target exists.**

**The records:**
- the script, [type_count.py](v0.5.13-amendment-1/type_count.py);
- its output, [type-count.json](v0.5.13-amendment-1/type-count.json);
- the log, [log.jsonl](v0.5.13-amendment-1/log.jsonl).

The table has 308 usable rows for 307 distinct TICs, and no TIC carries two types.

| KELT-FP type (catalogue label) | Usable TICs |
|---|---|
| SB1 (single-lined spectroscopic binary) | **172** |
| NEB (nearby eclipsing binary) | 49 |
| SB2 (double-lined spectroscopic binary) | 27 |
| EB1 | 17 |
| BEB (blended eclipsing binary) | 17 |
| EB2 | 8 |
| Giant | 6 |
| Variable | 6 |
| RV0 | 5 |
| **Total** | **307** |

Variable and RV0 are catalogue additions to the study's seven-type tally (v0.5.10 report, section
(c)). The benchmark is agreement with the frozen catalogue labels (Codex's round 1,
non-blocking).

## 2. The amendment (Codex's round 1, item 1, as written)

> The confirmatory FP population is the full route (d1) KELT-FP cohort under the charter's
> eligibility rules, provisionally 307 distinct TICs in the v0.5.10 census. Apply the pooled and
> band safety rules to assessed cases in that cohort. Apply the pooled and band FP coverage rules
> and the FP side of the symmetry lock to the full corresponding frozen denominators, counting both
> abstention buckets. The planet arm and all §5 thresholds apply as approved.
>
> Report the catalogue-defined non-SB1 subgroup as a prespecified descriptive analysis. It
> comprises NEB, BEB, EB1, EB2, SB2, Giant, Variable and RV0, provisionally 135 TICs. Report SB1
> separately, provisionally 172 TICs. For both groups and each catalogue type, report counts,
> survival among assessed cases, coverage among all frozen cases and both abstention buckets,
> pooled and by band, with Wilson bounds where estimable. Catalogue labels describe the reporting
> groups. Photometric decidability remains unmeasured. A subgroup result cannot satisfy the
> full-cohort gate.
>
> Freeze one case per eligible TIC and the catalogue-to-report mapping under the approved lock
> procedure. Use catalogue FP type only for reporting. Apply the same label-blind SNR procedure and
> frozen battery rules to all cases. Difficulty, missing signal, missing reference SNR, product or
> numerical failure and battery outcomes cannot remove or replace a frozen case or move it between
> reporting groups. Apply the charter's reason map, missing-SNR accounting and empty-cell rules.
>
> Before v0.6 authorization, apply the frozen sizing procedure to documented eligibility and band
> sizes. Record a shortfall as a feasibility finding. If an approved target is judged infeasible,
> submit a separate evidence-backed record for that target under the advance rule, with Codex
> review, independent review and maintainer approval. A subgroup result or an assumed survival rate
> cannot establish infeasibility or count as a PASS.

**This replaces** the charter's section 5 sentence "Report per-type FP results descriptively.". The
sentence that follows it in the charter stays in force as approved: "A difficult FP mix does not
change the pooled target, case eligibility or denominators."

**Unchanged** (Codex's choices, round 1):
- X = 0.25, Y = 0.80 and Z = 0.70;
- the band bounds 0.40, 0.65 and 0.60, and the fixed `<20` and `≥20` bands;
- the signed Newcombe margin D = 0.15. Symmetry uses all frozen planets and all frozen FPs,
  counting both abstention buckets.

## 3. Power (Codex's round 1, item 2, as written)

> The approved full-cohort planning scenario gives joint pass probability 0.945942. It assumes
> independent targets, planet bands of 85 and 86, FP bands of 153 and 154, assessment probability
> 0.85 in both arms, conditional planet retention 0.90 and conditional FP survival 0.15.
>
> For an exploratory sensitivity check, assume conditional survival 0.15 for the 135 non-SB1 cases
> and vary the assumed SB1 survival \(q\). Pass the common probability \((135 \times 0.15 + 172
> \times q)/307\), at full precision, to the unchanged frozen calculator functions for both FP
> bands. For \(q = 0.15, 0.30, 0.50, 0.70\), the approximate joint pass probabilities are 0.945942,
> 0.134514, \(3.49 \times 10^{-7}\) and \(1.18 \times 10^{-17}\). This is a homogeneous planning
> approximation with common assessment rates and hypothetical band sizes. Actual rates and band
> composition are unknown. These scenarios establish neither expected battery performance nor
> infeasibility.
>
> The earlier 124-case analysis and its 183-case mixture are retained as exploratory alternatives.
> The 135-case calculation gives 0.910930, 0.769290 and 0.307170 at assumed survival 0.10, 0.15 and
> 0.20 under a hypothetical gate using only those 135 FPs. Those figures describe a different
> decision rule. There is no separate subgroup PASS, and 0.945942 is a planning reference rather
> than a minimum power requirement.

**The records.** The corrected check is in a new dated artifact:
[power_a1c.py](v0.5.13-amendment-1/power_a1c.py) and
[power-a1c.json](v0.5.13-amendment-1/power-a1c.json). It reproduces 0.945942 and 0.134514; the last
two values round to 0.000000 at six decimals. The earlier runs are preserved unchanged:
[power_a1.py](v0.5.13-amendment-1/power_a1.py) / [power-a1.json](v0.5.13-amendment-1/power-a1.json)
and [power_a1b.py](v0.5.13-amendment-1/power_a1b.py) /
[power-a1b.json](v0.5.13-amendment-1/power-a1b.json). All of them import the frozen
[power_v2.py](v0.5.13-charter-prep/power_v2.py) unchanged.

Codex's round 2, integration item 1, as written:

> Under the stated homogeneous planning approximation, assumed SB1 survival of 0.30 gives a joint
> pass probability of 0.134514. Before v0.6 authorization, apply the frozen sizing procedure to
> documented eligibility and band sizes. Record any shortfall as a feasibility finding. If the
> evidence supports judging an approved target infeasible, submit a separate record for that target
> under the advance rule. The simulation-free planning scenarios alone establish neither actual gate
> performance nor infeasibility.

## 4. Sources and what is not confirmed

- **KELT-FP:** Collins et al. 2018, https://arxiv.org/abs/1803.01869. The catalogue CSV has
  SHA-256 `72b21cce…`, as recorded by v0.5.10, and its licence is not confirmed.
- **Not confirmed:**
  - the photometric decidability of any type;
  - which SB1 systems a photometric test could still reject;
  - the decidability of NEB targets on the target's own SPOC light curve.
