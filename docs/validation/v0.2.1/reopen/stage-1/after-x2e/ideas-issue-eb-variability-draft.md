# Draft: ideas issue on eclipsing binaries and variability (not opened)

The maintainer's decision after X2e, item 9: prepare the text of an ideas issue on eclipsing
binaries and stellar variability as astronomical results of their own (their own analysis and
catalogs). **Not opened, and no implementation front.** It would be opened only on the maintainer's
decision; its place in the ROADMAP is v0.5 ("Variable stars pack: EB and pulsators, catalog
cross-match, exporter"), after v0.2.1's gate.

---

> **Title:** Ideas: eclipsing binaries and stellar variability as results of their own (v0.5,
> not started)
>
> **Label:** ideas (no milestone; no implementation until v0.5 is the current phase)
>
> **Context.** In the transit pack, eclipsing binaries and stellar variability are what the gauntlet
> must recognize and set aside: an eclipsing binary is a false positive to flag, variability a
> nuisance that the detrending and the holdout must survive. Stage 1 of v0.2.1 showed how much of the
> engine's behaviour depends on them (the attenuation of the measured depth with variability; the
> wrong candidates without it). The same light curves carry information that is a result in itself.
>
> **Ideas (none is a plan):**
> - an analysis of its own for eclipsing binaries: what the gauntlet already measures (odd/even
>   depths, a secondary eclipse, the eclipse shape) reported as an eclipsing-binary candidate with
>   its own claim and verdicts, instead of only as a reason to refute a transit;
> - variability as a measured quantity: the fundamentals the train detrending detects, reported per
>   target with their uncertainty, and checked against a held-out year like any other claim;
> - cross-matching against published catalogs of eclipsing binaries and variable stars, each catalog
>   named with its source and the date it was read when the work starts (none is chosen here);
> - an exporter in the format of the official channel for such catalogs, with a human always
>   submitting.
>
> **Rules that would apply:** the claims are candidates and verdicts, never confirmed discoveries;
> every identifier, period and classification comes from an authoritative source with its date;
> nothing is submitted automatically; the domain pack has its own gauntlet, holdout strategy and
> coverage rules (zero coverage is INCONCLUSIVE).
>
> **Not now:** this issue starts no code, no data download and no lot. It is a place to collect
> ideas until v0.5 is planned.
