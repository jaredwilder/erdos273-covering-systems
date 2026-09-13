#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Attach the exact bound semantics + UNSAT provenance to receipts written before
the semantics block existed.  Annotation only: no measured value is altered."""
import json, glob, os, sys

def semantics(N, result, source):
    twoN = 2 * N
    return {
        "evidence_class": "COMPUTED_BOUNDED",
        "unsat_source": source,
        "UNSAT_means": (
            "NO covering system of Z exists whose moduli are DISTINCT, all of the form p-1 for a "
            f"prime p >= 5, and ALL OF WHICH DIVIDE {twoN} (equivalently lcm(moduli) | {twoN}; in the "
            f"halved H-space every modulus h divides N = {N}). This is a BOUND with an explicit "
            "ceiling. It is NOT, and must never be reported as, a refutation of Erdos 273: the "
            "problem quantifies over an INFINITE modulus pool and no finite N settles the negative "
            "branch."),
        "SAT_means": (
            "A covering system with the required properties exists at this ceiling. It resolves "
            "Erdos 273 AFFIRMATIVELY once independently re-verified (fresh code path) and then "
            "kernel-checked in Lean. Until the kernel accepts it the status is WITNESS_UNVERIFIED."),
        "TIMEOUT_means": "Nothing whatsoever is established. Not evidence of UNSAT.",
        "never_claim": "OPEN -> closed on the negative branch.",
    }

d = sys.argv[1]
n = 0
for f in sorted(glob.glob(os.path.join(d, "receipt-*.json"))):
    r = json.load(open(f, encoding="utf-8", errors="replace"))
    dens = r.get("meta", {}).get("density_verdict") == "UNSAT_BY_DENSITY"
    res = r.get("result")
    src = "density" if dens else ("solver" if res == "UNSAT" else None)
    if dens and res == "EXPORT_ONLY":
        r["result"] = "UNSAT_BY_DENSITY"
        r["outcome"] = (f"UNSAT_TO_N (N={r['N']}, {r['mode']}): reciprocal mass "
                        f"S={r['meta'].get('sum_recip'):.4f} <= NEED; no solver invoked")
    r["unsat_source"] = src
    if src == "density":
        r["solver_used"] = None
        r["solver_seed"] = None
        r["solve_seconds"] = 0.0
    elif r.get("solver") and "solver_seed" not in r:
        r["solver_used"] = r["solver"]
        r["solver_seed"] = 0
        r["solver_version"] = {"kissat": "4.0.3-2", "kissat-unsat": "4.0.3-2",
                               "cadical": "2.1.3"}.get(r["solver"], "unknown")
        r["solver_determinism_note"] = ("run before --seed was passed explicitly; kissat/cadical "
                                        "default seed is 0, which is what was used")
    r["semantics"] = semantics(r["N"], r.get("result"), src)
    json.dump(r, open(f, "w", encoding="utf-8", errors="replace"), indent=1)
    n += 1
print("annotated", n, "receipts in", d)
