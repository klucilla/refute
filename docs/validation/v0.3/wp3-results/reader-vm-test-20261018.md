# The VM proof of the container readers (2026-10-18)

The proof that `docs/validation/v0.3/wp3-data-sources-acceptance.md` (section 4.2) requires
before a container reader is used on a paper. `scripts/vm/reader_vm_test.py` ran on the
Refute VM with the docker backend. The reader is `src/refute/packs/ml/container_reader.py`,
SHA-256 `4b64c5edda6bd940aa392d02a193a0e0547f8b4ddc30f5bb96bf879ad41cb733`, in both records.

| Reader | Record | Image (base) | Library | Count read / expected |
|---|---|---|---|---|
| `cifar_python` | `reader-vm-test-20261018T140753Z.json` | python 3.12-slim | numpy | 4000 / 4000 |
| `excel` | `reader-vm-test-20261018T140753Z.json` | python 3.12-slim | pandas, openpyxl | 123 / 123 |
| `dgl` | `reader-vm-test-dgl-20261018T142936Z.json` | python 3.11-slim | dgl 1.1.3, torch 2.1.2 | 57 / 57 |

Each record shows what the probe saw. The probe runs with the reader's own command prefix:
`/usr/bin/env -i`, the thread variables, the built interpreter, `-I -S`.

- **The environment:** the thread variables, plus `LC_CTYPE=C.UTF-8`. Python's locale
  coercion sets `LC_CTYPE` itself at start-up (PEP 538); no other variable of the image
  reaches the reader.
- **The flags:** `isolated` 1 and `no_site` 1.
- **`sys.path`:** the interpreter's standard library and the venv's own `site-packages`,
  added by the reader's library-path step. The library is imported from there.
- **The working folder:** it holds only `reader.py` and the dataset, which is mounted read
  only from the VM's file.

**The `dgl` case.** The first record has no `dgl` result. Before the passing run, four
attempts failed while the test environment was being built and its graph file written,
before the reader ran:

- dgl 2.x needs `torchdata.datapipes`;
- the only `torchdata` wheel for Python 3.12 needs the system's libcurl;
- dgl imports `setuptools.extern.packaging` and `packaging` without declaring them.

The commits `ce38436`, `cc564d9`, `f84014a` and `3ea0e1a` changed only the requirements of
the test case. The reader did not change.

The CIFAR case uses a batch in the real format: the images are a NumPy array inside the
pickle. Unpickling it imports numpy. The reader's first version failed on it under -I -S,
and the maintainer's check of 2026-10-18 found this; it was fixed in `0c15e5f`.
