"""The split readers of the ML pack (src/refute/packs/ml/readers.py), offline."""

from __future__ import annotations

import io
import zipfile

import numpy as np
import pyarrow as pa
import pyarrow.parquet as pq

from refute.packs.ml import readers as rd


def test_npz_npy_csv_tsv_jsonl(tmp_path):
    npz = tmp_path / "d.npz"
    np.savez(npz, x_train=np.zeros((7, 3)), x_test=np.zeros((4, 3)))
    assert rd.count_split(npz, "reader:npz:x_train") == 7
    assert rd.count_split(npz, "reader:npz:x_test") == 4
    npy = tmp_path / "d.npy"
    np.save(npy, np.zeros(5))
    assert rd.count_split(npy, "reader:npy:") == 5
    csv = tmp_path / "d.csv"
    csv.write_text("a,b\n1,2\n3,4\n\n5,6\n")
    assert rd.count_split(csv, "reader:csv:rows") == 3
    tsv = tmp_path / "d.tsv"
    tsv.write_text("a\tb\n1\t2\n")
    assert rd.count_split(tsv, "reader:tsv:rows") == 1
    jsonl = tmp_path / "d.jsonl"
    jsonl.write_text('{"a": 1}\n\n{"a": 2}\n')
    assert rd.count_split(jsonl, "reader:jsonl:rows") == 2


def test_parquet_and_zip(tmp_path):
    table = pa.table({"x": list(range(9))})
    parquet = tmp_path / "d.parquet"
    pq.write_table(table, parquet)
    assert rd.count_split(parquet, "reader:parquet:rows") == 9
    buf = io.BytesIO()
    np.savez(buf, y=np.zeros(11))
    archive = tmp_path / "d.zip"
    with zipfile.ZipFile(archive, "w") as z:
        z.writestr("inner/data.npz", buf.getvalue())
    assert rd.count_split(archive, "reader:zip:inner/data.npz!npz:y") == 11


def test_no_reader_or_unreadable_gives_no_count(tmp_path):
    f = tmp_path / "d.npz"
    np.savez(f, x=np.zeros(3))
    assert rd.count_split(f, "the first 3 rows of the file") is None  # free text: not read
    assert rd.count_split(f, "reader:npz:missing") is None
    assert rd.count_split(f, "reader:hdf5:x") is None  # no hdf5 reader in version 1
    obj = tmp_path / "o.npy"
    np.save(obj, np.array([{"a": 1}], dtype=object), allow_pickle=True)
    assert rd.count_split(obj, "reader:npy:") is None  # pickled data is never loaded


def test_split_counts_all_or_none(tmp_path):
    f = tmp_path / "d.npz"
    np.savez(f, tr=np.zeros(5), te=np.zeros(2))
    splits = {"train": {"source": "reader:npz:tr"}, "test": {"source": "reader:npz:te"}}
    assert rd.split_counts(f, splits) == {"train": 5, "test": 2}
    splits["test"] = {"source": "free text"}
    assert rd.split_counts(f, splits) is None
