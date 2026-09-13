#!/usr/bin/env python3
"""Per-prime-power counting conditions for the HALF-B-ALONE instance.

For each prime power q | N, Z/N splits into q classes mod q.  A modulus m
reaches q/gcd(m,q) of those classes and, inside each, has density gcd(m,q)/m.
Moduli with gcd(m,q)=1 give their full 1/m to EVERY class -- that mass is free.
The rest is targetable.  If (targetable mass) < q*(1 - free), no assignment of
residues can bring every class to density 1 and the instance is UNSAT by
counting alone.

Result (2026-09-02): NO counting obstruction at any q, for any N on the ladder.
The local-search plateau is therefore NOT explained by a density fact.

Usage: python class_density.py [N ...]
"""
import sys
from math import gcd


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


def pool(N, drop2=True):
    P = [m for m in range(2, N + 1) if N % m == 0 and isprime(2 * m + 1)]
    return [m for m in P if not (drop2 and m == 2)]


def prime_powers(N):
    out, n, p = [], N, 2
    while p * p <= n:
        if n % p == 0:
            q = 1
            while n % p == 0:
                n //= p
                q *= p
            out.append(q)
        p += 1
    if n > 1:
        out.append(n)
    return out


def main():
    Ns = [int(x) for x in sys.argv[1:]] or [3960, 27720, 55440, 83160, 360360, 2162160]
    for N in Ns:
        P = pool(N)
        S = sum(1.0 / m for m in P)
        print("=== N=%d  |pool|=%d  S_B=%.4f ===" % (N, len(P), S))
        for q in prime_powers(N):
            free = sum(1.0 / m for m in P if gcd(m, q) == 1)
            targetable = sum(q * 1.0 / m for m in P if gcd(m, q) > 1)
            need = q * max(0.0, 1.0 - free)
            ok = targetable >= need - 1e-12
            print("  mod %-5d free/class=%.4f  need/class=%.4f  need total=%.4f  "
                  "targetable=%.4f  -> %s"
                  % (q, free, max(0.0, 1 - free), need, targetable,
                     "feasible by counting" if ok else "*** COUNTING OBSTRUCTION ***"))
        print()


if __name__ == "__main__":
    main()
