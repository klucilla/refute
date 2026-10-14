# Right of reply (v0.3)

How the authors of a paper are told about the verdicts on its claims before any
negative result is published. This document follows
[docs/plans/v0.3-plan.md](plans/v0.3-plan.md), section 9.

**Status.** This is the planned procedure. The commands named here (`refute
reply-draft`) are built in the v0.3 work packages; until then nothing here is
automated.

Verdicts are about claims, never about the people who made them. An agent never sends
email, and nothing is submitted to any venue (arXiv, OpenReview, MLRC or any other):
the maintainer sends every message from their own account.

## Seal, annexes and embargo

1. **Seal.** When a locked run finishes, the **experimental core** of each dossier is
   sealed: the locked claims, the outputs, the logs, `verdict.json` and its manifest.
   The SHA-256 of a deterministic archive of all cores (and one per paper) is
   committed and pushed at once, with no content. The core never changes after the
   seal.
2. **Annexes.** Reviewer reports, the `reply/` records and the authors' reply are
   annexes, each with its own manifest that cites the hash of the sealed core. The
   published dossier lets anyone verify the original core and each annex.
3. **Embargo.** Until a paper's results may be published, every public commit or
   issue about it contains only hashes or neutral metadata.

## Notice to the authors

4. **Draft.** `refute reply-draft <dossier>` writes an email draft in English to the
   corresponding author address printed in the paper. No other source of personal
   data is searched. The draft contains:
   - the claim and its location;
   - the paper version and the commit tested;
   - the verdict and its meaning;
   - exact reproduction commands, and the dossier;
   - an invitation to reply within the period;
   - an offer to publish the reply next to the verdict.

   The wording is neutral, about the claim, never about the people.
5. **Send.** The maintainer reviews the draft and sends it from their own account.
   The `reply/` annex records the send date, the SHA-256 of the sealed core, the reply
   deadline and the SHA-256 of the draft.
6. **Waiting period.** 30 days from sending, extendable by up to 14 days by a rule
   defined beforehand, on a justified request. The notice, the deadline and any
   delivery failure are recorded. No reply does not mean agreement.
7. **Reply handling.**
   - The locked verdict never changes.
   - If the authors show an error in Refute's procedure, a new claim is written,
     approved, locked and run; both results are published together.
   - Rerun approvals go into a neutral public issue that holds only the claim id and
     the SHA-256 of a sealed file with the reason and the exact procedure; the file is
     published with the result.
   - The authors' reply is published only with their permission.

**States recorded for every notice:** "notice sent", "period ended" and "reply
received" are distinct states, each with its date.

## Papers with no negative claim

- **All claims `REPRODUCED`:** the authors receive a courtesy notice after the seal.
  It may open an optional reply period, recorded with the same states. It does not
  delay publication.
- **Only `INCONCLUSIVE` claims, or `INCONCLUSIVE` and `REPRODUCED`, with no negative
  claim:** publication without a mandatory wait, with the same courtesy notice. The
  paper is described as inconclusive for those claims, never as positive or
  reproduced, and stays in the denominators.
- The absence of a wait never waives the gate (next section).

Negative claim verdicts are `FRAGILE`, `NOT_REPRODUCED` and `NOT_REPRODUCIBLE`.

## Order: notification, gate, publication

1. **Notification:** the notices are sent and recorded.
2. **Gate:** the gate review of the phase. The exit criterion on the right of reply is
   met when at least one notification was sent and recorded, with the send date, the
   SHA-256 of the sealed core and the reply deadline: "the notification was made and
   recorded; the reply period remains open". A courtesy notice that opened an
   optional reply period is such a notification.
3. **Publication:**
   - a paper with a negative claim is published only after the gate is passed and its
     reply period, including any extension, has ended;
   - a paper with no negative claim may be published without waiting for its period,
     but not before the gate;
   - publication contains the dossier, the verdicts, the authors' reply (if allowed)
     or "authors contacted on <date>, no reply received".

Later replies never change a locked verdict.
