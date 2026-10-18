# The VM proof of the container readers (2026-10-18)

The proof that `docs/validation/v0.3/wp3-data-sources-acceptance.md` (section 4.2) requires
before a container reader is used on a paper: `scripts/vm/reader_vm_test.py` on the
Refute VM with the docker backend. The reader is `src/refute/packs/ml/container_reader.py`,
SHA-256 `4b64c5edda6bd940aa392d02a193a0e0547f8b4ddc30f5bb96bf879ad41cb733`, in every record.

## The record that decides: `reader-vm-test-20261018T153704Z.json`

This run used Refute commit `404c136`, after the end-of-round review.

**What it passes on.** A reader passes only when all five checks hold:
- the count equals the expected count;
- the reader exited 0 and was not stopped;
- the probe ran;
- `-I -S` was in force (`isolated` 1, `no_site` 1);
- the mount of the dataset was read only (`ro`, from `/proc/self/mountinfo`).

| Reader | Image (base) | Library | Count read / expected | Data mount |
|---|---|---|---|---|
| `cifar_python` | python 3.12-slim | numpy | 4000 / 4000 | `ro,relatime` |
| `excel` | python 3.12-slim | pandas, openpyxl | 123 / 123 | `ro,relatime` |
| `dgl` | python 3.11-slim | dgl 1.1.3, torch 2.1.2 | 57 / 57 | `ro,relatime` |

**What the probe saw.** The probe runs with the reader's own command prefix:
`/usr/bin/env -i`, the thread variables, the built interpreter, `-I -S`.
- **The environment:** the thread variables, plus `LC_CTYPE=C.UTF-8`. Python's locale
  coercion sets `LC_CTYPE` itself at start-up (PEP 538).
- **`sys.path`:** the interpreter's standard library and the venv's own `site-packages`.
  The library is imported from there.
- **The working folder:** `reader.py` and the read-only dataset. In the `dgl` case,
  dgl's own `~/.dgl/config.json` is there too: with no `HOME`, dgl writes it into the
  working folder as `./~/.dgl/config.json`. That is the only file written there besides
  the answer.

## The earlier records

- **`reader-vm-test-20261018T140753Z.json`** (Refute commit `acd92a9`). `cifar_python` and
  `excel` counted correctly. Its `dgl` entry is a failure of the test's own graph
  generator: dgl 2.1.0 imports `setuptools.extern` without declaring it. The script of
  that commit recorded the mounts without their options, and compared only the count.
- **`reader-vm-test-dgl-20261018T142936Z.json`** (Refute commit `3ea0e1a`). `dgl` counted
  57 / 57, with the same limits of the record.
- **The failed `dgl` attempts.** Each was a failure of the test environment before the
  reader ran:

  | Record | Commit | Failure |
  |---|---|---|
  | `…T141455Z-failed.json` | `ce38436`, setuptools pinned | no `torchdata.datapipes` in the latest torchdata |
  | `…T142111Z-failed.json` | `cc564d9`, torchdata 0.8.0 | its extension needs the system's libcurl |
  | `…T142624Z-failed.json` | `f84014a`, dgl 1.1.3 on Python 3.11 | dgl imports `packaging` without declaring it |

  The change to Python 3.11 in `f84014a` also added the script's `--python-image-311`
  option. One more attempt, between the first record and `ce38436`, is not recorded: the
  VM's checkout could not fetch through the proxy, so it ran the script of `acd92a9` again
  and failed as the first record did. Its record was overwritten by the next one.

The CIFAR case uses a batch in the real format, with the images as a NumPy array inside
the pickle. Unpickling it imports numpy. The reader's first version failed on it under
`-I -S`, which the maintainer's check of 2026-10-18 found; it was fixed in `0c15e5f`.
