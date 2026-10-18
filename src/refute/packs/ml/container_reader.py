"""Refute's container reader: counts the examples of declared splits in formats that need a
library or run code (docs/validation/v0.3/wp3-data-sources-acceptance.md, section 4.2).

This file is copied, byte for byte, into a fresh folder of its own and run there, in the
paper's image after the build, as ``<interpreter> -I -S reader.py '<request JSON>'``: with
``-S`` no ``.pth`` file and no ``sitecustomize`` installed by the build is processed, so
the only library folders added are those of the interpreter itself (``purelib`` and
``platlib``), appended here without processing ``.pth`` files. It uses the standard library
and, for one reader, the library of the format, imported from the paper's environment.

The request (built by ``readers.container_request``) names the file (a path relative to
the working folder, where the dataset is mounted read only) and, for each split, its
reader, an optional member of an archive and an optional argument (a sheet, an edge
type). The answer is ``out/counts.json``,
created by this run (never over an existing file): a JSON object from split name to a
non-negative integer. Any error ends the run with a non-zero exit and no answer. Readers:

- ``cifar_python``: the length of the ``labels`` (CIFAR-10) or ``fine_labels`` (CIFAR-100)
  list of each pickled batch named (members joined by ``+``) in a tar archive, summed;
- ``excel``: the data rows ``pandas.read_excel`` returns for a sheet (by name, or by
  0-based index when the argument is digits), the header row excluded;
- ``dgl``: the edges of one canonical edge type (``src,etype,dst``) in the first graph
  ``dgl.load_graphs`` returns.

Residual trust (section 4.2): the reader imports the paper's interpreter and libraries, and
``cifar_python`` unpickles, which can run code. A compromised environment can write a
well-formed, false answer; the host checks its form, not its truth.
"""

import json
import os
import sys
import sysconfig
import tarfile

ANSWER = os.path.join("out", "counts.json")


def _library_paths():
    # with -S, Python 3.12 and 3.13 leave sys.prefix at the base installation for a venv:
    # the venv is the folder above the interpreter's folder when it holds pyvenv.cfg (the
    # interpreter's own path, not the file a link points to)
    scheme_vars = {}
    prefix = os.path.dirname(os.path.dirname(os.path.abspath(sys.executable)))
    if os.path.isfile(os.path.join(prefix, "pyvenv.cfg")):
        scheme_vars = {"base": prefix, "platbase": prefix}
    for key in ("purelib", "platlib"):
        path = sysconfig.get_paths(vars=scheme_vars).get(key)
        if path and path not in sys.path:
            sys.path.append(path)


def _member(archive, name):
    found = [m for m in archive.getmembers() if m.name == name]
    if len(found) != 1 or not found[0].isfile():
        raise ValueError("the archive has not exactly one file named " + name)
    return archive.extractfile(found[0])


def cifar_python(path, member, arg):
    import pickle

    # a real batch holds its images as a NumPy array: unpickling it imports numpy from the
    # paper's environment (the maintainer's check of 2026-10-18)
    _library_paths()
    total = 0
    with tarfile.open(path, "r:*") as archive:
        for name in member.split("+"):
            with _member(archive, name) as handle:
                batch = pickle.load(handle, encoding="bytes")
            labels = batch.get(b"labels", batch.get(b"fine_labels"))
            if not isinstance(labels, list):
                raise ValueError("a batch with no label list: " + name)
            total += len(labels)
    return total


def excel(path, member, arg):
    _library_paths()
    import pandas

    sheet = int(arg) if arg.isdigit() else arg
    if member:
        import io
        import zipfile

        with zipfile.ZipFile(path) as archive:
            names = [n for n in archive.namelist() if n == member]
            if len(names) != 1:
                raise ValueError("the archive has not exactly one member named " + member)
            frame = pandas.read_excel(io.BytesIO(archive.read(member)), sheet_name=sheet)
    else:
        frame = pandas.read_excel(path, sheet_name=sheet)
    return int(len(frame))


def dgl(path, member, arg):
    if member:
        raise ValueError("dgl reads a bare file")
    _library_paths()
    import dgl as library

    parts = arg.split(",")
    if len(parts) != 3 or not all(parts):
        raise ValueError("a canonical edge type is src,etype,dst")
    graphs, _ = library.load_graphs(path)
    return int(graphs[0].num_edges(tuple(parts)))


READERS = {"cifar_python": cifar_python, "excel": excel, "dgl": dgl}


def main(argv):
    request = json.loads(argv[1])
    path = request["path"]
    counts = {}
    for split, place in request["splits"].items():
        read = READERS[place["reader"]]
        counts[split] = read(path, place["member"], place["arg"])
    os.makedirs("out", exist_ok=True)
    fd = os.open(ANSWER, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o644)
    with os.fdopen(fd, "w", encoding="utf-8") as out:
        json.dump(counts, out, sort_keys=True)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
