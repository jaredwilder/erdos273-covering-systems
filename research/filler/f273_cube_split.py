#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Erdos 273 -- DETERMINISTIC CUBE SPLITTER for the hard-half-only instances.

WHAT A CUBE IS HERE
-------------------
The hard half is a set of pairs (r_h, h), h in pool\\{2}, each modulus used AT MOST ONCE.
So for every modulus h the encoded formula admits exactly `|allowed(h)| + 1` mutually
exclusive, jointly exhaustive states:

    h is used at residue r,  for each r in allowed(h)          <- one positive literal x[h][r]
    h is unused                                                 <- all h literals of h negated

`allowed(h)` is imported from the ENCODER (`f273_hardhalf.allowed_residues`), never re-derived,
so a branch set can never drift away from the symmetry units actually in the CNF.

Disjointness is given by the at-most-one constraint on h; exhaustiveness is given by the case
split above.  Therefore:

    ALL cubes UNSAT  =>  the base instance is UNSAT
    ANY cube SAT     =>  the base instance is SAT (that cube's model is a model of the base)

**The split is a partition, so the aggregation is sound in both directions.**  This is the
whole reason a cube lane can be killed and restarted at will: a lost cube costs one cube.

MODULUS SELECTION (deterministic, no search, no tuning knob that changes the answer)
------------------------------------------------------------------------------------
Branching on the SMALLEST moduli is what prunes: a class of modulus h covers N/h cells of
Z/N, so small h are the decision-critical ones, and their branch factor h+1 is small.  Over
the K smallest moduli of pool\\{2} the splitter enumerates every subset and picks:

    1. the largest CARDINALITY whose cube count lands in [min_cubes, max_cubes]
    2. tie-break: the lexicographically smallest ascending tuple  (= prefer the smallest,
       most-constraining moduli)
    3. if no subset lands in the window at all: the subset with the largest cube count <=
       max_cubes, and the shortfall is REPORTED, never silently accepted

The chosen set and the resulting count are written into the manifest, so the split is
reproducible from the manifest alone.

OUTPUT
------
    cubes/N<N>/cube-<id>.cube      DIMACS unit clauses -- concatenate onto the base CNF
    cubes/N<N>/manifest.json       {cube_id, branch, assumptions, sha256} per cube + base sha
    cubes/N<N>/cubes.jsonl         one row per cube, what the box runner iterates
    cubes/N<N>/cubes.icnf          OPTIONAL (--icnf): `p inccnf` + base clauses + `a` lines

$0, deterministic, stdlib only.
"""
from __future__ import annotations
import argparse, hashlib, itertools, json, os, sys, time

_HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, _HERE)
from f273_hardhalf import hard_pool, layout, allowed_residues, FORM  # noqa: E402


def sha256_file(path, chunk=1 << 22):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        while True:
            b = f.read(chunk)
            if not b:
                break
            h.update(b)
    return h.hexdigest()


# --------------------------------------------------------------------- selection
def branch_factor(N, h):
    return len(allowed_residues(N, h)) + 1          # +1 for "h unused"


def select_moduli(N, min_cubes, max_cubes, k_pool=8):
    pool = hard_pool(N)
    cand = pool[:k_pool]
    best_in, best_any = None, None
    for card in range(1, len(cand) + 1):
        for sub in itertools.combinations(cand, card):       # ascending, lexicographic
            p = 1
            for h in sub:
                p *= branch_factor(N, h)
            if p <= max_cubes and (best_any is None or p > best_any[1]):
                best_any = (sub, p)
            if min_cubes <= p <= max_cubes:
                if best_in is None or card > len(best_in[0]):
                    best_in = (sub, p)                        # card 1 tie-break: first found
                                                              # = lexicographically smallest
    if best_in is not None:
        return list(best_in[0]), best_in[1], "in_window"
    if best_any is None:
        raise SystemExit("no subset of the %d smallest moduli fits under max_cubes=%d"
                         % (k_pool, max_cubes))
    return list(best_any[0]), best_any[1], "below_window_min"


# --------------------------------------------------------------------- cubes
def enumerate_cubes(N, moduli):
    """Every branch of every chosen modulus, crossed.  A partition of the model space."""
    pool, base, _ = layout(N)

    def X(h, r):
        return base[(0, h)] + r

    per = []
    for h in moduli:
        opts = [(r, [X(h, r)]) for r in allowed_residues(N, h)]
        opts.append(("unused", [-X(h, r) for r in range(h)]))
        per.append((h, opts))

    for combo in itertools.product(*[o for _, o in per]):
        branch, lits = {}, []
        for (h, _), (tag, ls) in zip(per, combo):
            branch[str(h)] = tag
            lits.extend(ls)
        yield branch, lits


def main():
    ap = argparse.ArgumentParser(description="deterministic cube splitter, Erdos 273 hard half")
    ap.add_argument("--N", type=int, required=True)
    ap.add_argument("--cnf", default=None, help="base CNF (for the sha + a sanity check); "
                                                "optional -- cubes derive from the pool alone")
    ap.add_argument("--outdir", default=os.path.join(_HERE, "cubes"))
    ap.add_argument("--min-cubes", type=int, default=None)
    ap.add_argument("--max-cubes", type=int, default=None)
    ap.add_argument("--moduli", default=None, help="explicit comma-separated split moduli, "
                                                   "bypasses the selector")
    ap.add_argument("--icnf", action="store_true",
                    help="also write a single `p inccnf` file (base clauses + one `a` line per "
                         "cube).  Requires --cnf.  Duplicates the base CNF -- do not use at "
                         "N=360360 unless you want a second 164 MB file.")
    a = ap.parse_args()

    # defaults follow the box plan: 64-256 cubes at the cheap rung, 512-4096 at the ceiling
    mn = a.min_cubes if a.min_cubes is not None else (512 if a.N >= 100000 else 64)
    mx = a.max_cubes if a.max_cubes is not None else (4096 if a.N >= 100000 else 256)

    t0 = time.time()
    pool, base, nx = layout(a.N)
    if a.moduli:
        moduli = [int(x) for x in a.moduli.split(",")]
        bad = [h for h in moduli if h not in pool]
        if bad:
            raise SystemExit("moduli not in pool\\{2} for N=%d: %r" % (a.N, bad))
        n_cubes = 1
        for h in moduli:
            n_cubes *= branch_factor(a.N, h)
        fit = "explicit"
    else:
        moduli, n_cubes, fit = select_moduli(a.N, mn, mx)

    d = os.path.join(a.outdir, "N%d" % a.N)
    os.makedirs(d, exist_ok=True)

    man = {"N": a.N, "formulation": FORM,
           "generated": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
           "generator": "filler/f273_cube_split.py",
           "base_cnf": os.path.abspath(a.cnf) if a.cnf else None,
           "base_cnf_sha256": sha256_file(a.cnf) if a.cnf else None,
           "base_vars": None, "base_clauses": None,
           "pool_size": len(pool), "pool": pool,
           "split_moduli": moduli,
           "branch_factors": {str(h): branch_factor(a.N, h) for h in moduli},
           "allowed_residues": {str(h): allowed_residues(a.N, h) for h in moduli},
           "n_cubes": n_cubes, "window": [mn, mx], "window_fit": fit,
           "partition_claim": ("the split is a PARTITION of the model space: branches of one "
                               "modulus are pairwise exclusive by the at-most-one constraint "
                               "and jointly exhaustive by the used/unused case split, so ALL "
                               "cubes UNSAT => base UNSAT, and ANY cube SAT => base SAT"),
           "cubes": []}
    if a.cnf:
        with open(a.cnf, encoding="utf-8") as f:
            hdr = f.readline().split()
        man["base_vars"], man["base_clauses"] = int(hdr[2]), int(hdr[3])
        top = max(abs(l) for _, ls in [next(enumerate_cubes(a.N, moduli))] for l in ls)
        if top > man["base_vars"]:
            raise SystemExit("cube literal %d exceeds the base CNF's variable count %d -- the "
                             "cube manifest and the CNF are not the same instance" % (top, man["base_vars"]))

    idx = []
    jl = open(os.path.join(d, "cubes.jsonl"), "w", encoding="utf-8")
    for i, (branch, lits) in enumerate(enumerate_cubes(a.N, moduli)):
        cid = "c%05d" % i
        fn = os.path.join(d, "cube-%s.cube" % cid)
        txt = "".join("%d 0\n" % l for l in lits)
        with open(fn, "w", encoding="utf-8") as f:
            f.write(txt)
        row = {"cube_id": cid, "file": os.path.basename(fn), "branch": branch,
               "assumptions": lits, "n_lits": len(lits),
               "sha256": hashlib.sha256(txt.encode("utf-8")).hexdigest()}
        man["cubes"].append(row)
        jl.write(json.dumps(row) + "\n")
        idx.append(os.path.basename(fn))
    jl.close()
    if len(man["cubes"]) != n_cubes:
        raise SystemExit("cube count mismatch: emitted %d, predicted %d"
                         % (len(man["cubes"]), n_cubes))

    with open(os.path.join(d, "index.txt"), "w", encoding="utf-8") as f:
        f.write("\n".join(idx) + "\n")
    with open(os.path.join(d, "manifest.json"), "w", encoding="utf-8") as f:
        json.dump(man, f, indent=1)

    if a.icnf:
        if not a.cnf:
            raise SystemExit("--icnf needs --cnf")
        p = os.path.join(d, "cubes.icnf")
        with open(p, "w", encoding="utf-8") as out, open(a.cnf, encoding="utf-8") as src:
            src.readline()
            out.write("p inccnf\n")
            for line in src:
                out.write(line)
            for row in man["cubes"]:
                out.write("a " + " ".join(map(str, row["assumptions"])) + " 0\n")
        man["icnf"] = p

    print(json.dumps({"N": a.N, "split_moduli": moduli, "n_cubes": n_cubes,
                      "window": [mn, mx], "window_fit": fit,
                      "max_cube_lits": max(c["n_lits"] for c in man["cubes"]),
                      "dir": d, "seconds": round(time.time() - t0, 2)}))


if __name__ == "__main__":
    main()
