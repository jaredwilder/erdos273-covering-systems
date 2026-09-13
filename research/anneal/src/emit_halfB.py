#!/usr/bin/env python3
"""Emit CNF for the HALF-B-ALONE instance of Erdos 273 (NEED = 1, not 2).

  "Does Z admit a covering system with distinct moduli from H\\{2}, all dividing N?"
  H = {(p-1)/2 : p prime >= 5}.

This is NOT the peer's symmetric-two-halves instance (which needs S(N) > 2).
Half B alone needs only S_B(N) > 1, which every rung from N = 3960 up satisfies.

Vars: x[m][r] for m in pool, r in 0..m-1.
Clauses:
  COVER   for each n in Z/N: OR_{m in pool} x[m][ n mod m ]
  AMO     at-most-one residue per modulus (Sinz sequential encoding)
No at-least-one clause: a modulus may go unused.  That is WLOG in the SAT
direction too -- an unused modulus can be given any residue afterwards, and
the covering only grows.

Usage: python emit_halfB.py N out.cnf [--include-2]
Writes out.cnf and out.cnf.layout.json (var -> (m,r) map, for decoding).
"""
import json
import sys


def isprime(n):
    if n < 2:
        return False
    if n % 2 == 0:
        return n == 2
    d = 3
    while d * d <= n:
        if n % d == 0:
            return False
        d += 2
    return True


def main():
    N = int(sys.argv[1])
    out = sys.argv[2]
    inc2 = "--include-2" in sys.argv

    pool = [m for m in range(2, N + 1) if N % m == 0 and isprime(2 * m + 1)]
    if not inc2:
        pool = [m for m in pool if m != 2]
    S = sum(1.0 / m for m in pool)

    xv = {}
    nv = 0
    for m in pool:
        for r in range(m):
            nv += 1
            xv[(m, r)] = nv

    clauses = []
    # COVER
    for n in range(N):
        clauses.append([xv[(m, n % m)] for m in pool])
    # AMO, sequential (Sinz)
    for m in pool:
        if m < 2:
            continue
        s = []
        for i in range(m - 1):
            nv += 1
            s.append(nv)
        clauses.append([-xv[(m, 0)], s[0]])
        for i in range(1, m - 1):
            clauses.append([-xv[(m, i)], s[i]])
            clauses.append([-s[i - 1], s[i]])
            clauses.append([-xv[(m, i)], -s[i - 1]])
        clauses.append([-xv[(m, m - 1)], -s[m - 2]])

    with open(out, "w", encoding="utf-8") as f:
        f.write("c Erdos 273 HALF-B-ALONE  N=%d  pool=%d moduli  S=%.6f  NEED>1\n" % (N, len(pool), S))
        f.write("p cnf %d %d\n" % (nv, len(clauses)))
        for c in clauses:
            f.write(" ".join(map(str, c)) + " 0\n")

    layout = {"N": N, "pool": pool, "S": S, "include_2": inc2,
              "n_vars": nv, "n_clauses": len(clauses),
              "x": {"%d,%d" % k: v for k, v in xv.items()},
              "formulation": "half-B-alone: covering of Z/N by distinct moduli from H%s, one class each"
                             % ("" if inc2 else " minus {2}")}
    with open(out + ".layout.json", "w", encoding="utf-8") as f:
        json.dump(layout, f)
    print("N=%d pool=%d S=%.6f vars=%d clauses=%d -> %s" % (N, len(pool), S, nv, len(clauses), out))


if __name__ == "__main__":
    main()
