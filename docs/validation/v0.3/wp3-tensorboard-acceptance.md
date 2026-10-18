# WP3 addendum: a scalar read from a TensorBoard event file

Addendum to [wp3-acceptance.md](wp3-acceptance.md) (W3.11, metric extraction), committed
before its tests and code (plan section 11).

## 0. Why

Some repositories write a metric only to a TensorBoard event file. 2407.11735 (main
sample) writes its AUROC values with `tf.summary.scalar("ood/auroc_<score>", ...)` to a
writer created by `tf.summary.create_file_writer(<train_dir>/summaries)` (`prosub_ossl.py`,
lines 495 to 517, and `base.py`, line 23, of the repository read for the inventory); the
value is printed nowhere else. Today `metric_extraction` reads JSON, CSV or text, so such a
value cannot be read, whatever the run does.

The maintainer decided on 2026-10-18 that a generic reader of event files is engine work:
it may enter before the lock of the main sample, with acceptance criteria before the code
and a proof on the VM, and with no new dependency if possible. If it is not ready before
the lock, a drawn AUROC claim of 2407.11735 is `INCONCLUSIVE` by a limitation of Refute.
The freeze of the inventories does not wait for it. This is a generic contract of the
extraction, not a change made to obtain a conclusion on a paper.

## 1. The format (external facts, read on 2026-10-18)

- **Records** (TFRecord), https://www.tensorflow.org/tutorials/load_data/tfrecord: each
  record is `uint64 length`, `uint32 masked_crc32_of_length`, `byte data[length]`,
  `uint32 masked_crc32_of_data`, concatenated; the CRC is CRC-32C (Castagnoli) and the mask
  is `((crc >> 15) | (crc << 17)) + 0xa282ead8`, on 32-bit unsigned integers. Integers are
  little-endian.
- **Event**,
  https://raw.githubusercontent.com/tensorflow/tensorflow/master/tensorflow/core/util/event.proto:
  `wall_time` double = 1, `step` int64 = 2, and a oneof `what` with `file_version` string
  = 3, `graph_def` bytes = 4, `summary` Summary = 5, `log_message` = 6, `session_log` = 7,
  `tagged_run_metadata` = 8, `meta_graph_def` bytes = 9; `source_metadata` = 10.
- **Summary**,
  https://raw.githubusercontent.com/tensorflow/tensorflow/master/tensorflow/core/framework/summary.proto:
  `repeated Value value = 1`; Value has `tag` string = 1, `metadata` = 9, `node_name` = 7,
  and a oneof `value` with `simple_value` float = 2, `obsolete_old_style_histogram` = 3,
  `image` = 4, `histo` = 5, `audio` = 6, `tensor` TensorProto = 8.
- **TensorProto**,
  https://raw.githubusercontent.com/tensorflow/tensorflow/master/tensorflow/core/framework/tensor.proto:
  `dtype` = 1, `tensor_shape` = 2, `version_number` = 3, `tensor_content` bytes = 4,
  `float_val` = 5 (packed), `double_val` = 6 (packed), and other typed lists from 7 on.
- **TensorShapeProto**,
  https://raw.githubusercontent.com/tensorflow/tensorflow/master/tensorflow/core/framework/tensor_shape.proto:
  `dim` = 2 (Dim: `size` = 1, `name` = 2), `unknown_rank` bool = 3.
- **DataType** values used here: `DT_FLOAT` = 1, `DT_DOUBLE` = 2 (`types.proto`, same
  folder as `tensor.proto`).

## 2. The rule (W3.11b)

- **Where.** A fourth way of `metric_extraction` (method, and reference when it has its
  own extraction): `tensorboard: {tag: <text>, step: <integer >= 0 | "last">}`, only with
  `from: file`, and never together with `json_path`, `csv` or `regex`. The `file` follows
  W3.11 and W3.11a unchanged (`{seed}`, one `*` component; event file names hold a time, a
  host and a process number, so the last component is usually `*`). The bytes are read by
  the same function as every other output (`read_output_bytes`: no symbolic link, one hard
  link, checked again on the open handle, 64 MiB at most, one read per file within an
  evaluation). The count selectors of the coverage routes do not accept `tensorboard`
  (refused at validation): nothing needs it now.
- **No new dependency.** The engine reads the records and the few protobuf fields above
  with its own code: CRC-32C by a table, a protobuf wire-format reader of varints,
  fixed 32-bit and 64-bit fields and length-delimited fields.
- **Every record is checked, the whole file first.** The file is a sequence of whole
  records: a length or data CRC that does not match, a record cut short (in its header,
  data or footer), or bytes left after the last whole record make the whole file
  unreadable (`ExtractionError`); a bad record is never skipped. Every record is decoded
  and checked before any value is selected, so a corruption after a valid value is still
  an error (no early return). The first record must be an Event whose only `what` is a
  `file_version` that starts with `brain.Event:`.
- **Protobuf wire format.** Wire types 0 (varint), 1 (64-bit), 2 (length-delimited) and 5
  (32-bit) are read; 3, 4, 6 and 7 are an `ExtractionError`. A varint longer than 10
  bytes, a tenth byte above 1 (beyond 64 bits), a varint not terminated, a field number 0
  or above 2^29 - 1, a fixed field or a length cut short, and a length beyond its message
  are an `ExtractionError`. Fields not listed in section 1 are skipped by their wire type,
  except inside the selected tensor (below). A field listed in section 1 with another wire
  type is an `ExtractionError`.
- **One value per field, one alternative per oneof.** This is a deliberate restriction of
  Refute: protobuf would keep the last one, and the reading would then depend on the order
  of the fields. A field that appears twice where the format allows one value (`wall_time`,
  `step`, `file_version`, `summary`, `tag`, `metadata`, `simple_value`, `tensor`, `dtype`,
  `tensor_shape`, `tensor_content`, `unknown_rank`) is an `ExtractionError`. More than one
  alternative of a oneof in one message, whatever their order, is an `ExtractionError`:
  for `Event.what` (fields 3 to 9) and for `Summary.Value.value` (fields 2 to 6 and 8).
  Event payloads other than `summary` are not read further.
- **Defaults (proto3).** An absent `step` is 0 (proto3 cannot tell an absent step from
  step 0, and TensorFlow omits step 0); `step` is a signed int64 (two's complement of the
  varint), so a negative step stays negative. An absent `dtype` is `DT_INVALID` and is an
  `ExtractionError`, never inferred from the size of the bytes. An absent `tensor_shape`
  is an `ExtractionError` (outside the supported profile; if the proof on the VM shows a
  real writer that omits it, this criterion is revised before the code is accepted). An
  `unknown_rank` that is present and true is an `ExtractionError`; present and false is
  the same as absent.
- **The values of the tag.** A value is named by its `tag`, compared byte for byte (UTF-8)
  with the claim's `tag`. **Every** value with that tag in the file, at every step, must
  be a scalar, given as exactly one of:
  - `simple_value` (a float32, wire type 5);
  - `tensor` with `dtype` `DT_FLOAT` or `DT_DOUBLE`, a shape of rank 0 (no `dim`), and
    exactly one element in total, given either by `tensor_content` (exactly 4 or 8 bytes,
    little-endian, by the dtype) or by the typed list of its dtype: `float_val` for
    `DT_FLOAT` (packed, wire type 2, a payload whose length is a multiple of 4, or not
    packed, wire type 5), `double_val` for `DT_DOUBLE` (packed, a multiple of 8, or not
    packed, wire type 1); all occurrences of the list, packed and not packed, are joined,
    and the total must be one element. `tensor_content` together with a typed list, a
    typed list of the other dtype, or any other typed list or content field (fields 7 to
    18) is an `ExtractionError`, never skipped.

  Any other value with that tag (an image, a histogram, audio, a tensor of another dtype,
  rank or size) is an `ExtractionError`, even at a step that is not selected: the reader
  does not choose among the tag's values by their kind.
- **The steps of the tag.** In record order, the steps at which the tag appears must
  strictly increase; a repeated or decreasing step (a restart written into the same file,
  two values at one step in one Event or in two) is an `ExtractionError`. Two event files
  matching the `*` are already an error before any content is read (W3.11a); the reader
  never picks the newest.
- **The step selected.** `step: <n>` selects the value with that tag at step `n`;
  `step: "last"` selects the value at the greatest step of the tag. Exactly one value is
  then selected, or the step is absent and it is an `ExtractionError`. The choice never
  depends on `wall_time` or on the value. `"last"` means the greatest step of the tag in
  that file, not "the final evaluation": when a claim needs the final evaluation, that
  link comes from the claim's `selected_evaluation` and its evidence, not from the reader;
  without it the check is `INCONCLUSIVE`.
- **The token.** The value is a binary float; it is written as its exact decimal
  expansion, with no exponent (`Decimal(float)`, formatted with `f`; a negative zero is
  `-0`), and checked as every other token. A NaN or an infinity among the values of the
  tag, at any step, selected or not, is an `ExtractionError`.
  `Extracted` records that the token comes from a binary float, and of which width
  (`float32` or `float64`).
- **No printed interval for a binary value.** `metric_recompute` and the coverage routes
  that link a computed value to the extracted token (`printed_interval`, and `_interval`
  and `_inside` in `integration.py`) derive an interval from the token's decimal places,
  which is meaningless for a binary value: with the token `0.5` of a float32 they would
  accept `0.54`, and with the exact expansion of the float32 of `0.1` they would reject
  `0.1`. A binary value also carries the rounding of the arithmetic of the program that
  computed it (a float32 sum, then a division, in 2407.11735), which no interval of the
  last cast describes. So these checks are not run on a binary token: each gives
  `INCONCLUSIVE` with the reason "a value read from a binary float has no printed
  interval", never `PASS` and never `FAIL`. A comparison model for binary values is not
  part of this addendum.
- **Exact comparisons with long tokens.** The predicates of the verdict
  (`predicates.py`: `value_predicate`, `comparison_predicate`, which `ablation_predicate`
  uses, and `trivial_baseline_predicate`) computed their bounds in a Decimal context of 50
  digits, so a long token, or a sum that needs more than 50 digits, was rounded before the
  comparison (the float64 of `0.1`, compared with itself at tolerance 0, failed). Their
  comparisons are made exactly (exact rational arithmetic on the Decimal values), and the
  tolerance is computed exactly as a sum, a difference, a product or a maximum of exact
  numbers (`one_number`, `widen`). A square-root tolerance (`sqrt(a² + b²)`, in
  `difference_tolerance` and `ablation_tolerance`) keeps its exact square, and a predicate
  decides `l <= sqrt(S)` as `l <= 0 or l² <= S`; the record shows the root rounded down to
  50 digits (checked against the exact square), which decides nothing. This applies to
  every token, not only to binary ones.
- **Where the exact values travel** (Codex review of the round, 2026-10-18). A predicate's
  `Outcome` carries the exact square of a square-root tolerance, and the guard of
  `reproduction.decide_on_mean` (a passing set narrower than the bracket of a mean that
  is not a finite decimal) compares `4 S` with the bracket's square, never the rounded
  record. The trivial baselines are kept as exact fractions (`1/3` for a random guess
  among 3 classes) and compared as fractions; their 50-digit values are records only.
- **A budget for exact arithmetic.** An extracted token with more than 4,096 significant
  digits, or a decimal exponent beyond ±4,096 (`1e999999999` is a short token), is an
  `ExtractionError` "outside the exact-arithmetic budget of Refute (a limitation of
  Refute)": exact arithmetic on it would expand millions of digits. Every float32 and
  float64 expansion fits (at most 767 digits, exponent -1074).
- **The source.** `Extracted.source` is `file:<the resolved path>`, as for every file, so
  W3.12a compares the resolved paths unchanged; the claim holds the tag and the step.
- **What the rule shows, and what it does not.** It shows that the value was written under
  that tag and step to the one event file the run created. It does not show over how many
  examples the metric was computed: `metric_extracted` still needs the coverage evidence
  of W3.12. For 2407.11735 the event file holds no count of the test examples, so unless
  another coverage route of the claim proves it, the AUROC claim is `INCONCLUSIVE` by
  coverage. The reader is not changed to avoid that.
- **2407.11735, checked with Codex on 2026-10-18** (the maintainer's decision 4). None of
  the coverage routes the engine offers shows the test examples with the frozen command:
  no count of the evaluation is printed (`printed_count`; the `%d records found` of
  `scripts/create_split.py` counts the training file); `sufficient_statistics` does not
  apply to AUROC and the accuracy's `correct/total` is not written; no test predictions
  are saved (`saved_predictions`; `savestats` is off by default and covers the unlabeled
  training set); the hook observes `sklearn.metrics.roc_auc_score` and
  `accuracy_score`, while the paper computes AUROC with its own TensorFlow function
  (`utils.py`, `auroc_rank_calculation`) and accuracy with
  `tf.keras.metrics.SparseCategoricalAccuracy`. A drawn claim of 2407.11735, AUROC or
  accuracy, is therefore `INCONCLUSIVE` by coverage, a limitation of Refute recorded as
  such; it stays in the draw.

## 3. Synthetic cases

Event files are built in the tests by an encoder written in the test module, separate
from the reader, and checked against fixed vectors: CRC-32C of `123456789` is `0xE3069283`
(RFC 3720, appendix B.4, and the Castagnoli check value), and the masked form of one known
CRC.

**Must pass:** a `simple_value` scalar; a `DT_FLOAT` rank-0 tensor by `tensor_content`,
by a packed `float_val` and by a not packed `float_val`; a `DT_DOUBLE` tensor by
`tensor_content`, by a packed and by a not packed `double_val`; `step: n` and
`step: "last"` with the tag at several steps; step 0 written by omitting the field; a
negative step before positive ones; other tags, images and graph records in the same file,
ignored; unknown fields skipped; `unknown_rank` present and false; an event file named
through `*`; the token of the float32 of `0.1` equal to its exact expansion; a negative
zero (`-0`), a subnormal and the largest finite float32 and float64; the same selection
when the fields of a message are permuted, when independent records are permuted (the
tag's steps still increasing) and when `wall_time` contradicts the step order.

**Must fail** (`ExtractionError`, or refused at validation):
- a wrong length CRC; a wrong data CRC; a record cut in its header, data or footer; bytes
  after the last record; an empty file; a first record that is not an Event with only a
  `file_version` starting with `brain.Event:`; a corrupt record after the record holding a
  valid selected value;
- a varint of 11 bytes, a tenth byte above 1, a varint not terminated, field number 0, a
  field number above 2^29 - 1, a fixed32 or fixed64 cut short, a length beyond its
  message, a wire type 3, 4, 6 or 7, a known field with the wrong wire type;
- a field repeated where one value is allowed (each field of the list in section 2); two
  alternatives of `Event.what` (`summary` with `file_version`, `graph_def` or
  `session_log`); two alternatives of `Summary.Value.value` (`simple_value` with `tensor`,
  `image`, `histo` or `audio`), in either order;
- the tag absent; the step absent; two values at one step (in one event, in two events,
  equal or not); a decreasing step of the tag; `"last"` after a restart in the same file;
- under the tag, at the selected step or at another one: an image, a histogram, audio, a
  `DT_INT32`, `DT_HALF` or `DT_INVALID` (absent `dtype`) tensor, an absent
  `tensor_shape`, `unknown_rank` true, a rank-1 tensor, a tensor with two elements (in one
  packed block, in two not packed occurrences, or packed plus not packed), a packed
  payload whose length is not a multiple of 4 or 8, `tensor_content` of 3, 5, 7 or 9
  bytes, `tensor_content` with `float_val`, `float_val` in a `DT_DOUBLE` tensor,
  `double_val` in a `DT_FLOAT` tensor, `int_val` or any of fields 7 to 18 in the tensor;
- NaN, `+inf`, `-inf`;
- two event files matching the `*` (W3.11a), a file over 64 MiB;
- at validation: `tensorboard` with `from: log`, with another way, an empty `tag`, a
  negative or boolean `step`, a `step` text other than `"last"`, and `tensorboard` in a
  count selector.

**Integration** (whole evaluations with a synthetic run): a claim read by `tensorboard`
reaches `metric_extracted` through a coverage route that does not use the token's
interval, and the value enters the verdict, in `fraction` and in `percent`; with
`metric_recompute`, and with a coverage route that links a computed value to the token,
those checks are `INCONCLUSIVE` with the reason of section 2, never `PASS` or `FAIL`.

**Exact predicates:** the float64 of `0.1` as an exact 55-digit token, compared with
itself at tolerance 0 in every value mode, passes; a token one unit of its last digit
outside the bound fails, in every value and comparison mode and in `trivial_baseline`
(an advantage above a tolerance by `1e-55` passes, equal to it fails); a value of 50
digits whose bound needs more digits (`x = tol = 10^49`, published `-0.1`, two-sided)
fails; the tolerance of a product and a maximum is exact; with a square-root tolerance, a
decimal just above the 50-digit root of 2 but whose square is below 2 passes, one whose
square is above 2 fails, and `widen` keeps the exact square.

## 4. Proof on the VM

Event files written by real writers are read by the reader:

- on the VM, in a container of the pinned Python image, a short script writes known
  values with TensorFlow 2 (`tf.summary.scalar`, which writes a tensor) and with the
  TensorFlow 1 compatible summary (`simple_value`), at several steps, with an image under
  another tag; the package versions and the bytes' SHA-256 are recorded;
- the files are committed as test fixtures with the script and the record, and a test
  reads them offline (no network in the tests); the values read must equal the float32
  (or float64) of the values written.

Running TensorFlow on the VM is the first run of that third-party code. The maintainer
approved it on 2026-10-18, only to make these fixtures, with these conditions:

- after the publication of the main inventories, not before;
- the version 2407.11735 declares, if it declares one that runs on the pinned Python
  image; otherwise a stable version uploaded at least 7 days before (the upload date read
  on PyPI and recorded); the CPU-only variant when the version has one; the version, the
  SHA-256 of the wheels and the `pip freeze` are recorded;
- installed in the build profile, from PyPI only, through the proxy; the event files are
  written in the run profile, with no network;
- the image with TensorFlow serves only this proof: no run of a paper reuses it, and the
  engine never imports TensorFlow (the reader has no new dependency);
- the fixtures, the script and the record (versions and SHA-256 of the bytes) are
  committed, and the test reads them offline;
- if the real writer omits `tensor_shape` or leaves the supported profile otherwise, this
  criterion is revised before the code is accepted, with the reason recorded.

**Result (2026-10-18,
[`wp3-results/tensorboard-vm-fixtures-20261018.json`](wp3-results/tensorboard-vm-fixtures-20261018.json)).**
`tensorflow-cpu==2.14.0` (wheel cp311 SHA-256
`8886642da74839b6cadcbc2f748ebdfc20e83b71f2069686485f9a186bff1b07`, uploaded
2023-09-26) on the pinned Python 3.11 image, with `numpy<2` added: the first build
resolved numpy 2.4.6 and `import tensorflow` failed (its binaries need numpy 1). The lock
used `--exclude-newer 2026-10-11`; every wheel was uploaded on or before that date. Both
writers stay within the supported profile, so the criterion is not revised:
`tf.summary.scalar` writes a `DT_FLOAT` tensor with a present, empty `tensor_shape` and
4 bytes of `tensor_content`; the TensorFlow 1 writer writes `simple_value`; both omit the
step 0; the image is a `DT_STRING` tensor under its own tag, ignored. The two files
(`tests/fixtures/tensorboard/`) are read offline by `tests/test_ml_tbevents.py`, with the
values equal to the float32 of the values written.

## 5. Regression

Every existing extraction test passes unchanged; `json_path`, `csv` and `regex` are read
as today. Every existing predicate and verdict test passes unchanged. The exact
arithmetic can change a decision at a boundary that the 50-digit arithmetic decided
wrongly (as in the cases above), even with short tokens. No claim already written and no
published dossier changes its decision, checked on 2026-10-18: the development claim of
2304.14390 (`calibration/v0.3/dev/2304.14390/claim.json`) resolves again to the same bytes
(SHA-256 `4a7a1c510d3079fb77b20bca890ecc265d2abf1bf310185c66bd91c4dca0e5ea`), and its
recorded `base_reproduction` (`|-3.971605134010315 - -5.35| <= 1.540`, PASS) is the same,
with the same tolerance and message, under the exact predicates. A claim read by
`json_path`, `csv` or `regex` resolves to the same hash (an absent `tensorboard` is not
written).
