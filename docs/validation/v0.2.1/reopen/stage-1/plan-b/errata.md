# Plan B: errata (text clarifications; the plan is not reopened)

## E1 (2026-10-23): the example "a sector across a year boundary"

**The text.** Plan B section 1.2 (and the population study's Amendment B), "The represented
geometries": "A draw that would fall outside D1 to D5 (for example a sector across a year
boundary) is redrawn by the generator's own rule".

**The clarification.** The example is imprecise. By Amendment B's normative definitions a sector
is labelled by the year of its first kept cadence, so a sector across a year boundary keeps that
one label and is **inside** the domain whenever the three sectors' labels are distinct. What a
year boundary can cause is two sectors with one label (a separation shorter than the rest of the
calendar year), which D1 rejects. The generator's only rejection is D1 to D5; the example adds no
condition. Read as: "(for example two sectors in one calendar year)".

**Ratified by the maintainer on 2026-10-23** ("Ratifico a sua leitura: um setor que atravessa a
virada do ano recebe o ano da primeira cadência e só sai do domínio se dois setores ficarem com o
mesmo ano"), after gate 1's acceptance (`7ee2b11`). The acceptance record
([../../../population/population-v4-acceptance.md](../../../population/population-v4-acceptance.md),
section 6, item 1) applied this reading.

**The code read for it (2026-10-23, reading only, nothing run).** Both label the year **by sector,
never by cadence**:

- the adapter: `load_from_manifest` sets one `year = btjd_to_year(float(t.min()))` per sector and
  gives it to every cadence of that sector (`src/refute/packs/tess/adapter.py`, lines 577 and 583);
  the engine counts the distinct labels (`LightCurveData.years`, `types.py`, line 137);
- `population_v4`: the label of each sector is the domain function's, `btjd_to_year` of the
  sector's first kept time stamp (`domain.py`, `sector_timing`), and it is given to every cadence
  of that sector (`population_v4.py`, lines 326, 329 and 369); `population_v4_check.built_report`
  checks on every built case that `lc/year` equals that label.

**One difference of input, for gate 2.** The adapter takes `t.min()` **after** it drops the
cadences whose time, flux or flux error is not finite (`adapter.py`, lines 573 and 574); the
domain function takes the first kept time stamp **before** any filter that reads a flux
(Amendment B's input). In `population_v4` the two are the same cadence (no generated flux is
non-finite and the time stamps are in order), so the generator and the adapter agree. On a real
product they could differ only if the cadences dropped for a non-finite flux at a sector's start
run across a new year; the profile O2 (gate 2) must therefore label a sector for the domain and
for the engine from the same cadence, or refuse the case when the two labels differ. This is an
input to gate 2's acceptance, not a change of D1 to D5.
