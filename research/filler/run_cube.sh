#!/usr/bin/env bash
# ---------------------------------------------------------------------------
# Erdos 273 filler lane -- run ONE cube.  Idempotent, checkpointed, restartable.
#
#   run_cube.sh <N> <cube_id> [secs] [solver] [drat]
#     run_cube.sh 3960   c00007 3600 cadical drat
#     run_cube.sh 360360 c00042 3600 kissat
#
# A cube whose checkpoint already says SAT/UNSAT is SKIPPED: killing the lane loses at most
# the cubes currently in flight, never finished work.  This is the whole point of cubing.
# ---------------------------------------------------------------------------
set -u
FILLER="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
N="${1:?N}"; CID="${2:?cube_id}"; SECS="${3:-3600}"; SOLVER="${4:-cadical}"; DRAT="${5:-}"

CNF="$FILLER/cnf/hard-half-only-N$N.cnf"
CUBEDIR="$FILLER/cubes/N$N"
CUBE="$CUBEDIR/cube-$CID.cube"
OUT="$FILLER/out/N$N"; mkdir -p "$OUT"
CK="$OUT/$CID.json"
TMPDIR="${FILLER_TMPDIR:-/dev/shm}"
WORK="$TMPDIR/hh$N-$CID.cnf"

[ -f "$CNF"  ] || { echo "MISSING base CNF $CNF (build it: python3 $FILLER/f273_hardhalf.py --N $N)"; exit 3; }
[ -f "$CUBE" ] || { echo "MISSING cube $CUBE (split it: python3 $FILLER/f273_cube_split.py --N $N)"; exit 3; }

if [ -f "$CK" ] && grep -qE '"result": *"(SAT|UNSAT)"' "$CK"; then
  echo "SKIP $CID (already decided)"; exit 0
fi

cleanup() { rm -f "$WORK" "$WORK.partial"; }
trap cleanup EXIT

python3 "$FILLER/mkcube.py" --base "$CNF" --cube "$CUBE" --out "$WORK" >/dev/null || exit 4

LOG="$OUT/$CID.solverlog"
PROOF=""
T0=$(date +%s)
case "$SOLVER" in
  cadical)
    if [ -n "$DRAT" ]; then
      PROOF="$OUT/$CID.drat"
      cadical --no-binary -q -t "$SECS" "$WORK" "$PROOF" > "$LOG" 2>&1; RC=$?
    else
      cadical -q -t "$SECS" "$WORK" > "$LOG" 2>&1; RC=$?
    fi ;;
  kissat)
    kissat -q --time="$SECS" "$WORK" > "$LOG" 2>&1; RC=$? ;;
  *) echo "unknown solver $SOLVER"; exit 5 ;;
esac
T1=$(date +%s); EL=$((T1-T0))

case "$RC" in
  10) RES=SAT ;;
  20) RES=UNSAT ;;
  *)  RES=TIMEOUT ;;          # anything that is not 10/20 is NOT a verdict
esac

# A killed process is not a timeout.  Exit 137/143 = SIGKILL/SIGTERM: record it as such.
if [ "$RC" = 137 ] || [ "$RC" = 143 ]; then RES=STOPPED_NO_VERDICT; fi

PSHA=""; DRATV="null"
if [ -n "$PROOF" ] && [ -f "$PROOF" ]; then PSHA=$(sha256sum "$PROOF" | cut -d' ' -f1); fi

# A cadical UNSAT line is NOT a certificate.  Check the proof HERE, while $WORK still exists
# (it is base+cube, and drat-trim needs exactly those bytes).  Never after cleanup.
if [ "$RES" = UNSAT ] && [ -n "$PROOF" ] && command -v drat-trim >/dev/null 2>&1; then
  if drat-trim "$WORK" "$PROOF" > "$OUT/$CID.drattrim" 2>&1; then
    grep -q "s VERIFIED" "$OUT/$CID.drattrim" && DRATV="true" || DRATV="false"
  else
    DRATV="false"
  fi
fi
CSHA=$(sha256sum "$CUBE" | cut -d' ' -f1)

python3 - "$CK" "$N" "$CID" "$RES" "$EL" "$RC" "$SOLVER" "$LOG" "$PROOF" "$PSHA" "$CSHA" "$DRATV" <<'PY'
import json, sys, time
ck,N,cid,res,el,rc,solver,log,proof,psha,csha,dratv = sys.argv[1:13]
json.dump({"N": int(N), "cube_id": cid, "result": res, "seconds": int(el),
           "exit_code": int(rc), "solver": solver, "solverlog": log,
           "proof": proof or None, "proof_sha256": psha or None, "cube_sha256": csha,
           "drat_verified": {"true": True, "false": False}.get(dratv),
           "finished": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
           "note": ("TIMEOUT/STOPPED establishes NOTHING; only SAT (exit 10) and UNSAT "
                    "(exit 20) are verdicts. A DRAT proof is not a certificate until "
                    "drat_verified is true.")},
          open(ck,"w",encoding="utf-8"), indent=1)
PY

echo "$CID $RES ${EL}s (exit $RC) drat_verified=$DRATV"

if [ "$RES" = SAT ]; then
  echo "*** SAT ON CUBE $CID -- decoding and verifying ***"
  python3 "$FILLER/decode_cube_model.py" \
      --layout "$FILLER/cnf/hard-half-only-N$N.layout.json" \
      --model "$LOG" --cube "$CUBE" --out "$OUT/witness-$CID.json"
fi
exit 0
