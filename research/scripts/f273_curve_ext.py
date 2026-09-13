#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Extend the density curve past 2,162,160 to ~1e9.

NEED_2      = 2       (both halves need reciprocal sum > 1)
NEED_KRUK   = 7/3     (IF Krukenberg 1971 holds: a distinct-moduli covering with least
                       modulus 3 has sum 1/m >= 4/3; the 2-half still needs > 1)
"""
from __future__ import annotations
import json
from fractions import Fraction

def is_prime(n):
    if n < 2: return False
    for p in (2,3,5,7,11,13,17,19,23,29,31,37):
        if n % p == 0: return n == p
    d,s = n-1,0
    while d % 2 == 0: d//=2; s+=1
    for a in (2,3,5,7,11,13,17,19,23,29,31,37):
        x = pow(a,d,n)
        if x in (1,n-1): continue
        for _ in range(s-1):
            x = x*x % n
            if x == n-1: break
        else: return False
    return True

def in_H(h): return h >= 2 and is_prime(2*h+1)

def divs(fs):
    ds = [1]
    for p,e in fs:
        nd, pe = [], 1
        for _ in range(e+1):
            nd.extend(d*pe for d in ds); pe *= p
        ds = nd
    return ds

def fstr(fs): return "*".join(f"{p}^{e}" if e>1 else str(p) for p,e in fs)

# lcm-shaped / highly composite candidates up to ~1e9
CANDS = [
 [(2,3),(3,2),(5,1),(7,1),(11,1)],                                   # 27720
 [(2,4),(3,2),(5,1),(7,1),(11,1)],                                   # 55440
 [(2,3),(3,2),(5,1),(7,1),(11,1),(13,1)],                            # 360360
 [(2,4),(3,2),(5,1),(7,1),(11,1),(13,1)],                            # 720720
 [(2,5),(3,2),(5,1),(7,1),(11,1),(13,1)],                            # 1441440
 [(2,4),(3,3),(5,1),(7,1),(11,1),(13,1)],                            # 2162160
 [(2,5),(3,3),(5,1),(7,1),(11,1),(13,1)],                            # 4324320
 [(2,4),(3,4),(5,1),(7,1),(11,1),(13,1)],                            # 6486480
 [(2,6),(3,3),(5,1),(7,1),(11,1),(13,1)],                            # 8648640
 [(2,4),(3,3),(5,2),(7,1),(11,1),(13,1)],                            # 10810800
 [(2,5),(3,3),(5,2),(7,1),(11,1),(13,1)],                            # 21621600
 [(2,4),(3,2),(5,1),(7,1),(11,1),(13,1),(17,1)],                     # 12252240
 [(2,4),(3,3),(5,1),(7,1),(11,1),(13,1),(17,1)],                     # 36756720
 [(2,6),(3,3),(5,2),(7,1),(11,1),(13,1)],                            # 43243200
 [(2,5),(3,3),(5,1),(7,1),(11,1),(13,1),(17,1)],                     # 73513440
 [(2,5),(3,2),(5,2),(7,1),(11,1),(13,1),(17,1)],                     # 122522400
 [(2,4),(3,3),(5,2),(7,1),(11,1),(13,1),(17,1)],                     # 183783600
 [(2,5),(3,3),(5,2),(7,1),(11,1),(13,1),(17,1)],                     # 367567200
 [(2,6),(3,3),(5,2),(7,1),(11,1),(13,1),(17,1)],                     # 735134400
 [(2,4),(3,3),(5,2),(7,2),(11,1),(13,1)],                            # 75675600
 [(2,5),(3,3),(5,2),(7,2),(11,1),(13,1)],                            # 151351200
 [(2,4),(3,3),(5,1),(7,1),(11,1),(13,1),(19,1)],                     # 41081040
 [(2,4),(3,3),(5,2),(7,1),(11,1),(13,1),(19,1)],                     # 205405200
 [(2,4),(3,3),(5,1),(7,1),(11,1),(13,1),(17,1),(19,1)],              # 698377680
 [(2,3),(3,2),(5,1),(7,1),(11,1),(13,1),(17,1),(19,1)],              # 232792560
 [(2,4),(3,2),(5,1),(7,1),(11,1),(13,1),(17,1),(19,1)],              # 465585120
 [(2,4),(3,2),(5,1),(7,1),(11,1),(13,1),(23,1)],                     # 281801520
 [(2,4),(3,3),(5,1),(7,1),(11,1),(13,1),(23,1)],                     # 845404560
]
NEED2 = Fraction(2)
NEEDK = Fraction(7,3)
rows = []
for fs in CANDS:
    N = 1
    for p,e in fs: N *= p**e
    if N > 1_000_000_000: continue
    pool = [d for d in divs(fs) if in_H(d)]
    S = sum(Fraction(1,d) for d in pool)
    rows.append({"N": N, "fact": fstr(fs), "k": len(pool), "S": float(S),
                 "slack2": float(S-NEED2), "slackK": float(S-NEEDK),
                 "clears2": S > NEED2, "clearsK": S > NEEDK,
                 "x_vars_hardhalf": sum(d for d in pool if d != 2)})
rows.sort(key=lambda r: r["N"])
print(f"{'N':>12} {'factorization':<28} {'|pool|':>6} {'S':>7} {'S-2':>8} {'S-7/3':>8} {'>2':>3} {'>7/3':>5}")
for r in rows:
    print(f"{r['N']:>12} {r['fact']:<28} {r['k']:>6} {r['S']:>7.4f} {r['slack2']:>+8.4f} "
          f"{r['slackK']:>+8.4f} {'Y' if r['clears2'] else 'n':>3} {'YES' if r['clearsK'] else 'no':>5}")
first = next((r for r in rows if r["clearsK"]), None)
print()
if first:
    print(f"FIRST N WITH S > 7/3 = 2.3333 :  N = {first['N']:,}  ({first['fact']})  S = {first['S']:.4f}")
    print(f"  hard-half x_vars (sum of pool minus 2) = {first['x_vars_hardhalf']:,}"
          f"   cover clauses = {first['N']:,}")
else:
    print("NO tested N reaches S > 7/3")
json.dump(rows, open("curve-ext.json","w",encoding="utf-8"), indent=1)
