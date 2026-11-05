# S5: the draw of the C3 dossiers for independent review

The maintainer's decision of 2026-11-05 (#199): 4 independent reviews of C3 dossiers (2 planets
and 2 eclipsing-binary false positives) and 1 gate review; each a fresh Claude Opus session,
read only, receiving only its dossier (the gate session, the phase's dossier). Caps: 250,000
tokens per dossier session, 400,000 for the gate session (worst case 1.4 M of the 1.5 M reviewer
cap). A session that reaches its cap ends, and its report is recorded as it came out, with no
extension. A second gate review needs a new approval. The reviewer protocol is
`docs/reviewer-protocol.md` (TESS dossiers, v0.2): its prompt, rules and storage.

This rule is committed alone, as the tip of `main`, before its round is published. The script is
[`draw.py`](draw.py); its output, `draw.json`, is a later commit.

## Strata (fixed by the committed C3 run, before the round)

In each class, the final 8 controls of the C3 assignment (`calibration/v0.5/runs/c3/report.json`)
split by their v0.5 verdict **without the catalog test** (the variant the targets T3a and T3b
read; `runs/c3/records.jsonl`, field `without_catalog.v05.verdict`):

| Stratum | Controls |
|---|---|
| `planet-inconclusive` | TIC-144193715, TIC-151724385, TIC-237099296, TIC-280206394 |
| `planet-other` | TIC-17746821, TIC-257567854, TIC-310002617, TIC-399860444 |
| `eb-fp-inconclusive` | TIC-101395259, TIC-233681149, TIC-308050066 |
| `eb-fp-other` | TIC-199688472, TIC-286355915, TIC-300871545, TIC-382188882, TIC-9727392 |

One dossier is drawn from each stratum: 4 in all. The final assignment includes TIC-310002617,
first a planet reserve, which replaced TIC-62483237 (signal identity not matched); the unused
reserves, the replaced control and the error record (TIC-184679932) are outside the strata.

**What the draw is and is not.** A stratified random sample: it guarantees that both verdict
groups of each class are reviewed. It is not a simple random sample of a class: each planet has
an inclusion probability of 1/4; each eclipsing binary 1/3 (INCONCLUSIVE) or 1/5 (other). Four
qualitative reviews do not estimate classification accuracy or the prevalence of objections; any
class-level aggregate would need weights by stratum size.

## Randomness and the draw

- **Round:** the first drand round (mainnet, default chain, `refute.drand`) published at least
  1 hour after the `created_at` of the CI push run of this rule's commit: workflow `ci.yml`,
  event `push`, `head_sha` equal to the commit, `run_attempt` 1
  (`discover.pilot.push_run_created_at`, `refute.drand.round_after`). No such run, or more than
  one, stops the draw for the maintainer. The BLS signature is verified
  (`refute.drand.drand_seed`); drand unavailable or a signature that fails stops the draw.
- **Seed per stratum:** `int(sha256(randomness_hex + "|v0.5|s5|<stratum>").hexdigest(), 16)`,
  with `<stratum>` one of the four names above, literally; the string is encoded as UTF-8 with
  no newline; `randomness_hex` is the beacon's 64 lowercase hexadecimal characters, used as text
  (not decoded); the whole SHA-256 digest is read as one integer (as R_c3's seeds).
- **Order:** the stratum's controls sorted by TIC ID (as an integer), then shuffled with that
  seed (`refute.drand.shuffled`); the first is drawn.
- **Dossiers:** the drawn controls' dossiers of the C3 dossier run
  (`.cache/v05/c3/dossiers/c3-dossiers/<TIC>`; archived to the Drive with the manifest
  `calibration/v0.5/runs/c3-dossiers/drive-manifest.sha256`), checked against that manifest
  before each review.

## Authentication and attempts

- **The rule commit** adds this file and `draw.py`; it is pushed alone, as the tip of `main`; no
  later commit replaces it and no other round is used once the randomness is known. `draw.py`
  refuses a rule commit that is not the one commit that added this file, that is not on
  `origin/main`, or whose bytes of this file, `draw.py`, `runs/c3/report.json` and
  `runs/c3/records.jsonl` differ from the working tree; and it refuses executed code that is not
  the frozen code: `refute.drand`, `discover.pilot` and `calib05.steps` must be imported from
  this tree's `src/`, and the tree's code hash must be the one frozen in `inputs.json` with every
  bound path intact (`calib05.steps.frozen_code`); all before any network access.
- **The interpreter** is fixed: CPython 3.13.16, the project's environment (`random.shuffle` is
  not guaranteed across Python versions; `refute.drand.interpreter_record`). Any other
  interpreter is refused.
- **Attempts:** each attempt is written to `draw-attempts/attempt-NN.json` (never over a file);
  the first is also `draw.json`. A later attempt (for example after a network failure) must
  reproduce the same round and draw, or the draw stops for the maintainer; every attempt is kept
  and committed. Any redraw needs the maintainer's approval recorded in an issue first, and its
  result supplements the original, which is kept.

## Criterion 6 (fixed here, before the round)

The clean-clone reproduction of exit criterion 6 uses the dossier drawn for the first stratum in
sorted order, `eb-fp-inconclusive`, so that the reproduced dossier is chosen by the draw, not by
the agent.
