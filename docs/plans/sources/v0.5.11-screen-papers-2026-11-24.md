# Sources of the v0.5.11 screen tests (read on 2026-11-24)

This is the charter of v0.5.11, step 0, item 1. For every test it records the paper version, the
equation, the inequality and the applicability, read from the paper itself, with a short literal
excerpt.

**How the papers were read.**
- The PDFs were fetched by the metered unit `fetch-papers` (2026-11-24 23:01Z). Their SHA-256 are
  in [../../validation/v0.5.11/papers/fetch-record.json](../../validation/v0.5.11/papers/fetch-record.json).
  They are kept outside git.
- The text was read from the arXiv HTML renderings of the same versions (the official arXiv HTML
  for K25; ar5iv for T18 and SM03), fetched in full (not summarized) on 2026-11-24.
  - A PDF reader would need a program the project does not have (poppler), which is third-party
    code behind the maintainer's stop.
  - **Not confirmed:** that each HTML rendering matches its PDF character for character.
  - **Unresolved for T18 and SM03:** the upstream arXiv revision each rendering shows, and its
    equivalence to the PDF.
- The excerpts below are literal, with the equations in the rendering's LaTeX.

**Versions and hashes of the artifacts read** (Codex's blocking item 2 of step 0's first round):

| Paper | Version | PDF SHA-256 (fetch-record.json) | Markdown of the HTML read, SHA-256 (kept under `.cache/v0511/papers/`) |
|---|---|---|---|
| K25 | arXiv 2509.10619**v1** (stated in both URLs) | `a7f848f9a01b5e70b8b97b145de1ac7819834b7108971fd13d457c75c4437d8c` | `0cf5c217b3a7fd86c3061224e262de2afc9434717321a70eeb63f116562f1e22` |
| T18 | arXiv 1710.06758, **version not stated**: the URLs carry none, and the version ar5iv rendered is not recorded on the page | `876d603eb9342bddd5b34be64b7d6ac91355b340e1874dcaa63e2a6a795f78fd` | `2568491c5816528db1d8fd38408a185c768641ba928e5e2b0571687017e625d4` |
| SM03 | arXiv astro-ph/0206228, **version not stated**, as for T18 | `280f302f757b07d077344c8ec29e2a1ef5e523ec688e7e0f662436f4c40be891` | `4b77f0826f4e8fbcdc41d9be3c42959df366d6b9d9ecc5bd8c8fcb5879d83307` |

**Unresolved:**
- the upstream revision of T18 and of SM03 that each rendering shows;
- that each HTML rendering matches its PDF.

The hashes were taken by the metered `inspect` unit.

**Use in the specification after step 0's first round:**
- Only F1's OE_box decides, so K25 Eq. 11 and its threshold are the only ones with an effect.
- Every other equation below feeds report-only quantities, with its paper threshold shown for
  reference.

## K25: Kunimoto et al., "LEO-Vetter", arXiv:2509.10619v1

URL: https://arxiv.org/html/2509.10619v1 (PDF: https://arxiv.org/pdf/2509.10619v1). Read
2026-11-24.

| Item | Section, equation | Literal excerpt | Use here |
|---|---|---|---|
| Box SNR | II.1, Eq. (1) | `\mathrm{SNR}=\frac{\delta}{\sigma_{tr}}` | the MES of a phase cell |
| Box depth | II.1 | "weighted mean of all in-transit data points (entirely within half a transit duration from the transit center" | the depth estimator |
| Pink noise | II.1, Eq. (2) | `\sigma_{tr}=\sqrt{\frac{\sigma_{w}^{2}}{n}+\frac{\sigma_{r}^{2}}{N_{tr}}}` | the noise of an event set |
| Red noise | II.1, Eq. (3) | `\sigma_{r}^{2}=\sigma_{\mathrm{bin}}^{2}-\sigma_{\mathrm{bin,xpt}}^{2}`; "we set σr=0" when negative | the red noise |
| White noise | II.1 | "after masking out data within one transit duration" | σ_w |
| Trapezoid | II.2 | the ingress fraction fixed "to fixed values of 0.1, 0.15, 0.2, 0.25, 0.3, 0.35, and 0.4", then "allowed to vary between 0 and 0.5" | the trapezoid fit |
| Model-shift events | III.9 | the secondary "at least two transit durations from the primary"; the positive event "at least three transit durations" | event selection |
| MS1 to MS3 | III.9, Eq. (7) | `\mathrm{MS}_{1}\equiv\mathrm{MES}_{\mathrm{pri}}/F_{\mathrm{red}}-\mathrm{FA}_{1}`; `\mathrm{MS}_{2}\equiv(\mathrm{MES}_{\mathrm{pri}}-\mathrm{MES}_{\mathrm{ter}})-\mathrm{FA}_{2}`; `\mathrm{MS}_{3}\equiv(\mathrm{MES}_{\mathrm{pri}}-\mathrm{MES}_{\mathrm{pos}})-\mathrm{FA}_{2}` | U1 (report-only) |
| U1 thresholds | III.9 | "We fail TCEs with MS1<0.2 ... MS2<0.8 ... or MS3<0.8" | recorded, not used (report-only) |
| Size | IV.1 | "fail TCEs with Rp>22 R⊕", Rp from "the transit model-fitted Rp/R⋆" | F3 (report-only: our estimator is not the transit-model fit) |
| V shape | IV.2 | "a more lenient threshold of V<1.5" for `V=R_{p}/R_{\star}+b` | F4 (report-only) |
| MS4 to MS6 | IV.3, Eq. (9) | `\mathrm{MS}_{4}\equiv\mathrm{MES}_{\mathrm{sec}}/F_{\mathrm{red}}-\mathrm{FA}_{1}`, `\mathrm{MS}_{5}\equiv(\mathrm{MES}_{\mathrm{sec}}-\mathrm{MES}_{\mathrm{ter}})-\mathrm{FA}_{2}`, `\mathrm{MS}_{6}\equiv(\mathrm{MES}_{\mathrm{sec}}-\mathrm{MES}_{\mathrm{pos}})-\mathrm{FA}_{2}` | F2 |
| Secondary threshold | IV.3 | "significant if MS4>0, MS5>−1, and MS6>−1" | F2 |
| F_red clause | IV.3 | "We therefore ignore this first condition if Fred>1.8" | F2 (**confirmed in the text**) |
| Occultation exception | IV.3 | "less than 10% of the primary transit depth, the impact parameter ... less than 0.95, the derived planet radius is less than 22 R⊕, and the planetary albedo ... less than 1" | F2's exception |
| Albedo | IV.3, Eq. (10) | `A=\delta_{\mathrm{sec}}\bigg(\frac{a}{R_{p}}\bigg)^{2}` | recorded, not evaluable here |
| Odd-even box | IV.4, Eq. (11) | `\mathrm{OE}_{\mathrm{box}}=\frac{|\delta_{\mathrm{odd}}-\delta_{\mathrm{even}}|}{\sqrt{\sigma_{\delta_{\mathrm{odd}}}^{2}+\sigma_{\delta_{\mathrm{even}}}^{2}}}`; "We fail TCEs with OEbox>3" | F1 |
| Odd-even trapezoid | IV.4, Eqs. (12), (13) | `\mathrm{OE}_{\mathrm{trap}}\equiv\frac{|\delta_{\mathrm{trap,odd}}-\delta_{\mathrm{trap,even}}|}{\sqrt{\sigma_{\delta_{\mathrm{trap,odd}}}^{2}+\sigma_{\delta_{\mathrm{trap,even}}}^{2}}}`; `\mathrm{OE}_{\mathrm{trap},T}\equiv\frac{|T_{\mathrm{odd}}-T_{\mathrm{even}}|}{\sqrt{\sigma_{T_{\mathrm{odd}}}^{2}+\sigma_{T_{\mathrm{even}}}^{2}}}`; "only δ and T are allowed to vary"; "fail TCEs with either OEtrap>3"; "OEtrap,T>10" | F1_trap (report-only) |

**Not stated in K25's text:**
- the value of N_TCE in FA1;
- how F_red is computed in its box adaptation;
- the phase grid of the MES series.

K25 refers to Coughlin's Model-Shift for these. The specification fixes them as its own choices,
marked as such.

## T18: Thompson et al. 2018, "Planetary Candidates Observed by Kepler. VIII", arXiv:1710.06758

URL: https://ar5iv.labs.arxiv.org/html/1710.06758 (PDF: https://arxiv.org/pdf/1710.06758). Read
2026-11-24.

| Item | Section, equation | Literal excerpt | Use here |
|---|---|---|---|
| FA1 | A.3.4, Eq. (A4) | `FA_{1}=\sqrt{2}\cdot\textrm{erfcinv}\left(\frac{T_{\rm dur}}{P\cdot N_{\rm TCEs}}\right)` | F2, U1 |
| FA2 | A.3.4, Eq. (A5) | `FA_{2}=\sqrt{2}\cdot\textrm{erfcinv}\left(\frac{T_{\rm dur}}{P}\right)` | F2, U1 |
| F_red | A.3.4 | "examining the standard deviation of the best-fit depths at phases outside of the primary and secondary events" | F_red's definition |
| MS1 to MS3 (T18's sign convention) | A.3.4, Eqs. (A6) to (A8) | `MS_{1}=FA_{1}-\sigma_{\rm Pri}/F_{\rm Red}`; `MS_{2}=FA_{2}-(\sigma_{\rm Pri}-\sigma_{\rm Ter})`; `MS_{3}=FA_{2}-(\sigma_{\rm Pri}-\sigma_{\rm Pos})` | **not used:** T18 defines MS1 to MS3 with the opposite sign to K25's Eq. (7); the specification follows K25 |
| MS4 to MS6 | A.4.1.2, Eqs. (A13) to (A15) | `MS_{4}=\sigma_{\rm Sec}/F_{\rm Red}-FA_{1}`; `MS_{5}=(\sigma_{\rm Sec}-\sigma_{\rm Ter})-FA_{2}`; `MS_{6}=(\sigma_{\rm Sec}-\sigma_{\rm Pos})-FA_{2}` | the same forms as K25 Eq. (9) |
| T18's own thresholds | A.4.1.2 | "If MS4>1, MS5>0, and MS6>0" | **not used:** the screen uses K25's |

## SM03: Seager and Mallén-Ornelas 2003, arXiv:astro-ph/0206228

URL: https://ar5iv.labs.arxiv.org/html/astro-ph/0206228 (PDF:
https://arxiv.org/pdf/astro-ph/0206228). Read 2026-11-24.

| Item | Section, equation | Literal excerpt | Use here |
|---|---|---|---|
| Radius ratio | 3.2.1, Eq. (6) | `\frac{R_{p}}{R_{*}}=\sqrt{\Delta F}` | F3, F4 (report-only) |
| Impact parameter | 3.2.1, Eq. (7) | `b\equiv\frac{a}{R_{*}}\cos i=\left[\frac{(1-\sqrt{\Delta F})^{2}-\frac{\sin^{2}\frac{t_{F}\pi}{P}}{\sin^{2}\frac{t_{T}\pi}{P}}(1+\sqrt{\Delta F})^{2}}{1-\frac{\sin^{2}\frac{t_{F}\pi}{P}}{\sin^{2}\frac{t_{T}\pi}{P}}}\right]^{1/2}` | F4 (report-only) |
| Assumptions | 2 | circular orbit, no limb darkening (section 2, "Assumptions") | why F3 and F4 stay report-only |

## Licences of code

- No implementation of these tests was read.
- LEO-Vetter's code is GPL-3.0 or later
  ([../../sources/engines-licences-2026-11-24.md](../../sources/engines-licences-2026-11-24.md)), and it
  was not opened.
- Coughlin's Model-Shift code (https://github.com/JeffLCoughlin/Model-Shift, named by T18) was not
  opened either.
