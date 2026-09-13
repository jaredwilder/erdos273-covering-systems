#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Aggregate the cube checkpoints into ONE rung verdict.  Fails closed.

    python3 aggregate.py --N 3960

THE AGGREGATION RULE -- the only one this lane may use
------------------------------------------------------
The cube set is a PARTITION of the model space (see f273_cube_split.py).  Therefore:

  any cube SAT                          -> SAT_HARD_HALF.  Stage 1 of 2, NOT a witness.
                                           `decode_cube_model.py` must have validated it and
                                           stage two must then be run.
  every cube UNSAT, none missing         -> UNSAT_TO_N.  No covering system of Z with distinct
                                           moduli p-1 (p>=5) has lcm | 2N.  A BOUND with an
                                           explicit ceiling -- NEVER a refutation of Erdos 273.
  anything else (a TIMEOUT, a STOPPED,   -> INCOMPLETE.  Establishes NOTHING about the rung.
   a missing checkpoint, a cube whose       The count of undecided cubes is printed; a partial
   sha does not match the manifest)         sweep is not a partial bound.

A DRAT proof that drat-trim has not verified does not upgrade an UNSAT cube; the aggregate
reports `proofs_verified` separately from `unsat` so the two can never be conflated.
"""
from __future__ import annotations
import argparse, json, os, time

_HERE = os.path.dirname(os.path.abspath(__file__))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--N", type=int, required=True)
    ap.add_argument("--cubes", default=None)
    ap.add_argument("--out", default=None)
    a = ap.parse_args()

    cdir = a.cubes or os.path.join(_HERE, "cubes", "N%d" % a.N)
    odir = os.path.join(_HERE, "out", "N%d" % a.N)
    man = json.load(open(os.path.join(cdir, "manifest.json"), encoding="utf-8"))

    counts = {"SAT": 0, "UNSAT": 0, "TIMEOUT": 0, "STOPPED_NO_VERDICT": 0, "MISSING": 0,
              "SHA_MISMATCH": 0}
    sat_cubes, undecided, proofs_verified = [], [], 0
    for c in man["cubes"]:
        ck = os.path.join(odir, "%s.json" % c["cube_id"])
        if not os.path.exists(ck):
            counts["MISSING"] += 1
            undecided.append(c["cube_id"])
            continue
        r = json.load(open(ck, encoding="utf-8"))
        if r.get("cube_sha256") and r["cube_sha256"] != c["sha256"]:
            counts["SHA_MISMATCH"] += 1          # the checkpoint is for different bytes
            undecided.append(c["cube_id"])
            continue
        res = r.get("result", "MISSING")
        counts[res] = counts.get(res, 0) + 1
        if res == "SAT":
            sat_cubes.append(c["cube_id"])
        elif res == "UNSAT":
            if r.get("drat_verified") is True:
                proofs_verified += 1
        else:
            undecided.append(c["cube_id"])

    n = man["n_cubes"]
    if sat_cubes:
        verdict = "SAT_HARD_HALF"
        meaning = ("a distinct-moduli covering of Z from H n divisors(N) \\ {2} exists. "
                   "STAGE 1 OF 2 -- NOT an Erdos 273 witness. Run stage two "
                   "(decode_cube_model.py prints the exact command) before claiming anything.")
    elif counts["UNSAT"] == n:
        verdict = "UNSAT_TO_N"
        meaning = ("NO covering system of Z exists whose moduli are DISTINCT, all of the form "
                   "p-1 for a prime p >= 5, and all of which divide %d. A BOUND WITH AN "
                   "EXPLICIT CEILING. It is NOT and must never be reported as a refutation "
                   "of Erdos 273, which quantifies over an infinite modulus pool."
                   % (2 * a.N))
    else:
        verdict = "INCOMPLETE"
        meaning = ("%d of %d cubes undecided. A partial sweep is NOT a partial bound; this "
                   "establishes nothing about the rung." % (len(undecided), n))

    rep = {"N": a.N, "n_cubes": n, "split_moduli": man["split_moduli"],
           "base_cnf_sha256": man.get("base_cnf_sha256"),
           "counts": counts, "sat_cubes": sat_cubes,
           "undecided_count": len(undecided), "undecided": undecided[:50],
           "unsat_proofs_drat_verified": proofs_verified,
           "proofs_note": ("drat_verified counts cubes whose DRAT proof drat-trim accepted. "
                           "An UNSAT without a verified proof is still a solver claim, not a "
                           "certificate."),
           "VERDICT": verdict, "meaning": meaning,
           "evidence_class": "COMPUTED_BOUNDED",
           "aggregated": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())}
    out = a.out or os.path.join(odir, "AGGREGATE-N%d.json" % a.N)
    os.makedirs(os.path.dirname(out), exist_ok=True)
    with open(out, "w", encoding="utf-8", errors="replace") as f:
        json.dump(rep, f, indent=1)
    print(json.dumps({k: rep[k] for k in ("N", "n_cubes", "counts", "VERDICT",
                                          "undecided_count", "unsat_proofs_drat_verified")}))
    print("aggregate " + out)


if __name__ == "__main__":
    main()
