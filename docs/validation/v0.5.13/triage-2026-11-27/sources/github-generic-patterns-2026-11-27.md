# Source: GitHub's availability of secret scanning for non-provider (generic) patterns

Read on 2026-11-27 for the maintainer's decision W1(f) on #56 (#218, comment 7229841832).

- **URL given by the maintainer:**
  https://docs.github.com/en/enterprise-cloud@latest/code-security/secret-scanning/using-advanced-secret-scanning-and-push-protection-features/non-provider-patterns
- **Where it redirected on 2026-11-27:**
  https://docs.github.com/en/enterprise-cloud@latest/code-security/how-tos/secure-your-secrets/detect-secret-leaks/enabling-secret-scanning-for-generic-patterns
- **Page title:** "Enabling secret scanning for generic patterns". The former "non-provider patterns" are now called "generic patterns".

**Literal excerpt** ("Who can use this feature?"):

> Scanning for generic patterns is available for the following repository types:
>
> - Organization-owned repositories on GitHub Team or GitHub Enterprise Cloud with GitHub Secret Protection enabled

**What it supports here:** klucilla/refute is a repository of a personal account, not of an organization, so the feature is not available to it. That is the maintainer's adviser's check through the API on 2026-11-27, as stated in decision W1(f). This file does not re-run that check.
