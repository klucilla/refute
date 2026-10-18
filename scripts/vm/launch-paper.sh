#!/bin/bash
# Starts one paper run on the Refute VM as a systemd unit of its own, refute-<paper>.service,
# owned by the user refute: it survives the end of the SSH session, has no automatic
# restart, and a second start of the same unit is refused by systemd (the unit name is
# fixed by the paper id). Run by the agent over SSH, after the maintainer's approval of the
# paper's run (the first run of third-party code needs that approval, V4).
#   scripts/vm/launch-paper.sh <paper> <claim.json> [--data name=path ...] [--micromamba-image img]
# Stop: sudo systemctl stop refute-<paper>.service (the engine gets SIGTERM and kills its
# own running containers by id before it exits: production.run_production), or the whole
# VM with .cache/vm/stop-all.ps1 on the host.
set -euo pipefail
PAPER=${1:?paper id}; CLAIM=${2:?resolved claim file}; shift 2
BASE=/home/refute/refute-run/papers/$PAPER
CHECKOUT=/home/refute/refute-run/refute
[ -e "$BASE" ] && { echo "refused: $BASE exists"; exit 1; }
mkdir -p "$BASE"
cp "$CLAIM" "$BASE/claim.json"
git -C "$CHECKOUT" rev-parse HEAD > "$BASE/refute-commit.txt"
sudo -n systemd-run --unit "refute-$PAPER" --uid refute --gid refute \
  --property=Restart=no --property=WorkingDirectory="$CHECKOUT" \
  --property=StandardOutput=append:"$BASE/engine.log" --property=StandardError=append:"$BASE/engine.log" \
  --setenv=HOME=/home/refute \
  --setenv=HTTPS_PROXY=http://10.231.71.3:3128 --setenv=HTTP_PROXY=http://10.231.71.3:3128 \
  --setenv=https_proxy=http://10.231.71.3:3128 --setenv=http_proxy=http://10.231.71.3:3128 \
  "$CHECKOUT/.venv/bin/python" -m refute.packs.ml.production \
  --claim "$BASE/claim.json" --paper "$PAPER" --root "$BASE/work" --out "$BASE/dossier" \
  --cache /home/refute/refute-run/cache --run-phase-flag "$BASE/run-phase-approved" "$@"
echo "started refute-$PAPER at $(date -u +%Y-%m-%dT%H:%M:%SZ)"
