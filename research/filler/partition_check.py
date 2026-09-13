#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
PROVE the cube set is a PARTITION of the model space.  Without this the aggregation rule
("all cubes UNSAT => the rung is UNSAT") is an assertion, and an aggregation rule that is
merely asserted is how a partial sweep becomes a fake bound.

TWO ARMS
--------
ARM 1 -- EXHAUSTIVE, STRUCTURAL (no solver, always runs).
    For each split modulus h, enumerate EVERY assignment of h's variables that the CNF can
    admit -- at most one true (the at-most-one constraint) and true only at a residue the
    symmetry units leave alive -- and check that EXACTLY ONE branch of h matches it.
    h+1 assignments, h+1 branches, so this is a complete case check, not a sample.
    The global cube set is the product of the per-modulus branch sets, so per-modulus
    partition + product => global partition.

ARM 2 -- THE PREMISE, CHECKED AGAINST THE ACTUAL CNF (needs pysat + the built CNF).
    Arm 1 is sound only if the CNF really does forbid two residues of the same modulus.
    So: for every split modulus and EVERY pair of its residues, assume both true and require
    the solver to refute it.  If any pair survives, Arm 1's case list was incomplete and the
    aggregation rule is INVALID -- reported as a failure, never as a caveat.
    Also checks that every residue the units are supposed to have killed really is refuted.

    python partition_check.py --N 3960 --cnf cnf/hard-half-only-N3960.cnf
    python partition_check.py --N 360360            # Arm 1 only (no CNF on this PC)
"""
from __future__ import annotations
import argparse, itertools, json, os, sys, time

_HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, _HERE)
from f273_hardhalf import layout, allowed_residues  # noqa: E402


def arm1(N, moduli):
    pool, base, _ = layout(N)
    rows = []
    for h in moduli:
        allowed = allowed_residues(N, h)
        X = lambda r: base[(0, h)] + r                                     # noqa: E731
        branches = [("r=%d" % r, [X(r)]) for r in allowed]
        branches.append(("unused", [-X(r) for r in range(h)]))
        # every assignment the CNF can admit for this modulus
        cases = [set()] + [{X(r)} for r in allowed]                        # none true, or one
        bad = []
        for case in cases:
            def sat(lits):
                return all((l > 0) == (abs(l) in case) for l in lits)
            m = [tag for tag, lits in branches if sat(lits)]
            if len(m) != 1:
                bad.append({"case": sorted(case), "matched": m})
        rows.append({"h": h, "allowed_residues": allowed, "branches": len(branches),
                     "admissible_cases": len(cases), "exactly_one_match": not bad,
                     "violations": bad})
    n = 1
    for r in rows:
        n *= r["branches"]
    return {"per_modulus": rows, "n_cubes_implied": n,
            "PARTITION": all(r["exactly_one_match"] for r in rows)}


def arm2(N, moduli, cnf_path):
    from pysat.solvers import Cadical153
    pool, base, _ = layout(N)
    cls, ncl = [], None
    with open(cnf_path, encoding="utf-8") as f:
        for line in f:
            if line.startswith("c"):
                continue
            if line.startswith("p"):
                ncl = int(line.split()[3]);  continue
            lits = [int(t) for t in line.split()]
            if lits and lits[-1] == 0:
                cls.append(lits[:-1])
    if ncl != len(cls):
        return {"CNF_INTEGRITY": False, "declared": ncl, "actual": len(cls)}

    out = {"CNF_INTEGRITY": True, "clauses": len(cls), "pairs_checked": 0,
           "pairs_refuted": 0, "killed_residues_checked": 0, "killed_residues_refuted": 0,
           "failures": []}
    with Cadical153(bootstrap_with=cls) as s:
        for h in moduli:
            X = lambda r: base[(0, h)] + r                                 # noqa: E731
            for r1, r2 in itertools.combinations(range(h), 2):
                out["pairs_checked"] += 1
                if s.solve(assumptions=[X(r1), X(r2)]) is False:
                    out["pairs_refuted"] += 1
                else:
                    out["failures"].append({"h": h, "pair": [r1, r2],
                                            "why": "at-most-one does NOT hold: Arm 1's case "
                                                   "list is incomplete, aggregation INVALID"})
            for r in range(h):
                if r in allowed_residues(N, h):
                    continue
                out["killed_residues_checked"] += 1
                if s.solve(assumptions=[X(r)]) is False:
                    out["killed_residues_refuted"] += 1
                else:
                    out["failures"].append({"h": h, "residue": r,
                                            "why": "the symmetry units do not actually kill "
                                                   "this residue; allowed_residues() and the "
                                                   "emitted CNF have DRIFTED APART"})
    out["AMO_AND_UNITS_HOLD"] = not out["failures"]
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--N", type=int, required=True)
    ap.add_argument("--cnf", default=None)
    ap.add_argument("--cubes", default=None)
    ap.add_argument("--out", default=None)
    a = ap.parse_args()

    cdir = a.cubes or os.path.join(_HERE, "cubes", "N%d" % a.N)
    man = json.load(open(os.path.join(cdir, "manifest.json"), encoding="utf-8"))
    moduli = man["split_moduli"]

    t0 = time.time()
    rep = {"N": a.N, "split_moduli": moduli, "manifest_n_cubes": man["n_cubes"],
           "arm1_structural": arm1(a.N, moduli)}
    rep["cube_count_agrees"] = (rep["arm1_structural"]["n_cubes_implied"] == man["n_cubes"]
                                == len(man["cubes"]))
    if a.cnf:
        rep["arm2_against_cnf"] = arm2(a.N, moduli, a.cnf)
        rep["arm2_run"] = True
    else:
        rep["arm2_run"] = False
        rep["arm2_note"] = ("NOT RUN -- no CNF supplied. Arm 1 alone assumes the at-most-one "
                            "constraint and the symmetry units are in the file. Run Arm 2 on "
                            "the box against the real CNF before trusting an UNSAT aggregate.")
    rep["VERDICT"] = ("PARTITION_PROVED" if (rep["arm1_structural"]["PARTITION"]
                                             and rep["cube_count_agrees"]
                                             and (not a.cnf
                                                  or rep["arm2_against_cnf"].get("AMO_AND_UNITS_HOLD")))
                      else "PARTITION_NOT_PROVED")
    rep["seconds"] = round(time.time() - t0, 2)
    out = a.out or os.path.join(cdir, "partition-check.json")
    with open(out, "w", encoding="utf-8", errors="replace") as f:
        json.dump(rep, f, indent=1)
    print(json.dumps({"N": a.N, "split_moduli": moduli,
                      "arm1": rep["arm1_structural"]["PARTITION"],
                      "n_cubes_implied": rep["arm1_structural"]["n_cubes_implied"],
                      "cube_count_agrees": rep["cube_count_agrees"],
                      "arm2_run": rep["arm2_run"],
                      "arm2": (rep.get("arm2_against_cnf") or {}).get("AMO_AND_UNITS_HOLD"),
                      "VERDICT": rep["VERDICT"], "seconds": rep["seconds"]}))
    print("check " + out)
    raise SystemExit(0 if rep["VERDICT"] == "PARTITION_PROVED" else 1)


if __name__ == "__main__":
    main()
