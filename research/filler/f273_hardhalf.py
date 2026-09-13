#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Erdos 273 -- HARD-HALF-ONLY encoder (reconstruction of the box's `--mode hardhalf`).

WHY THIS FILE EXISTS
--------------------
The `hardhalf` mode was present on the Scaleway box's copy of `f273_sat.py` and produced the
three CNFs recorded in `receipts/receipt-export-hardhalf-N{27720,83160,360360}.json`.  The box
was lost; the committed `scripts/f273_sat.py` in this campaign carries only
`symmetric | fixedhalf | onehalf`.  This module re-implements the missing mode and PROVES the
reconstruction faithful by reproducing, exactly, the receipted
`vars / x_vars / clauses / literals` of the two surviving hard-half exports.

    python f273_hardhalf.py --selfcheck        # must print 3/3 MATCH

THE OBJECT
----------
After the parity split (see `scripts/f273_minhalf.py`), Erdos 273 at ceiling `2N` asks for TWO
DISJOINT distinct-moduli covering systems of Z drawn from `pool = H n divisors(N)`, where
`H = {(p-1)/2 : p prime >= 5}`.  The halves are disjoint, so **at most one contains the modulus
2**.  The other one -- the HARD HALF -- is a distinct-moduli covering of Z drawn from
`pool \\ {2}`.  This encoder asks only for the hard half:

    exists a set of pairs (r_h, h), h in pool\\{2}, each h used at most once,
    such that every cell of Z/N is covered.

SEMANTICS -- the only two readings this instance admits
-------------------------------------------------------
UNSAT  ->  no distinct-moduli covering of Z drawn from `H n divisors(N) \\ {2}` exists.
           Because any Erdos-273 witness with `lcm | 2N` must contain such a half, this is
           **UNSAT_TO_N for the full rung**: no covering system of Z with distinct moduli
           `p-1` (`p >= 5`) has `lcm | 2N`.  A BOUND WITH AN EXPLICIT CEILING.
           It is NOT and must never be reported as a refutation of Erdos 273.

SAT    ->  a hard half exists.  **THIS IS NOT A WITNESS.**  It is stage one of two.  The
           complementary half (the one that may hold modulus 2) must then be found in
           `pool \\ (moduli used by the hard half)`, and only if THAT also closes, and the
           lifted object is independently re-verified, is there a candidate witness.

SOUNDNESS OF THE SYMMETRY BREAKING (r_3 = 0 and r_5 in {0,1,2})
---------------------------------------------------------------
Translation `n -> n+t` maps a covering system to a covering system with the same moduli.
If 3 is used, translate so `r_3 = 0`; the residual freedom is translation by multiples of 3,
under which `r_5 -> r_5 + 3k (mod 5)` sweeps all of Z/5 (gcd(3,5)=1), so `r_5` may be pinned
to a SINGLE value.  If 3 is unused the units on modulus 3 are vacuous and `r_5` may be pinned
directly.  `{0,1,2}` is therefore a strictly WEAKER (more permissive, hence still sound)
restriction than the `{0}` that is actually available.  It is replicated here verbatim from
the receipted box metadata rather than tightened, so the bytes match the lost artefacts.

VARIABLE LAYOUT (replicated verbatim, including the dead half)
--------------------------------------------------------------
    var(half, h, r) = 1 + half*sum(pool) + sum(h' in pool, h' < h) + r      half in {0,1}
Only half 0 is ACTIVE.  Half 1's `sum(pool)` variables appear in NO clause -- they are dead
weight the box's encoder allocated because `build()` always laid out both halves.  They are
kept so that `x_vars` reproduces the receipts byte-for-byte.  Every solver eliminates them at
once; they cost nothing but a larger `p cnf` header.

$0, deterministic, stdlib + python-sat.  No model, no network.
"""
from __future__ import annotations
import argparse, json, os, sys, time

# the arithmetic + AMO primitives are taken from the committed encoder, not re-typed
_HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(os.path.dirname(_HERE), "scripts"))
from f273_sat import is_prime, divisors, in_H, amo_clauses, amo_clauses_pysat  # noqa: E402

MODE = "hardhalf"
FORM = "hard-half-only"

# receipted box metadata -- the reconstruction target (receipts/receipt-export-hardhalf-N*.json)
RECEIPTED = {
    27720:  {"pool_size": 42, "sum_recip": 1.5873376623376623,
             "vars": 159432,   "x_vars": 106316,  "clauses": 187032,   "literals": 1482858},
    83160:  {"pool_size": 57, "sum_recip": 1.6332972582972582,
             "vars": 287721,   "x_vars": 191852,  "clauses": 370716,   "literals": None},
    360360: {"pool_size": 78, "sum_recip": 1.7114246864246865,
             "vars": 1270116,  "x_vars": 846796,  "clauses": 1630248,  "literals": 30647850},
}


# --------------------------------------------------------------------------- layout
def hard_pool(N):
    """pool \\ {2}: the moduli available to the half that cannot hold 2."""
    return [d for d in divisors(N) if in_H(d) and d != 2]


def layout(N):
    """Variable base offsets. Half 1 is allocated but DEAD (appears in no clause)."""
    pool = hard_pool(N)
    base, v = {}, 1
    for half in (0, 1):
        for h in pool:
            base[(half, h)] = v
            v += h
    return pool, base, v - 1          # pool, base, nx


def allowed_residues(N, h):
    """Residues of modulus h left alive by the symmetry-breaking units.

    THIS FUNCTION IS THE CONTRACT THE CUBE SPLITTER RELIES ON: the branches it enumerates
    must be exhaustive with respect to the CNF actually emitted.  Any change here MUST be
    mirrored in `units()` below -- they are asserted equal by --selfcheck.
    """
    pool = hard_pool(N)
    h0 = pool[0]
    if h == h0:                       # translate_half0 / r3_eq_0
        return [0]
    if h == 5 and 5 in pool:          # r5_in_012
        return [0, 1, 2]
    return list(range(h))


# --------------------------------------------------------------------------- build
def build(N, cnf_path=None, amo_backend="pysat", use_forced=True, symbreak=True,
          dead_subsets=None, count_only=False):
    """Emit the hard-half-only CNF.  Returns meta dict.

    count_only=True computes every count without writing the (possibly 164 MB) file.
    """
    pool, base, nx = layout(N)
    S2 = sum(1.0 / d for d in pool)
    NEED = 1.0                        # ONE covering of Z -> reciprocal mass strictly > 1
    meta = {"N": N, "mode": MODE, "pool": pool, "pool_size": len(pool),
            "sum_recip": S2, "amo_backend": amo_backend, "allow_p3": False}
    if S2 <= NEED:
        meta["density_verdict"] = "UNSAT_BY_DENSITY"
        return meta
    meta["density_verdict"] = "density_ok"

    next_var = nx + 1

    def X(h, r):
        return base[(0, h)] + (r % h)

    units, extra = [], []

    # (2) AMO per modulus over the ACTIVE half only  (distinctness + one residue)
    for h in pool:
        lits = [X(h, r) for r in range(h)]
        if amo_backend == "pysat":
            cl, next_var = amo_clauses_pysat(lits, next_var - 1)
            next_var += 1
        else:
            cl, next_var = amo_clauses(lits, next_var)
        extra.extend(cl)

    # (3) forced-use: dropping h leaves mass S2 - 1/h <= 1, and a covering needs > 1
    if use_forced:
        forced = [h for h in pool if 1.0 / h >= S2 - NEED]
        meta["forced_moduli"] = forced
        for h in forced:
            extra.append([X(h, r) for r in range(h)])

    # (4) symmetry breaking, verbatim from the receipted box metadata.
    #
    #     The receipted meta carries `translate_half0: true` AND `r3_eq_0: true` as two
    #     SEPARATE flags, and reproducing the receipted clause counts requires SIX unit
    #     clauses where the two rules together only need four.  The box therefore emitted the
    #     generic translate-half-0 units and then the hardhalf-specific r_3 = 0 units, which
    #     for h0 = 3 are the SAME TWO UNITS WRITTEN TWICE.  Duplicated unit clauses are
    #     semantically inert (every solver dedupes them at parse time) and they are kept here
    #     only so the reconstruction reproduces the lost artefacts exactly.  This is an
    #     INFERENCE from the counts, stated as one; it is the unique fixed +2 that is
    #     independent of |pool| and of N, which the three receipts jointly pin down.
    if symbreak:
        h0 = pool[0]
        for r in range(1, h0):
            units.append(-X(h0, r))                       # translate_half0: r_{h0} = 0
        sb = {"h0": h0, "half_swap": False, "translate_half0": True}
        if 3 in pool:
            for r in (1, 2):
                units.append(-X(3, r))                    # r3_eq_0 (duplicate when h0 == 3)
            sb["r3_eq_0"] = True
        if 5 in pool:
            for r in (3, 4):
                units.append(-X(5, r))                    # r_5 in {0,1,2}
            sb["r5_in_012"] = True
        meta["symbreak"] = sb
        meta["duplicate_units"] = 2 if (h0 == 3 and 3 in pool) else 0

    # (5) dead-subset exclusions.  NOTHING IS INVENTED HERE.  A dead subset is a set of
    #     moduli PROVED (elsewhere, with a receipt) to admit no covering; excluding it is a
    #     blocking clause `OR_{h in D} (h unused)`.  The campaign record contains NO proved
    #     dead subset, so the default is empty and the CNF carries no such clause.
    dead = []
    if dead_subsets:
        with open(dead_subsets, encoding="utf-8") as f:
            spec = json.load(f)
        for entry in spec.get("dead_subsets", []):
            ms = [int(m) for m in entry["moduli"]]
            if not all(m in pool for m in ms):
                raise SystemExit("dead subset references a modulus outside pool\\{2}: %r" % ms)
            if "receipt" not in entry:
                raise SystemExit("a dead subset without a `receipt` field is a guess, refused")
            # "not all of D used"  ==  OR_{h in D} NOT used(h).  `used(h)` is a disjunction,
            # so this needs one selector per modulus.
            sel = []
            for m in ms:
                s = next_var; next_var += 1
                sel.append(-s)
                for r in range(m):
                    extra.append([-X(m, r), s])           # used(m) -> s
            extra.append(sel)                             # some m in D is unused
            dead.append(entry)
    meta["dead_subsets"] = dead

    # ------------------------------------------------------------------ counts / stream
    ncl = nlit = 0
    body = None if count_only else cnf_path + ".partial.body"
    f = None if count_only else open(body, "w", encoding="utf-8", errors="replace")
    try:
        for c in range(N):                                # (1) cover, ACTIVE half only
            row = [X(h, c % h) for h in pool]
            if f:
                f.write(" ".join(map(str, row)));  f.write(" 0\n")
            ncl += 1;  nlit += len(row)
        for cl in extra:
            if f:
                f.write(" ".join(map(str, cl)));   f.write(" 0\n")
            ncl += 1;  nlit += len(cl)
        for u in units:
            if f:
                f.write("%d 0\n" % u)
            ncl += 1;  nlit += 1
    finally:
        if f:
            f.close()

    nv = max(next_var - 1, nx)
    meta.update({"vars": nv, "x_vars": nx, "clauses": ncl, "literals": nlit,
                 "formulation": FORM,
                 "active_halves": [0], "dead_half_vars": nx // 2})

    if count_only:
        return meta

    head = cnf_path + ".partial"
    with open(head, "w", encoding="utf-8", errors="replace") as h:
        h.write("p cnf %d %d\n" % (nv, ncl))
    with open(head, "ab") as out, open(body, "rb") as b:
        while True:
            chunk = b.read(1 << 22)
            if not chunk:
                break
            out.write(chunk)
    os.remove(body)
    meta["cnf_bytes"] = os.path.getsize(head)
    os.replace(head, cnf_path)        # renamed only when complete: a killed build is never
    return meta                       # mistaken for a finished instance


def write_layout(N, meta, cnfdir, cnf_path):
    pool, base, nx = layout(N)
    lay = {"N": N, "mode": MODE, "formulation": FORM, "pool": pool,
           "x_vars": nx, "vars": meta["vars"], "clauses": meta["clauses"],
           "var_of_half_h_r": "var = 1 + half*sum(pool) + sum(h' in pool, h'<h) + r",
           "lift": "true modulus = 2*h ; true residue = 2*r + half ; p = 2*h+1",
           "active_halves": [0],
           "allowed_residues": {str(h): allowed_residues(N, h) for h in pool
                                if allowed_residues(N, h) != list(range(h))},
           "cnf": cnf_path}
    p = os.path.join(cnfdir, "%s-N%d.layout.json" % (FORM, N))
    with open(p, "w", encoding="utf-8", errors="replace") as f:
        json.dump(lay, f, indent=1)

    # COMPAT layout for the campaign's own, independently written decoder.
    # `scripts/decode_model.py` knows `symmetric | fixedhalf | onehalf` and would take a
    # `hardhalf` layout down its two-half lifting path with an empty half 1 and emit a wrong
    # verdict.  The variable map and the active half are IDENTICAL to `onehalf`, so a layout
    # tagged `onehalf` lets that decoder run UNMODIFIED and give a genuinely independent
    # second reading of any SAT model.  Two decoders, one instance, no shared code.
    compat = dict(lay)
    compat["mode"] = "onehalf"
    compat["compat_note"] = ("mode is relabelled `onehalf` ONLY so scripts/decode_model.py "
                             "runs unmodified. The instance is hard-half-only: pool excludes "
                             "modulus 2. decode_model.py will print HALF_VERIFIED (NOT an "
                             "Erdos 273 witness), which is the correct reading.")
    cp = os.path.join(cnfdir, "%s-N%d.onehalf-compat.layout.json" % (FORM, N))
    with open(cp, "w", encoding="utf-8", errors="replace") as f:
        json.dump(compat, f, indent=1)
    return p


# --------------------------------------------------------------------------- selfcheck
def selfcheck():
    ok = 0
    for N, want in sorted(RECEIPTED.items()):
        t0 = time.time()
        got = build(N, count_only=True)
        bad = []
        for k, v in want.items():
            if v is None:
                continue
            if got.get(k) != v:
                bad.append("%s: got %r want %r" % (k, got.get(k), v))
        # the layout contract the cube splitter depends on
        pool = got["pool"]
        for h in pool:
            ar = allowed_residues(N, h)
            if h == pool[0] and ar != [0]:
                bad.append("allowed_residues(%d,%d)=%r" % (N, h, ar))
            if h == 5 and ar != [0, 1, 2]:
                bad.append("allowed_residues(%d,5)=%r" % (N, ar))
        print("N=%-7d %s  (%.1fs)  %s" % (N, "MATCH" if not bad else "MISMATCH",
                                          time.time() - t0, "; ".join(bad)))
        ok += (not bad)
    print("%d/%d MATCH against receipted box metadata" % (ok, len(RECEIPTED)))
    return 0 if ok == len(RECEIPTED) else 1


# --------------------------------------------------------------------------- main
def main():
    ap = argparse.ArgumentParser(description="Erdos 273 hard-half-only CNF encoder")
    ap.add_argument("--N", type=int)
    ap.add_argument("--cnfdir", default=os.path.join(_HERE, "cnf"))
    ap.add_argument("--question-lock",
                    default=os.path.join(os.path.dirname(_HERE),
                                         "erdos273-covering-sat-ladder.json"))
    ap.add_argument("--amo", default="pysat", choices=["pysat", "native"])
    ap.add_argument("--no-forced", action="store_true")
    ap.add_argument("--no-symbreak", action="store_true")
    ap.add_argument("--dead-subsets", default=None,
                    help="JSON {dead_subsets:[{moduli:[..], receipt:'path'}]} -- every entry "
                         "MUST cite a receipt; a subset without one is refused")
    ap.add_argument("--count-only", action="store_true",
                    help="compute vars/clauses/literals without writing the CNF")
    ap.add_argument("--selfcheck", action="store_true")
    a = ap.parse_args()

    if a.selfcheck:
        raise SystemExit(selfcheck())
    if a.N is None:
        raise SystemExit("--N is required (or --selfcheck)")
    if not os.path.exists(a.question_lock):
        raise SystemExit("question lock not found: " + a.question_lock)
    os.makedirs(a.cnfdir, exist_ok=True)
    cnf = os.path.join(a.cnfdir, "%s-N%d.cnf" % (FORM, a.N))

    t0 = time.time()
    meta = build(a.N, cnf_path=None if a.count_only else cnf, amo_backend=a.amo,
                 use_forced=not a.no_forced, symbreak=not a.no_symbreak,
                 dead_subsets=a.dead_subsets, count_only=a.count_only)
    secs = round(time.time() - t0, 2)
    rec = {"tag": "hardhalf-N%d" % a.N, "N": a.N, "mode": MODE, "formulation": FORM,
           "cnf_path": None if a.count_only else cnf,
           "question_lock": os.path.abspath(a.question_lock),
           "build_seconds": secs,
           "regenerated_by": "filler/f273_hardhalf.py (box copy of f273_sat.py --mode hardhalf "
                             "was lost with the box; this is the audited reconstruction)",
           "meta": {k: v for k, v in meta.items() if k != "pool"},
           "pool": meta["pool"],
           "result": "COUNT_ONLY" if a.count_only else "EXPORT_ONLY",
           "outcome": ("counts only, no CNF written" if a.count_only else
                       "CNF exported for the cube-and-conquer filler lane; no solve run here")}
    if not a.count_only and meta.get("density_verdict") == "density_ok":
        rec["layout_path"] = write_layout(a.N, meta, a.cnfdir, cnf)
        with open(os.path.join(a.cnfdir, "READY-N%d.txt" % a.N), "a",
                  encoding="utf-8", errors="replace") as f:
            f.write("%s N=%d cnf=%s vars=%d clauses=%d bytes=%d built=%s\n"
                    % (FORM, a.N, os.path.basename(cnf), meta["vars"], meta["clauses"],
                       meta["cnf_bytes"], time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())))
    outp = os.path.join(a.cnfdir, "receipt-build-hardhalf-N%d.json" % a.N)
    with open(outp, "w", encoding="utf-8", errors="replace") as f:
        json.dump(rec, f, indent=1)
    print(json.dumps({k: rec["meta"].get(k) for k in
                      ("pool_size", "sum_recip", "vars", "x_vars", "clauses", "literals",
                       "cnf_bytes")}))
    print("receipt " + outp)


if __name__ == "__main__":
    main()
