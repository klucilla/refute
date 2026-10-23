# Dependencies: which vulnerable paths are reachable (reading; nothing changed)

The maintainer's decision after X2e, item 6: security apart from the scientific comparison; verify,
by reading the code and the configurations in use, which vulnerable paths are reachable; propose an
early correction if the exposure is relevant, and a way to keep a frozen scientific environment for
comparison without keeping the working environment exposed. **Nothing in the environment, the locks
or the alerts changes before the maintainer's approval.** The alerts are those listed in
[../dependabot-2026-10-22.md](../dependabot-2026-10-22.md) (42 open, all in `uv.lock`); the
advisories were read on 2026-10-22 from the GitHub advisory database
(`https://github.com/advisories/<GHSA id>`); the release dates from PyPI on the same day.

How each reading was made: the source tree (`src/`, `scripts/`, `tests/`, `docs/`) searched for the
packages' entry points (no match for `PIL`, `imread`, TIFF, Ghostscript, `s3fs`, `aiohttp` or
`s3://` in any `.py`, `.ps1`, `.sh`, `.yml`, `.yaml` or `.toml` file); the installed packages read
where they call each other; and a local check without network
(`.cache/merge-v021/tools/tls_paths.py`, the project's virtual environment) of the certificate
stores the clients use.

## certifi 2026.7.22 (alert 4, critical: emSign roots whose intermediate keys were compromised)

- **Reachable.** `requests` 2.34.2 uses certifi's bundle: in this environment
  `requests.certs.where()` and `requests.utils.DEFAULT_CA_BUNDLE_PATH` are certifi's `cacert.pem`,
  and that bundle contains emSign entries. `requests` carries every MAST download
  (`adapter.download_checked` → lightkurve's `product.download`) and the TIC queries (astroquery
  `Catalogs`, `astroquery/query.py` with `verify=True`, the bundle by default), and pyvo.
- **Not through certifi:** the project's own `urllib` clients (`drand.py`, `ebcatalog.py`,
  `ml/fetch.py`) use the standard library's default context; on this machine it loads the Windows
  store (no `cafile`; 104 certificates), on Linux the system's OpenSSL paths. Whether those system
  stores trust the emSign roots was not checked. (Revision 2: `selection/walk.py`, listed here
  before, only handles `urllib` errors; its fetches go through functions passed in. **Also through
  certifi:** astropy's `download_file`, section "Revision 2" below.)
- **The exposure is relevant, whatever the package's purpose:** a party holding the compromised keys
  and on the network path could serve altered MAST or TIC data over a TLS connection that `requests`
  accepts. The adapter records each file's SHA-256 **at its first fetch** and verifies offline
  afterwards, so altered data fetched once would become the recorded reference and pass every later
  check. The CI does not download (the tests are offline), so it is not exposed this way.
- **Today's use:** stage 1's lots are synthetic and download nothing; downloads happen only in work
  on real targets (the v0.3 papers and calibrations, and future v0.2.1 steps on real data).
- **Fixed in** 2026.10.19, eligible under the 7-day rule from **2026-10-27 02:25 UTC**.

## Pillow 12.3.0 (alerts 10 to 18, 21 to 39; critical: 38 TIFF write to `BytesIO`, 21 Ghostscript argument injection, 10 JPEG decoding)

- **Reachable only as a PNG encoder of the project's own figures.** `plots.py` saves every figure
  with `Figure.savefig` to a `.png` path (lines 28 to 31); matplotlib 3.11.2 writes PNG through
  Pillow (its `print_png` goes through `image.imsave`, which uses `PIL`: checked in the installed
  source). The encoder receives an RGBA buffer rendered by Agg from the data, not a file structured
  by anyone else.
- **Not reachable:** the TIFF encoder of alert 38 (no TIFF is written anywhere, no `BytesIO` save);
  the EPS/Ghostscript path of alert 21 (no EPS opened or saved); every decoder (JPEG, TIFF, PDF, GIF,
  APNG, MSP, XBM, FreeType fonts): the project opens no image file, and the ML readers use numpy,
  parquet and pandas. A third-party package could open an image in a path the project does not use
  (bokeh comes with lightkurve); none is called.
- **The scientific comparison:** a new Pillow can change the PNG bytes of a figure without changing
  any number; a dossier that cites its plots' SHA-256 would then differ on a rerun. This is a
  reproducibility question, not a security one, and is why the frozen environment below matters.
- **Fixed in** 13.0.0 (a major version), eligible from **2026-10-23 22:15 UTC**.

## aiohttp 3.14.3 (alerts 1 to 3, 5 to 9)

- **Installed, not reached.** It comes with `s3fs` 2026.9.0 (and `aiobotocore`), a dependency of
  lightkurve 2.6.0 in `uv.lock`. No module of the project imports `s3fs` or `aiohttp`. The installed
  lightkurve has conditional `fsspec` branches for `s3://` inputs (`io/read.py` and `io/generic.py`;
  Codex's review corrected an earlier reading that it had none); the project passes no `s3://` URL,
  so the inspected paths never select them; and it runs no HTTP server. The server-side advisories (multipart, timeouts,
  request smuggling, `Request.scheme`) need a server; the client-side ones (cookie scope, the
  connector pool via `Max-Age`) need the aiohttp client, which only a cloud read through `s3fs`
  would use.
- **It would become reachable** if a cloud data path were enabled (none is planned).
- **Fixed in** 3.14.4, **eligible now**.

## virtualenv 21.14.2 (alerts 19, 20, 40 to 42)

- **Only through pre-commit 4.6.2**, which builds the hooks' environments
  ([.pre-commit-config.yaml](../../../../../../.pre-commit-config.yaml): ruff-pre-commit, a Python
  hook, and gitleaks) in the user's pre-commit cache, with names and paths that pre-commit generates.
  pre-commit is **not installed as a git hook** in this clone (`.git/hooks` holds only the samples)
  and the CI does not run it; it runs only when someone runs `pre-commit` by hand.
- The advisories need an environment name or destination path chosen by an attacker (alerts 19, 20
  and 40, the last for POSIX launchers), or links planted in an environment's directory (41, 42).
  None holds for pre-commit's own environments on this machine. **Not reachable as used.**
- **Fixed in** 21.14.9, eligible from **2026-10-24 16:09 UTC**.

## Proposal (for the maintainer's approval; nothing done)

1. **Early correction, without an exception to the 7-day rule:** until certifi 2026.10.19 is in the
   lock, **no download through `requests`** (no MAST, TIC or pyvo fetch) on any machine; stage 1's
   synthetic work needs none. Then one dependency update, planned as the rule asks: `uv lock
   --upgrade-package certifi --upgrade-package aiohttp --upgrade-package virtualenv --upgrade-package
   pillow` on or after 2026-10-27 02:25 UTC (every one eligible by then), the full suite, the
   comparison below, one commit. The alerts close when the lock changes. Downloads resume only when
   **the environment that runs them** uses the corrected bundle (checked with
   `requests.certs.where()` and certifi's version in that environment, the machine and every VM),
   not merely when the lock has it. Whether the system stores used by the project's own `urllib`
   clients trust the emSign roots stays unverified and is reported as such.
2. **An exception only if a download is needed before 2026-10-27:** certifi alone, recorded in the
   ROADMAP or an issue as an explicit exception to the 7-day rule with its reason (a CA bundle whose
   fix removes trust, against a release four days old). Not proposed unless that need arises.
3. **No lock of the phase is affected:** no v0.2.1 lock exists yet; the dependency update lands
   before any lock, as the pre-registration rules ask. The v0.3 locks and dossiers keep their own
   `uv.lock` in their code hash; their environment is the frozen one below.

## The frozen scientific environment (for comparison, apart from the working one)

- **What:** the environment of the current `uv.lock` (commit `5294c49`, the code of X2 and X2e),
  rebuilt with `uv sync --frozen` into `.cache/frozen-env-5294c49/`, used **only offline** for
  synthetic comparisons (no download, no image opened), where none of the reachable paths above is
  reached (certifi only matters for a TLS download; Pillow only encodes the project's own figures).
- **How it is compared:** the same subset of a synthetic lot (for example `x2_study.py run
  --subset`) in both environments, records compared with
  [../x2/scripts/compare_lots.py](../x2/scripts/compare_lots.py); the dossier tests run in both. A
  difference is recorded and explained before the working environment is used for any lot.
- **The working environment** is updated and is the only one used for downloads.
- Creating that environment and running the comparison come with the update's approval.

## New alerts of 2026-10-23 (43 to 54; read from their summaries, nothing changed)

Twelve alerts opened on 2026-10-23, all fixed by the versions already planned: Pillow 13.0.0
(alerts 43 to 53) and virtualenv 21.14.9 (alert 54); each alert's number, GHSA id and link,
summary and patched version, with the time of reading: [alerts-43-54.json](alerts-43-54.json)
([scripts/new_alerts.py](scripts/new_alerts.py)). By their summaries: image **decoding or
opening** (MPO, DCX, Spider, BMP, multi-frame loaders, PDF append, TarIO, PNG eXIf parsing,
WMF/EMF, the bundled OpenJPEG through `Image.open`), and **JPEG writing**; of the paths these
summaries name, none is the PNG encoding of the project's own figures, the one Pillow path the
project reaches. Alert 48 (undefined behaviour in native integer operations) does not name its
path in its summary: **its reachability is not determined**, and the conclusion above excludes it. Alert 54 (virtualenv's
generated files following links) needs links planted in an environment's directory, as alerts 41
and 42. The plan of the update (2026-10-27) is unchanged.

## Revision 2 (the maintainer's decisions of 2026-10-22 on the delivery `0abc6de`, item 5)

**Approved by the maintainer:** downloads through the vulnerable environment are suspended, and the
synthetic studies stay offline until the update. **What the suspension does and does not show:** it
reduces the exposure identified (the certifi bundle); it does **not** show that every network path
of the project is safe. In particular, **the system certificate stores used by the standard
library's `urllib` were not verified** (this machine's Windows store, the VMs' and the CI's OpenSSL
paths), nor are the tools' own stores.

**The network paths of the project, outside `requests` and through it** (read from the source; no
run; the list covers the paths found by reading `src/`, `scripts/` and the population scripts, not a
proof that no other exists, for example inside a third-party package's code path not exercised
here):

| Path | Client | Trust store | Used for | Under the suspension |
|---|---|---|---|---|
| MAST products (`adapter.download_checked` → lightkurve → astroquery) | `requests` | **certifi** | real light curves | suspended |
| TIC queries (`adapter`, astroquery `Catalogs`) | `requests` | **certifi** | target metadata | suspended |
| pyvo (a dependency of astroquery) | `requests` | **certifi** | not called by the project | suspended with them |
| astropy `download_file` (`astropy/utils/data.py`, lines 1266 to 1269: `certifi.where()` as `cafile` when certifi is installed) | `urllib` | **certifi** | astropy's own downloads (for example its IERS and leap-second tables) and any package that calls it; not called by the project's code; whether a real-data path triggers it was not verified | suspended (same bundle) |
| `refute/drand.py` (`urlopen`, fixed URLs) | `urllib` | the system store | drand beacons (pre-registration) | not covered by the certifi fix; system store unverified |
| `refute/packs/tess/ebcatalog.py` (`urlopen`, recorded URL) | `urllib` | the system store | the eclipsing-binary catalog | as above |
| `refute/packs/ml/fetch.py` (an HTTPS-only redirect opener) | `urllib` | the system store | the ML pack's data | as above |
| `refute/packs/ml/repository.py` (`git` in a subprocess) | git | git's own TLS backend (not verified) | the ML pack's repositories | as above |
| `refute/packs/ml/production.py` (the paper builds, in containers on the VM with the docker backend): `micromamba create` (conda channels, default `conda-forge`), `python -m pip install uv==…`, then `uv pip compile` and `uv pip install` | micromamba, pip, uv inside the container image | the container's own stores (the micromamba image, pinned by digest; the paper's base image), not the host's certifi (not verified) | building third-party papers' environments (v0.3) | not covered by the host update; outside stage 1's synthetic work |
| Tooling: `uv` (packages), `gh`, `git push` and `fetch`, the Codex CLI, `curl.exe` in `scripts/vm/Get-RefuteMedia.ps1`, `curl` on the VMs through the proxy | each its own | each its own (not verified) | development and the VMs | outside the science environment; not covered |

**The environment declaration.** Every lot records, before it starts and beside its manifest, the
effective environment: the interpreter's path, version and implementation, the platform, every
installed distribution's name and version, and the SHA-256 of `uv.lock` and `pyproject.toml`
([scripts/env_record.py](scripts/env_record.py)); after the lot, the record is made again and must
be equal. The record of the current lock (`uv.lock` SHA-256 `79e16fa7…`, 103 distributions,
CPython 3.13.16): [env-record-5294c49-lock.json](env-record-5294c49-lock.json), the reference of the
frozen comparison environment.

**The update of 2026-10-27, checked in full.** After `uv lock --upgrade-package …`, the **whole
diff of `uv.lock`** is read and listed (every package whose version, source or hash changed, and
every package added or removed), not only the four asked for: an upgrade can move dependencies too.
Every change must satisfy the 7-day rule (`exclude-newer-span = "P7D"` in the lock); an unexpected
change is reported before the commit. Then: `uv sync --frozen`, the environment record, the full
suite, the comparison with the frozen environment, and a check that the running environment uses
the corrected bundle (`certifi.__version__`, `requests.certs.where()`) on this machine and on each VM
that downloads.

**Fixed before every lot and the confirmation.** The final environment is fixed and checked (its
record) before execution; **no dependency is updated during a lot** or between the sub-lots of one
lot; a lot whose environment record changes while it runs is stopped and reported. Spec C's choice
lot (X2f) and its confirmation are proposed to run in the same final environment, after the update
([x2f-declaration.md](x2f-declaration.md), section 7).
