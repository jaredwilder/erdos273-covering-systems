#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
decode_model.py -- turn a DIMACS model for one of the Erdos-273 CNFs into the
explicit covering system, and RE-VERIFY it exactly (fresh code path: per-integer
membership test over Z/lcm, no striding sieve, no reuse of the encoder).

usage:
  python3 decode_model.py --layout cnf/symmetric-two-halves-N27720.layout.json \
                          --model  solver_stdout.txt
`--model` accepts raw solver stdout ("s SATISFIABLE" + "v ..." lines) or a bare
whitespace-separated list of signed integers.
"""
from __future__ import annotations
import argparse, json, math, sys


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


def read_model(path):
    pos = set()
    with open(path, encoding="utf-8", errors="replace") as f:
        txt = f.read()
    toks = []
    if "v " in txt or txt.lstrip().startswith("v"):
        for line in txt.splitlines():
            ls = line.strip()
            if ls.startswith("v "):
                toks.extend(ls[2:].split())
            elif ls == "v":
                pass
    else:
        toks = txt.split()
    for t in toks:
        try:
            iv = int(t)
        except ValueError:
            continue
        if iv > 0:
            pos.add(iv)
    return pos


def covers_Z(pairs):
    """(residue, modulus) pairs.  Enumerate Z/lcm, test each integer directly."""
    if not pairs:
        return False, 0, None
    L = 1
    for _, m in pairs:
        L = L * m // math.gcd(L, m)
    for n in range(L):
        if not any((n - r) % m == 0 for r, m in pairs):
            return False, L, n
    return True, L, None


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--layout", required=True)
    ap.add_argument("--model", required=True)
    ap.add_argument("--json-out", default=None)
    a = ap.parse_args()

    lay = json.load(open(a.layout, encoding="utf-8"))
    pool = lay["pool"]
    total = sum(pool)
    pos = read_model(a.model)

    # var = 1 + half*total + prefix(h) + r
    prefix, acc = {}, 0
    for h in pool:
        prefix[h] = acc
        acc += h

    halves = {0: [], 1: []}
    active = lay.get("active_halves", [0, 1])
    for half in active:
        for h in pool:
            for r in range(h):
                if 1 + half * total + prefix[h] + r in pos:
                    halves[half].append((r, h))
    if lay["mode"] == "fixedhalf":
        halves[0] = [tuple(t) for t in lay["selfridge_pairs_residue_modulus"]]
    rep_active = active

    rep = {"layout": a.layout, "model": a.model, "N": lay["N"],
           "formulation": lay["formulation"],
           "half0": sorted(halves[0], key=lambda t: t[1]),
           "half1": sorted(halves[1], key=lambda t: t[1])}

    ok0, L0, bad0 = covers_Z(halves[0])
    rep["half0_covers_Z"], rep["half0_lcm"] = ok0, L0
    if lay["mode"] == "onehalf":
        rep["VERDICT"] = ("HALF_VERIFIED (NOT an Erdos 273 witness)" if ok0
                          else "HALF_INVALID")
        rep["first_uncovered"] = bad0
        print(json.dumps(rep, indent=1))
        return

    ok1, L1, bad1 = covers_Z(halves[1])
    rep["half1_covers_Z"], rep["half1_lcm"] = ok1, L1

    m0 = [m for _, m in halves[0]]
    m1 = [m for _, m in halves[1]]
    rep["disjoint_and_distinct"] = len(set(m0 + m1)) == len(m0) + len(m1)

    # LIFT: half h -> original moduli 2h ; residue 2r + parity
    lifted = [(2 * r, 2 * h) for r, h in halves[0]] + \
             [(2 * r + 1, 2 * h) for r, h in halves[1]]
    rep["covering_system_residue_modulus"] = sorted(lifted, key=lambda t: t[1])
    okL, LL, badL = covers_Z(lifted)
    rep["lifted_covers_Z"], rep["lifted_lcm"], rep["first_uncovered"] = okL, LL, badL
    prim = [{"m": m, "p": m + 1, "prime": is_prime(m + 1)} for _, m in lifted]
    rep["primes_p_with_m_eq_p_minus_1"] = sorted(d["p"] for d in prim)
    rep["all_p_prime_and_ge5"] = all(d["prime"] and d["p"] >= 5 for d in prim)
    rep["all_moduli_distinct"] = len(set(m for _, m in lifted)) == len(lifted)
    rep["k"] = len(lifted)
    rep["sum_reciprocals"] = sum(1.0 / m for _, m in lifted)
    rep["VERDICT"] = ("ERDOS_273_WITNESS_VERIFIED" if (okL and ok0 and ok1
                      and rep["all_p_prime_and_ge5"] and rep["all_moduli_distinct"]
                      and rep["disjoint_and_distinct"]) else "INVALID")
    out = json.dumps(rep, indent=1)
    print(out)
    if a.json_out:
        open(a.json_out, "w", encoding="utf-8", errors="replace").write(out)


if __name__ == "__main__":
    main()
