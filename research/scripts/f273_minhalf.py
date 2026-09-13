#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
DENSITY-AFTER-SPLIT — the decisive computation.

THE ARGUMENT
------------
After the parity split, Erdos 273 at ceiling N asks for TWO DISJOINT distinct-moduli
covering systems of Z drawn from  pool = H ∩ divisors(N),  H = {(p-1)/2 : p prime >= 5}.

The halves are disjoint, so **at most one of them contains the modulus 2**. Call the one
that may contain it half A, and the other half B. Then:

    sum_A 1/h  >  1            (any distinct-moduli covering of Z has reciprocal sum > 1,
                                strictly: = 1 would be an exact cover, impossible for >= 2
                                distinct moduli by Mirsky-Newman)
    sum_B 1/h  >= D(N)         where D(N) := the MINIMUM reciprocal sum of a distinct-moduli
                                covering of Z drawn from pool \\ {2}
    sum_A + sum_B <= S(N)      the halves are disjoint subsets of pool

    =>   S(N)  >  1 + D(N)

**Therefore: if S(N) <= 1 + D(N), the rung is UNSAT. No SAT solver required.**

Note the case split on modulus 3 is unnecessary: if 3 sits with 2 in half A then
half B ⊆ pool \\ {2,3} and its minimum is D_{23}(N) >= D(N), so the same inequality
with D(N) is implied. D(N) — 2 excluded only — is the decisive quantity.

WHAT THIS PROGRAM COMPUTES
--------------------------
For each N it runs a COMPLETE branch-and-bound search for a covering of Z/N drawn from
pool \\ {2} whose reciprocal sum is <= budget := S(N) - 1.

  * search exhausts with nothing found  ->  D(N) > budget  ->  S(N) < 1 + D(N)  ->  **UNSAT, PROVED**
  * a covering is found                 ->  that IS the construction path: its moduli are
                                            half B; exclude them and search only for a 2-half
                                            avoiding them (a far smaller problem)
  * node cap hit                         ->  INCONCLUSIVE, reported as such, never as UNSAT

SOUNDNESS OF THE SEARCH
-----------------------
* Branch on the LEAST UNCOVERED CELL c. Every covering must cover c, so some chosen class
  contains c; enumerating all moduli h (residue then FORCED to c mod h) is exhaustive.
* Prune when  density_so_far + uncovered_count/N  >  budget. Sound because the remaining
  classes must cover `uncovered_count` cells and a class of modulus h covers exactly N/h
  cells, so their reciprocal sum is at least uncovered_count/N.
* Every modulus used at most once (distinctness), and lcm | N by construction, so covering
  Z/N is exactly covering Z.

Coverage is carried in a Python big-int bitset; since h | N the periodic mask for
(h, r) is exactly  ((2^N - 1)/(2^h - 1)) << r.
"""
from __future__ import annotations
import argparse, json, os, sys, time
from fractions import Fraction


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


def divisors(n):
    ds, i = [], 1
    while i * i <= n:
        if n % i == 0:
            ds.append(i)
            if i != n // i:
                ds.append(n // i)
        i += 1
    return sorted(ds)


def in_H(h):
    return h >= 2 and is_prime(2 * h + 1)


def search(N, exclude, budget, node_cap, deadline, pool_override=None):
    """Complete B&B for a covering of Z/N from pool\\exclude with sum 1/h <= budget."""
    if pool_override is not None:
        pool = sorted(pool_override)
        assert all(N % h == 0 for h in pool), 'every modulus must divide N'
    else:
        pool = [d for d in divisors(N) if in_H(d) and d not in exclude]
    full = (1 << N) - 1
    base = {h: full // ((1 << h) - 1) for h in pool}   # bits at 0, h, 2h, ...
    inv = {h: 1.0 / h for h in pool}
    k = len(pool)
    nodes = [0]
    best = [None]
    hit_cap = [False]

    bestdens = [budget]     # incumbent: only accept strictly better than this

    def rec(covered, used_mask, dens, chosen):
        nodes[0] += 1
        if nodes[0] > node_cap or time.time() > deadline:
            hit_cap[0] = True
            return
        rem = full & ~covered
        if rem == 0:
            if dens < bestdens[0] - 1e-12:
                bestdens[0] = dens
                best[0] = list(chosen)
            return
        # sound lower bound on the reciprocal sum still required
        if dens + rem.bit_count() / N > bestdens[0] - 1e-12:
            return
        c = (rem & -rem).bit_length() - 1          # least uncovered cell
        for i, h in enumerate(pool):
            if (used_mask >> i) & 1:
                continue
            nd = dens + inv[h]
            if nd >= bestdens[0] - 1e-12:
                continue
            r = c % h
            chosen.append((r, h))
            rec(covered | (base[h] << r), used_mask | (1 << i), nd, chosen)
            chosen.pop()

    t0 = time.time()
    rec(0, 0, 0.0, [])
    found = best[0] is not None
    return {"pool_size": k, "pool": pool, "found": found,
            "covering": best[0], "nodes": nodes[0],
            "seconds": round(time.time() - t0, 2),
            "exhaustive": (not hit_cap[0]),
            "best_density": (bestdens[0] if best[0] is not None else None),
            "budget": budget}


def verify(pairs, N):
    """Independent check: every cell of Z/N hit, moduli distinct, all 2h+1 prime >= 5."""
    hit = bytearray(N)
    for r, m in pairs:
        for x in range(r % m, N, m):
            hit[x] = 1
    return {"covers": all(hit),
            "distinct": len(set(m for _, m in pairs)) == len(pairs),
            "all_legal": all(is_prime(2 * m + 1) and 2 * m + 1 >= 5 for _, m in pairs),
            "sum_recip": sum(1.0 / m for _, m in pairs),
            "moduli": sorted(m for _, m in pairs)}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--Ns", required=True, help="comma-separated")
    ap.add_argument("--node-cap", type=int, default=40_000_000)
    ap.add_argument("--secs-per-N", type=int, default=900)
    ap.add_argument("--out", default="/root/peer/out/minhalf.json")
    ap.add_argument("--question-lock", required=True)
    ap.add_argument("--pool", default=None,
                    help="CONTROL ONLY: explicit comma-separated pool, bypasses H (for known-answer "
                         "controls on arbitrary modulus sets such as Krukenberg's Z/144 system)")
    ap.add_argument("--exclude", default="2",
                    help="comma-separated moduli excluded from the pool (the OTHER half holds them)")
    ap.add_argument("--budget", type=float, default=None,
                    help="CONTROL ONLY: override budget=S-1 (use to prove the searcher CAN find "
                         "a 2-free covering when one exists)")
    a = ap.parse_args()
    if not os.path.exists(a.question_lock):
        raise SystemExit("question lock not found: " + a.question_lock)

    rows = []
    for N in [int(x) for x in a.Ns.split(",")]:
        pool = [d for d in divisors(N) if in_H(d)]
        S = sum(1.0 / d for d in pool)
        if a.pool:
            pool = [int(x) for x in a.pool.split(",")]
            S = sum(1.0 / d for d in pool)
        budget = S - 1.0 if a.budget is None else a.budget
        sys.stdout.write(f"\n=== N={N}  S={S:.6f}  budget=S-1={budget:.6f} ===\n")
        sys.stdout.flush()
        EXC = set(int(x) for x in a.exclude.split(",") if x.strip())
        PO = [int(x) for x in a.pool.split(",")] if a.pool else None
        if PO is not None:
            S = float(sum(Fraction(1, h) for h in PO))
            budget = a.budget if a.budget is not None else S - 1.0
        r = search(N, EXC, budget, a.node_cap, time.time() + a.secs_per_N, pool_override=PO)
        row = {"N": N, "S": S, "budget": budget, "excluded": sorted(EXC),
               "pool_size": len(pool),
               "pool_minus2_size": r["pool_size"], "nodes": r["nodes"],
               "seconds": r["seconds"], "exhaustive": r["exhaustive"],
               "found": r["found"]}
        if r["found"]:
            row["covering"] = r["covering"]
            row["verify"] = verify(r["covering"], N)
            row["D_exact_or_upper"] = row["verify"]["sum_recip"]
            row["D_plus_1_exceeds_S"] = (row["verify"]["sum_recip"] + 1.0 > S)
            L = 1
            from math import gcd
            for _, m in r["covering"]:
                L = L * m // gcd(L, m)
            row["lcm"] = L
            row["BBMST_filter_2or9or15_divides_lcm"] = (L % 2 == 0 or L % 9 == 0 or L % 15 == 0)
            row["VERDICT"] = ("CONSTRUCTION_PATH: covering found; it is the seed for the half-A search"
                              if not row["D_plus_1_exceeds_S"] else
                              "found but D+1>S at this budget - rung still dead")
        elif r["exhaustive"]:
            row["D_lower_bound_strict"] = budget
            row["D_plus_1_exceeds_S"] = True
            row["VERDICT"] = "UNSAT_BY_DENSITY_AFTER_SPLIT"
            row["proof"] = (f"Complete branch-and-bound over pool\\{{2}} (|pool\\{{2}}|="
                            f"{r['pool_size']}) found NO distinct-moduli covering of Z/{N} with "
                            f"reciprocal sum <= {budget:.6f}. Hence D({N}) > S({N})-1, i.e. "
                            f"S({N}) < 1 + D({N}). Since the 2-free half needs >= D({N}) and the "
                            f"other half needs > 1, and they are disjoint subsets of a pool of "
                            f"total mass S({N}) = {S:.6f}, no two disjoint coverings exist. "
                            f"UNSAT at ceiling 2N = {2*N}. NO SOLVER USED. "
                            f"Finite, kernel-checkable: the search tree is finite and every "
                            f"branch is closed by an explicit reciprocal-mass inequality.")
        else:
            row["VERDICT"] = "INCONCLUSIVE_NODE_CAP"
        rows.append(row)
        sys.stdout.write(json.dumps({k: row[k] for k in row if k != "covering"},
                                    default=str) + "\n")
        sys.stdout.flush()
        with open(a.out, "w", encoding="utf-8", errors="replace") as f:
            json.dump(rows, f, indent=1)
    print("\nDONE")


if __name__ == "__main__":
    main()
