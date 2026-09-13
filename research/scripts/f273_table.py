#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Render the Erdos-273 ladder table from the receipts, with UNSAT PROVENANCE.

Every row states whether a negative came from the SOLVER (exit 20 on a real CNF)
or from DENSITY ALONE (S(N) <= 2, no solver invoked).
"""
import json, glob, os, sys

FORM = {"symmetric": "symmetric-two-halves", "fixedhalf": "fixed-selfridge-half",
        "onehalf": "single-half-control"}

d = sys.argv[1] if len(sys.argv) > 1 else "."
best = {}
for f in glob.glob(os.path.join(d, "receipt-*.json")):
    r = json.load(open(f, encoding="utf-8", errors="replace"))
    m = r.get("meta", {})
    form = r.get("formulation") or FORM.get(r.get("mode"), r.get("mode"))
    dens_dead = m.get("density_verdict") == "UNSAT_BY_DENSITY"
    res = r.get("result")
    if dens_dead:
        res, src = "UNSAT_BY_DENSITY", "density"
    elif res == "UNSAT":
        src = "solver"
    else:
        src = "—"
    if res == "EXPORT_ONLY" and not dens_dead:
        res, src = "CNF emitted, not yet solved here", "—"
    row = {"form": form, "N": r["N"], "pool": m.get("pool_size"),
           "S": m.get("sum_recip"), "vars": m.get("vars"), "cl": m.get("clauses"),
           "res": res, "src": src,
           "solve": None if dens_dead else r.get("solve_seconds"),
           "cap": None if dens_dead else r.get("secs_cap"),
           "solver": None if dens_dead else r.get("solver"),
           "ver": (r.get("verification") or {}).get("WITNESS_VALID"),
           # a genuine Erdos-273 witness requires the FULL two-half object with
           # every modulus = p-1, p >= 5.  A single half, or a p>=3 control, is NOT one.
           "is273": bool(form == "symmetric-two-halves"
                         and (r.get("verification") or {}).get("WITNESS_VALID")
                         and (r.get("verification") or {}).get("all_moduli_are_p_minus_1")
                         and (r.get("verification") or {}).get("lifted_covers_Z")),
           "tag": r.get("tag", "")}
    # a real solve beats an export stub for the same (form, N)
    rank = {"SAT": 4, "UNSAT": 3, "UNSAT_BY_DENSITY": 3, "UNKNOWN": 2}.get(res, 1)
    k = (form, r["N"])
    if k not in best or rank > best[k][0]:
        best[k] = (rank, row)

order = {"symmetric-two-halves": 0, "fixed-selfridge-half": 1,
         "single-half-control": 2, "P3-CONTROL-symmetric-two-halves": 3}
rows = sorted((v[1] for v in best.values()),
              key=lambda r: (order.get(r["form"], 9), r["N"]))

v = lambda x, f="{}": ("—" if x is None else f.format(x))
print("| formulation | N | \\|pool\\| | Σ1/h | vars | clauses | solver | result | UNSAT from | solve s | cap s |")
print("|---|---|---|---|---|---|---|---|---|---|---|")
for r in rows:
    print(f"| `{r['form']}` | {r['N']:,} | {v(r['pool'])} | {v(r['S'],'{:.4f}')} | "
          f"{v(r['vars'],'{:,}')} | {v(r['cl'],'{:,}')} | {v(r['solver'])} | "
          f"**{r['res']}** | {r['src']} | {v(r['solve'],'{:.1f}')} | {v(r['cap'])} |")

print()
sats = [r for r in rows if r["res"] == "SAT"]
for r in sats:
    tag = ("*** ERDOS 273 WITNESS ***" if r["is273"]
           else "CONTROL ONLY - NOT an Erdos 273 witness")
    print(f"SAT: {r['form']} N={r['N']} -> {tag}")
print()
print("counts:",
      {k: sum(1 for r in rows if r["res"] == k) for k in
       sorted(set(r["res"] for r in rows))})
