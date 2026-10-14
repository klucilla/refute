Phase G, third review round (branch commit b7c724c, harness 408020676340...).
Commands: see the bash blocks of the session; the outputs here are:
- r1-evidence.txt: selftest-4 R1 states (snapshot diffs, lot-0 records, tampered record 3, log lines)
- d-checks.log: generate --check against manifests of an earlier commit/harness; metrics at HEAD over runs of 1692d99 with --records
- d3-r2.log: resume across a HEAD change, harness_commit recorded (HEAD), untracked harness copy refused in generate/analyze/orchestrate
- check-s4.json, check-s3.json: check reports of the two generate --check runs
- snr_check.txt, ser_check.txt, stats_check.txt, seed_check.txt: kept verifiers against harness 40802067 (identical to round 2)
- compare_outcomes.txt: selftest-4 short runs vs selftest-3 runs (identical outcomes)
