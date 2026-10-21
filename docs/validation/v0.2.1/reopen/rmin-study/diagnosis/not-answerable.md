# Q7. What the records do not answer

Declared in [DECLARATION.md](DECLARATION.md), Q7. Each item with what would be needed.

| Question | Why the records cannot answer it | What would be needed |
|---|---|---|
| The interruptions by injected depth, duration, period, impact or ingress (term 2's geometry) | the injected parameters are drawn inside `population_v2.build_case`, which builds the light curve; they are not in the records | the case's recorded final parameters, from rebuilding each case (a light curve) or from a lot whose records carry them |
| Whether the recovered candidate is the injected transit (term 4) | the records keep no recovered period, epoch or duration (except the rounded `T14` of timing-stopped rounds) and no injected one; the twin tests the depth at the predicted windows, not identity | the train candidate's period, epoch and duration and the injected ones, per round, in the record |
| The split of `e_pred` into the replica variance, `m_β` and the number of predicted transits (term 3) | `var_rep(dP)` and `N_pred` are computed but not recorded (only `S_pred`, `d_train`, `e_train` and the replica counts are) | `train_var_rep`, `hidden_var_rep` and `n_predicted_transits` in the record |
| The train SNR of rounds stopped before the capacity rule (`train_snr_below_gate`, timing, noise) | `d_train` and `e_train` are recorded only from the capacity stage on | the train measurement's depth and error in every round's record |
| `σ_T` and `T14` beyond two decimals, and `σ_T` of rounds not stopped by the timing rule | they appear only in the timing reason's text, rounded | `σ_T` per hidden epoch and the train duration as numbers in the record |
| Which round gave a target's PASS, and the hidden-year SNR of the rounds that PASS while the last round is undecided | derivable round by round, but not declared as an output of this diagnosis (see exploratory.md) | a separate declaration |
| Anything about real TESS light curves | the lot is synthetic and idealized (ROADMAP, v0.2.1 scope) | not applicable to this lot |
