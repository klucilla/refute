# Step 0's recount (v0.5.11)

Exploratory, `method_status: not_validated`. Read-only, by [RULES.md](RULES.md). Part B carries 'WEAKENED; does not meet D1, D2, D4, T2a'. Never a verdict, a candidate or an acceptance.

| Population | Records | Hosts | retained | rejected | unassessed | unknown |
|---|---|---|---|---|---|---|
| P1 part B, all | 295 | 295 | 136 | 88 | 71 | 0 |
| P1, arm fp | 147 | 147 | 48 | 56 | 43 | 0 |
| P1, arm planet | 148 | 148 | 88 | 32 | 28 | 0 |
| P1, matched True | 187 | 187 | 126 | 24 | 37 | 0 |
| P1, matched False | 108 | 108 | 10 | 64 | 34 | 0 |
| P2 C2 T2a, all | 637 | 87 | 0 | 0 | 34 | 603 |

Per test (assessed_pass / assessed_fail / not_assessed / unknown):

| Population | odd_even | secondary_eclipse | plausibility |
|---|---|---|---|
| P1 part B, all | 179 / 19 / 97 / 0 | 221 / 27 / 47 / 0 | 216 / 44 / 35 / 0 |
| P2 C2 T2a, all | 0 / 0 / 34 / 603 | 0 / 0 / 0 / 637 | 0 / 0 / 0 / 637 |

P1 records with no battery output (status not OK): {'planet': 2, 'fp': 3}.

The screen's own tests (F1, F2, F3, F4, U1) were never run on any record: their assessability is unknown for every record.
