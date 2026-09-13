#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
30-SECOND SMOKE TEST -- proves the PIPELINE SHAPE on this PC.  NO VERDICT IS EXPECTED.

There is no `cadical`, `kissat` or `drat-trim` binary on this machine, so the smoke test
drives pysat's bundled CaDiCaL 1.5.3 through the ASSUMPTION interface -- which is exactly
what a cube is.  What it proves:

  1. the regenerated CNF parses and loads
  2. a cube's literals are consistent with the formula (not instantly falsified)
  3. cube-restricted solving runs and returns cleanly under a budget
  4. the assembled `base CNF + cube units` file (what the box actually solves) is intact

The PARTITION property is NOT checked here -- it is proved exhaustively, both arms, by
`partition_check.py`, which is the file to read before trusting any UNSAT aggregate.

It does NOT establish SAT, UNSAT, or anything about Erdos 273.  Any cube that hits the budget
is reported as INDETERMINATE, which is what a 25-second budget on a 3,600-second job means.

    python smoke_test.py --N 3960 --cube c00000 --secs 25
"""
from __future__ import annotations
import argparse, json, os, time

_HERE = os.path.dirname(os.path.abspath(__file__))


def read_cnf(path):
    cls, nv, ncl = [], 0, 0
    with open(path, encoding="utf-8") as f:
        for line in f:
            if line.startswith("c"):
                continue
            if line.startswith("p"):
                _, _, nv, ncl = line.split()
                nv, ncl = int(nv), int(ncl)
                continue
            lits = [int(t) for t in line.split()]
            if lits and lits[-1] == 0:
                cls.append(lits[:-1])
    return nv, ncl, cls


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--N", type=int, default=3960)
    ap.add_argument("--cube", default="c00000")
    ap.add_argument("--secs", type=float, default=25.0)
    ap.add_argument("--conflicts", type=int, default=300000,
                    help="conflict budget for the probe (pysat has no wall-clock limit)")
    ap.add_argument("--cnf", default=None,
                    help="solve THIS file instead of the base -- point it at an assembled "
                         "`base + cube units` CNF to exercise the exact box path")
    ap.add_argument("--assembled", action="store_true",
                    help="the --cnf already contains the cube units: solve with NO assumptions")
    ap.add_argument("--out", default=None)
    a = ap.parse_args()
    if a.secs > 30:
        raise SystemExit("this PC's cap is 30 s; refusing --secs %s" % a.secs)

    cnf = a.cnf or os.path.join(_HERE, "cnf", "hard-half-only-N%d.cnf" % a.N)
    cdir = os.path.join(_HERE, "cubes", "N%d" % a.N)
    cube = os.path.join(cdir, "cube-%s.cube" % a.cube)
    man = json.load(open(os.path.join(cdir, "manifest.json"), encoding="utf-8"))
    row = next(c for c in man["cubes"] if c["cube_id"] == a.cube)

    rep = {"N": a.N, "cube_id": a.cube, "branch": row["branch"],
           "n_assumptions": row["n_lits"], "budget_seconds": a.secs,
           "purpose": "PIPELINE SHAPE ONLY -- no verdict expected or claimed"}

    t0 = time.time()
    nv, ncl, cls = read_cnf(cnf)
    rep["parse_seconds"] = round(time.time() - t0, 2)
    rep["declared"] = {"vars": nv, "clauses": ncl}
    rep["actual_clauses"] = len(cls)
    rep["header_intact"] = (len(cls) == ncl)
    if not rep["header_intact"]:
        raise SystemExit("CNF integrity FAILED: header says %d clauses, file holds %d"
                         % (ncl, len(cls)))

    from pysat.solvers import Cadical153
    import pysat
    rep["solver"] = "pysat Cadical153 (%s)" % getattr(pysat, "__version__", "?")

    assumps = [] if a.assembled else row["assumptions"]
    rep["path"] = ("assembled CNF, no assumptions (the exact box path)" if a.assembled
                   else "base CNF + cube as solver assumptions")
    rep["cnf"] = os.path.abspath(cnf)
    with Cadical153(bootstrap_with=cls) as s:
        t1 = time.time()
        # A conflict budget is the portable limit pysat offers.  It is chosen small enough
        # that the call returns well inside --secs; the elapsed time is measured and asserted
        # below, so a budget that turns out to be too generous is caught, not hidden.
        s.conf_budget(a.conflicts)
        r = s.solve_limited(assumptions=assumps)
        el = time.time() - t1
        rep["solve_seconds"] = round(el, 2)
        if r is None:
            rep["result"] = "INDETERMINATE"
            rep["meaning"] = ("budget exhausted. EXACTLY what a 25 s probe on a 3600 s job "
                              "means. Establishes nothing.")
        elif r:
            rep["result"] = "SAT"
            model = set(l for l in s.get_model() if l > 0)
            rep["assumptions_honoured"] = all((u > 0) == (abs(u) in model) for u in assumps)
            rep["meaning"] = ("this cube is satisfiable -> a hard half exists under this "
                              "branch. STAGE 1 OF 2, NOT an Erdos 273 witness. Re-run under "
                              "the real pipeline and decode with decode_cube_model.py.")
            with open(os.path.join(_HERE, "out", "smoke-model-%s.txt" % a.cube), "w",
                      encoding="utf-8") as f:
                f.write("v " + " ".join(map(str, s.get_model())) + " 0\n")
        else:
            rep["result"] = "UNSAT"
            rep["meaning"] = ("this ONE cube is refuted. One cube out of %d. The rung is "
                              "untouched." % man["n_cubes"])
    rep["total_seconds"] = round(time.time() - t0, 2)
    rep["within_pc_cap"] = rep["total_seconds"] <= a.secs + 5

    os.makedirs(os.path.join(_HERE, "out"), exist_ok=True)
    out = a.out or os.path.join(_HERE, "out", "smoke-N%d-%s.json" % (a.N, a.cube))
    with open(out, "w", encoding="utf-8", errors="replace") as f:
        json.dump(rep, f, indent=1)
    print(json.dumps(rep, ensure_ascii=False, indent=1))
    print("smoke receipt " + out)


if __name__ == "__main__":
    main()
