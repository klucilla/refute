## OVERALL: REFUTED for approval as written

The SHA-256 matches. Items 3, 4 and 6 are applied. Item 5 still lacks a valid phase-wide disk bound. No charter measurement ran.

- **Item 3 — Applied.** The standalone probe runs against the approval code outside pytest collection. Expected failures are documented before the probe, and the suite is committed and pushed before any `src/` change. [Charter:298](/C:/Projetos/refute/docs/plans/v0.5.12-charter.md:298)
- **Item 4 — Applied.** M1, M2 and the sensitivity control each freeze and check realized-input hashes before calling F1. Prior recipes are used to regenerate inputs only. A match or unresolved identity stops the batch. [Charter:437](/C:/Projetos/refute/docs/plans/v0.5.12-charter.md:437)
- **Item 5 — Not applied in full.** The new bootstrap unit and Claude traffic allowance address round 2. The disk rule still equates per-job write transfers with peak disk occupancy. Even if the counter captured every write, two successive units retaining 1.2 GB each would occupy 2.4 GB while each reports only 1.2 GB. The outer launcher also still samples disk during bootstrap. The optional Drive clause conflicts with the traffic allowlist. [Charter:124](/C:/Projetos/refute/docs/plans/v0.5.12-charter.md:124) · [Charter:135](/C:/Projetos/refute/docs/plans/v0.5.12-charter.md:135) · [Old launcher:271](/C:/Projetos/refute/docs/validation/v0.5.11/tools/launch_v4.py:271) · [Charter:591](/C:/Projetos/refute/docs/plans/v0.5.12-charter.md:591)

  **Exact fix:** “From bootstrap through closure, enforce one phase-wide 2 GB bound over all phase-attributable disk occupancy, including retained outputs, Git, launcher writes, warm-environment growth and transient allocations. Use enforced quotas or a proven conservative bound that carries retained bytes forward between units. Treat job write-transfer counts as telemetry unless proved sufficient for that bound. Before M1, demonstrate both create-and-delete and retained-output accounting across units. Keep required outputs in git, split below 5 MB as needed. Drive transfers are outside this charter.”

- **Item 6 — Applied by the recorded alternative.** The charter and ROADMAP list six exit criteria. The unchanged protocol can judge all six at the seal, and the gate result and reconciled tail are checked at closure. [Charter:544](/C:/Projetos/refute/docs/plans/v0.5.12-charter.md:544) · [Charter:579](/C:/Projetos/refute/docs/plans/v0.5.12-charter.md:579) · [ROADMAP:1516](/C:/Projetos/refute/ROADMAP.md:1516) · [Gate protocol:39](/C:/Projetos/refute/.claude/commands/gate-review.md:39)

**Recorded items:** None outside this round’s scope.

