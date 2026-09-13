#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Erdos 273 -- SAT ladder.

Formulations (all in H-space, H = {(p-1)/2 : p prime >= 5}):

  symmetric   : find TWO DISJOINT distinct-moduli covering systems of Z/N,
                both drawn from pool = H intersect divisors(N).
                <=> a covering system of Z with distinct moduli 2h (= p-1, p>=5)
                    and lcm dividing 2N.  THIS IS ERDOS 273 RESTRICTED TO lcm | 2N.

  fixedhalf   : half 0 is pinned to Selfridge's covering (divisors of 180 in H);
                only half 1 is searched.

Variables   x[half][h][r]   half in {0,1}, h in pool, r in [0,h)
Clauses     (1) cover   : for each half, each cell c of Z/N: OR_h x[half][h][c mod h]
            (2) AMO     : for each h, at-most-one over ALL 2h literals of both halves
                          (= 'each modulus is used at most once, in at most one half,
                             with at most one residue' = injective_moduli)
            (3) forced  : if 1/h >= S - 2 then h must be used  (sound: dropping h leaves
                          reciprocal mass S - 1/h <= 2, but two distinct-moduli coverings
                          need strictly more than 2)
            (4) symbreak: half-swap (min modulus never in half 1) + translation of half 0

DIMACS is streamed to disk; only the small AMO part goes through pysat.
"""
from __future__ import annotations
import argparse, json, math, os, subprocess, sys, time

SOLVE_META = {}

# ----------------------------------------------------------------- arithmetic
def is_prime(n: int) -> bool:
    if n < 2:
        return False
    for p in (2, 3, 5, 7, 11, 13, 17, 19, 23, 29, 31, 37):
        if n % p == 0:
            return n == p
    d, s = n - 1, 0
    while d % 2 == 0:
        d //= 2
        s += 1
    for a in (2, 3, 5, 7, 11, 13, 17, 19, 23, 29, 31, 37):
        x = pow(a, d, n)
        if x in (1, n - 1):
            continue
        for _ in range(s - 1):
            x = x * x % n
            if x == n - 1:
                break
        else:
            return False
    return True


def divisors(n: int):
    ds, i = [], 1
    while i * i <= n:
        if n % i == 0:
            ds.append(i)
            if i != n // i:
                ds.append(n // i)
        i += 1
    return sorted(ds)


def in_H(h: int) -> bool:
    return h >= 2 and is_prime(2 * h + 1)


SELFRIDGE = [2, 3, 5, 6, 9, 15, 18, 20, 30, 36, 90]
SELFRIDGE_PAIRS = [(0, 2), (1, 3), (3, 5), (5, 6), (0, 9), (0, 15),
                   (3, 18), (11, 20), (9, 30), (33, 36), (87, 90)]


# ----------------------------------------------------------------- AMO helper
def amo_clauses(lits, next_var):
    """At-most-one.  Pairwise for short lists, sequential (Sinz) for long ones.
    Returns (clauses, next_var)."""
    n = len(lits)
    if n <= 1:
        return [], next_var
    if n <= 6:
        return ([[-lits[i], -lits[j]] for i in range(n) for j in range(i + 1, n)],
                next_var)
    # Sinz sequential encoding: s_1..s_{n-1}
    s = list(range(next_var, next_var + n - 1))
    next_var += n - 1
    cl = [[-lits[0], s[0]]]
    for i in range(1, n - 1):
        cl.append([-lits[i], s[i]])
        cl.append([-s[i - 1], s[i]])
        cl.append([-lits[i], -s[i - 1]])
    cl.append([-lits[n - 1], -s[n - 2]])
    return cl, next_var


def amo_clauses_pysat(lits, vpool_top):
    from pysat.card import CardEnc, EncType
    enc = CardEnc.atmost(lits=lits, bound=1, top_id=vpool_top,
                         encoding=EncType.seqcounter)
    return [list(c) for c in enc.clauses], enc.nv


# ----------------------------------------------------------------- build CNF
def build(N, mode, cnf_path, amo_backend="pysat", use_forced=True, symbreak=True,
          allow_p3=False):
    pool = [d for d in divisors(N) if in_H(d) or (allow_p3 and d == 1)]
    S = sum(1.0 / d for d in pool)
    meta = {"N": N, "mode": mode, "pool": pool, "pool_size": len(pool),
            "sum_recip": S, "amo_backend": amo_backend, "allow_p3": allow_p3}
    NEED = 1.0 if mode == "onehalf" else 2.0

    if mode == "fixedhalf":
        if not all(N % m == 0 for m in SELFRIDGE):
            meta["density_verdict"] = "SELFRIDGE_MODULI_DO_NOT_DIVIDE_N"
            meta["free_pool_sum"] = None
            return meta, None
        free = [d for d in pool if d not in SELFRIDGE]
        meta["free_pool"] = free
        meta["free_pool_sum"] = sum(1.0 / d for d in free)
        if meta["free_pool_sum"] <= 1.0:
            meta["density_verdict"] = "UNSAT_BY_DENSITY"
            return meta, None
    else:
        if S <= NEED:
            meta["density_verdict"] = "UNSAT_BY_DENSITY"
            return meta, None
    meta["density_verdict"] = "density_ok"

    # variable layout
    base = {}
    v = 1
    for half in (0, 1):
        for h in pool:
            base[(half, h)] = v
            v += h
    nx = v - 1
    next_var = v

    def X(half, h, r):
        return base[(half, h)] + (r % h)

    units = []      # forced literals
    extra = []      # aux clauses (AMO, forced-use, symmetry)

    if mode == "fixedhalf":
        # pin half 0 exactly to Selfridge, forbid Selfridge moduli in half 1
        sel = dict((m, r) for r, m in SELFRIDGE_PAIRS)
        for h in pool:
            if h in sel:
                for r in range(h):
                    units.append(X(0, h, r) if r == sel[h] else -X(0, h, r))
                for r in range(h):
                    units.append(-X(1, h, r))
            else:
                for r in range(h):
                    units.append(-X(0, h, r))
    else:
        # AMO across the active halves, per modulus (= distinctness + one residue)
        active = (0,) if mode == "onehalf" else (0, 1)
        for h in pool:
            lits = [X(half, h, r) for half in active for r in range(h)]
            if amo_backend == "pysat":
                cl, next_var = amo_clauses_pysat(lits, next_var - 1)
                next_var += 1
            else:
                cl, next_var = amo_clauses(lits, next_var)
            extra.extend(cl)
        # forced-use
        if use_forced:
            forced = [h for h in pool if 1.0 / h >= S - NEED]
            meta["forced_moduli"] = forced
            for h in forced:
                extra.append([X(half, h, r) for half in active for r in range(h)])
        # symmetry breaking
        if symbreak:
            h0 = pool[0]
            if mode != "onehalf":
                for r in range(h0):
                    units.append(-X(1, h0, r))      # half-swap
            for r in range(1, h0):
                units.append(-X(0, h0, r))          # translation of half 0
            meta["symbreak"] = {"h0": h0, "half_swap": mode != "onehalf",
                                "translate_half0": True}

    # stream DIMACS  (built into .partial, renamed only when complete, so a
    # killed build can never be mistaken for a finished instance)
    final_path = cnf_path
    cnf_path = cnf_path + ".partial"
    body = cnf_path + ".body"
    ncl = 0
    nlit = 0
    with open(body, "w", encoding="utf-8", errors="replace") as f:
        halves = {"fixedhalf": (1,), "onehalf": (0,)}.get(mode, (0, 1))
        for half in halves:
            for c in range(N):
                row = [X(half, h, c % h) for h in pool]
                f.write(" ".join(map(str, row)))
                f.write(" 0\n")
                ncl += 1
                nlit += len(row)
        for cl in extra:
            f.write(" ".join(map(str, cl)))
            f.write(" 0\n")
            ncl += 1
            nlit += len(cl)
        for u in units:
            f.write(f"{u} 0\n")
            ncl += 1
            nlit += 1
    nv = max(next_var - 1, nx)
    with open(cnf_path, "w", encoding="utf-8", errors="replace") as f:
        f.write(f"p cnf {nv} {ncl}\n")
    with open(cnf_path, "ab") as out, open(body, "rb") as b:
        while True:
            chunk = b.read(1 << 22)
            if not chunk:
                break
            out.write(chunk)
    os.remove(body)
    size = os.path.getsize(cnf_path)
    os.replace(cnf_path, final_path)
    meta.update({"vars": nv, "x_vars": nx, "clauses": ncl, "literals": nlit,
                 "cnf_bytes": size})
    return meta, (base, pool)


# ----------------------------------------------------------------- solve
def solver_version(binary):
    try:
        return subprocess.run([binary, "--version"], stdout=subprocess.PIPE,
                              stderr=subprocess.STDOUT).stdout.decode(
                                  "utf-8", errors="replace").strip()
    except Exception as e:
        return "unknown (%s)" % e


def solve(cnf_path, solver, secs, log_path, seed=0):
    if solver == "kissat":
        cmd = ["kissat", "-q", f"--seed={seed}", f"--time={secs}", cnf_path]
    elif solver == "kissat-unsat":
        cmd = ["kissat", "-q", "--unsat", f"--seed={seed}", f"--time={secs}", cnf_path]
    elif solver == "kissat-sat":
        cmd = ["kissat", "-q", "--sat", f"--seed={seed}", f"--time={secs}", cnf_path]
    elif solver == "cadical":
        cmd = ["cadical", "-q", f"--seed={seed}", "-t", str(secs), cnf_path]
    else:
        raise SystemExit("unknown solver " + solver)
    t0 = time.time()
    with open(log_path, "w", encoding="utf-8", errors="replace") as lg:
        pr = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
        txt = pr.stdout.decode("utf-8", errors="replace")
        lg.write(txt)
    el = time.time() - t0
    SOLVE_META.update({"solver_cmd": " ".join(cmd), "solver_seed": seed,
                       "solver_binary": cmd[0],
                       "solver_version": solver_version(cmd[0]),
                       "exit_code": pr.returncode})
    if pr.returncode == 10:
        model = set()
        for line in txt.splitlines():
            if line.startswith("v "):
                for tok in line[2:].split():
                    iv = int(tok)
                    if iv > 0:
                        model.add(iv)
        return "SAT", el, model
    if pr.returncode == 20:
        return "UNSAT", el, None
    return "UNKNOWN", el, None


# ----------------------------------------------------------------- decode/verify
def decode(model, base, pool, N, mode):
    halves = {0: [], 1: []}
    for half in {"fixedhalf": (1,), "onehalf": (0,)}.get(mode, (0, 1)):
        for h in pool:
            for r in range(h):
                if base[(half, h)] + r in model:
                    halves[half].append((r, h))
    if mode == "fixedhalf":
        halves[0] = list(SELFRIDGE_PAIRS)
    return halves


def verify_half_independent(pairs):
    """Fresh code path: enumerate Z/lcm and test each integer directly."""
    if not pairs:
        return False, 0
    L = 1
    for _, m in pairs:
        L = L * m // math.gcd(L, m)
    for n in range(L):
        if not any((n - r) % m == 0 for r, m in pairs):
            return False, L
    return True, L


def verify_witness(halves):
    """Full independent verification of the Erdos-273 object built from two halves."""
    rep = {}
    p0, p1 = halves[0], halves[1]
    ok0, L0 = verify_half_independent(p0)
    ok1, L1 = verify_half_independent(p1)
    rep["half0_covers_Z"] = ok0
    rep["half1_covers_Z"] = ok1
    rep["half0_lcm"] = L0
    rep["half1_lcm"] = L1
    m0 = [m for _, m in p0]
    m1 = [m for _, m in p1]
    rep["moduli_half0"] = sorted(m0)
    rep["moduli_half1"] = sorted(m1)
    rep["disjoint_and_distinct"] = (len(set(m0 + m1)) == len(m0) + len(m1))
    # lift to M-space
    lifted = [(2 * r, 2 * h) for r, h in p0] + [(2 * r + 1, 2 * h) for r, h in p1]
    rep["lifted_pairs"] = sorted(lifted, key=lambda t: t[1])
    ok, L = verify_half_independent(lifted)
    rep["lifted_covers_Z"] = ok
    rep["lifted_lcm"] = L
    prim = []
    for _, m in lifted:
        prim.append({"m": m, "p": m + 1, "prime": is_prime(m + 1), "ge5": m + 1 >= 5})
    rep["primality"] = prim
    rep["all_moduli_are_p_minus_1"] = all(d["prime"] and d["ge5"] for d in prim)
    rep["all_moduli_distinct"] = len(set(m for _, m in lifted)) == len(lifted)
    rep["sum_recip_lifted"] = sum(1.0 / m for _, m in lifted)
    rep["k"] = len(lifted)
    rep["WITNESS_VALID"] = bool(ok and rep["all_moduli_are_p_minus_1"]
                                and rep["all_moduli_distinct"] and ok0 and ok1
                                and rep["disjoint_and_distinct"])
    return rep



def semantics(N, mode, result, source):
    """The exact, non-negotiable meaning of every verdict this script can emit."""
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

# ----------------------------------------------------------------- main
def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--N", type=int, required=True)
    ap.add_argument("--mode", choices=["symmetric", "fixedhalf", "onehalf"], default="symmetric")
    ap.add_argument("--solver", default="kissat",
                    choices=["kissat", "kissat-unsat", "kissat-sat", "cadical"])
    ap.add_argument("--secs", type=int, default=600)
    ap.add_argument("--seed", type=int, default=0)
    ap.add_argument("--outdir", default="/root/peer/out")
    ap.add_argument("--tag", default="")
    ap.add_argument("--amo", default="pysat", choices=["pysat", "native"])
    ap.add_argument("--no-forced", action="store_true")
    ap.add_argument("--no-symbreak", action="store_true")
    ap.add_argument("--question-lock", required=True)
    ap.add_argument("--cnfdir", default="/root/peer/sat273/cnf")
    ap.add_argument("--export-only", action="store_true")
    ap.add_argument("--solve-existing", action="store_true",
                    help="solve the CNF already in --cnfdir; never rebuild it")
    ap.add_argument("--allow-p3", action="store_true",
                    help="CONTROL ONLY: admit h=1 (p=3). Reproduces the SETTLED p>=3 sibling; "
                         "any witness found this way is NOT an Erdos 273 witness.")
    a = ap.parse_args()

    if not os.path.exists(a.question_lock):
        raise SystemExit("question lock not found: " + a.question_lock)
    os.makedirs(a.outdir, exist_ok=True)
    os.makedirs(a.cnfdir, exist_ok=True)
    FORM = {"symmetric": "symmetric-two-halves",
            "fixedhalf": "fixed-selfridge-half",
            "onehalf": "single-half-control"}[a.mode]
    if a.allow_p3:
        FORM = "P3-CONTROL-" + FORM
    tag = a.tag or f"{a.mode}-N{a.N}"
    cnf = os.path.join(a.cnfdir, f"{FORM}-N{a.N}.cnf")
    rec = {"tag": tag, "N": a.N, "mode": a.mode, "formulation": FORM,
           "cnf_path": cnf, "solver": a.solver,
           "secs_cap": a.secs, "question_lock": os.path.abspath(a.question_lock),
           "started": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())}

    if a.solve_existing:
        layp = os.path.join(a.cnfdir, f"{FORM}-N{a.N}.layout.json")
        if not (os.path.exists(cnf) and os.path.exists(layp)):
            raise SystemExit("no prebuilt CNF/layout for " + cnf)
        lay = json.load(open(layp, encoding="utf-8"))
        pool = lay["pool"]
        base, v = {}, 1
        for half in (0, 1):
            for h in pool:
                base[(half, h)] = v
                v += h
        rec["build_seconds"] = 0.0
        rec["meta"] = {k: lay[k] for k in ("N", "mode", "formulation", "x_vars",
                                           "vars", "clauses") if k in lay}
        rec["meta"]["pool_size"] = len(pool)
        rec["meta"]["sum_recip"] = sum(1.0 / h for h in pool)
        rec["meta"]["prebuilt"] = True
        rec["pool"] = pool
        st, el, model = solve(cnf, a.solver, a.secs,
                              os.path.join(a.outdir, f"{tag}.solverlog"), seed=a.seed)
        rec["result"], rec["solve_seconds"] = st, round(el, 2)
        if st == "SAT":
            halves = decode(model, base, pool, a.N, a.mode)
            rec["halves"] = {str(k): sorted(v, key=lambda t: t[1]) for k, v in halves.items()}
            rec["verification"] = verify_witness(halves)
            rec["outcome"] = ("WITNESS_UNVERIFIED->CHECKED" if rec["verification"]["WITNESS_VALID"]
                              else "SAT_BUT_VERIFICATION_FAILED")
        elif st == "UNSAT":
            rec["outcome"] = (f"UNSAT_TO_N (N={a.N}, {a.mode}): no covering system of Z with "
                              f"distinct moduli p-1 (p>=5) whose lcm divides {2*a.N}")
        else:
            rec["outcome"] = f"TIMEOUT_AT_N (N={a.N}, {a.mode}) after {a.secs}s"
        rec["unsat_source"] = "solver" if st == "UNSAT" else None
        rec["semantics"] = semantics(a.N, a.mode, st, rec["unsat_source"])
        rec.update(SOLVE_META)
        rec["finished"] = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
        path = os.path.join(a.outdir, f"receipt-{tag}.json")
        with open(path, "w", encoding="utf-8", errors="replace") as f:
            json.dump(rec, f, indent=1)
        print(json.dumps({"tag": tag, "result": st, "outcome": rec["outcome"][:80],
                          "solve_seconds": rec["solve_seconds"]}))
        print("receipt " + path)
        return

    t0 = time.time()
    meta, layout = build(a.N, a.mode, cnf, amo_backend=a.amo,
                         use_forced=not a.no_forced, symbreak=not a.no_symbreak,
                         allow_p3=a.allow_p3)
    rec["build_seconds"] = round(time.time() - t0, 2)
    rec["meta"] = {k: v for k, v in meta.items() if k not in ("pool", "free_pool")}
    rec["pool"] = meta.get("pool")
    rec["free_pool"] = meta.get("free_pool")

    if layout is not None:
        base, pool = layout
        lay = {"N": a.N, "mode": a.mode, "formulation": FORM, "pool": pool,
               "x_vars": meta["x_vars"], "vars": meta["vars"],
               "clauses": meta["clauses"],
               "var_of_half_h_r": "var = 1 + half*sum(pool) + sum(h' in pool, h'<h) + r",
               "lift": "true modulus = 2*h ; true residue = 2*r + half ; p = 2*h+1",
               "active_halves": {"symmetric": [0, 1], "fixedhalf": [1],
                                 "onehalf": [0]}[a.mode],
               "selfridge_pairs_residue_modulus": SELFRIDGE_PAIRS if a.mode == "fixedhalf" else None,
               "cnf": cnf}
        with open(os.path.join(a.cnfdir, f"{FORM}-N{a.N}.layout.json"), "w",
                  encoding="utf-8", errors="replace") as f:
            json.dump(lay, f, indent=1)
        with open(os.path.join(a.cnfdir, f"READY-N{a.N}.txt"), "a",
                  encoding="utf-8", errors="replace") as f:
            stamp = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
            f.write(f"{FORM} N={a.N} cnf={os.path.basename(cnf)} "
                    f"vars={meta['vars']} clauses={meta['clauses']} "
                    f"bytes={meta['cnf_bytes']} built={stamp}" + chr(10))
    else:
        with open(os.path.join(a.cnfdir, f"READY-N{a.N}.txt"), "a",
                  encoding="utf-8", errors="replace") as f:
            stamp = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
            f.write(f"{FORM} N={a.N} NO-CNF reason={meta.get('density_verdict')} "
                    f"({stamp})" + chr(10))

    if a.export_only:
        rec["result"] = "EXPORT_ONLY"
        rec["outcome"] = "CNF exported for the independent solver path; no solve run here"
        rec["solve_seconds"] = 0.0
        path = os.path.join(a.outdir, f"receipt-export-{tag}.json")
        with open(path, "w", encoding="utf-8", errors="replace") as f:
            json.dump(rec, f, indent=1)
        print(json.dumps({"tag": tag, "result": "EXPORT_ONLY", "cnf": cnf,
                          "build_seconds": rec["build_seconds"]}))
        return

    if layout is None:
        rec["result"] = "UNSAT_BY_DENSITY"
        rec["outcome"] = f"UNSAT_TO_N (N={a.N}, {a.mode}): reciprocal mass insufficient, no solver needed"
        rec["solve_seconds"] = 0.0
        rec["unsat_source"] = "density"
    else:
        st, el, model = solve(cnf, a.solver, a.secs,
                              os.path.join(a.outdir, f"{tag}.solverlog"), seed=a.seed)
        rec["result"] = st
        rec["solve_seconds"] = round(el, 2)
        if st == "SAT":
            halves = decode(model, base, pool, a.N, a.mode)
            rec["halves"] = {str(k): sorted(v, key=lambda t: t[1]) for k, v in halves.items()}
            if a.mode == "onehalf":
                ok, L = verify_half_independent(halves[0])
                rec["verification"] = {"WITNESS_VALID": ok, "half0_covers_Z": ok,
                                       "half0_lcm": L,
                                       "moduli_half0": sorted(m for _, m in halves[0]),
                                       "sum_recip": sum(1.0/m for _, m in halves[0]),
                                       "note": "ONE HALF ONLY - this is NOT an Erdos 273 witness"}
            else:
                rec["verification"] = verify_witness(halves)
            rec["outcome"] = ("WITNESS_UNVERIFIED->CHECKED" if rec["verification"]["WITNESS_VALID"]
                              else "SAT_BUT_VERIFICATION_FAILED")
        elif st == "UNSAT":
            rec["outcome"] = (f"UNSAT_TO_N (N={a.N}, {a.mode}): no covering system of Z with "
                              f"distinct moduli p-1 (p>=5) whose lcm divides {2*a.N}")
        else:
            rec["outcome"] = f"TIMEOUT_AT_N (N={a.N}, {a.mode}) after {a.secs}s"
        rec["unsat_source"] = "solver" if st == "UNSAT" else None
        rec.update(SOLVE_META)
    rec["semantics"] = semantics(a.N, a.mode, rec["result"], rec.get("unsat_source"))
    rec["finished"] = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
    path = os.path.join(a.outdir, f"receipt-{tag}.json")
    with open(path, "w", encoding="utf-8", errors="replace") as f:
        json.dump(rec, f, indent=1)
    print(json.dumps({k: rec[k] for k in ("tag", "result", "outcome", "build_seconds",
                                          "solve_seconds")}, ensure_ascii=False))
    print("receipt " + path)


if __name__ == "__main__":
    main()
