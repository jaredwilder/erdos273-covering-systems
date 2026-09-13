#!/usr/bin/env python3
"""Independent exact verifier for an anneal273 witness.  Stdlib only, no shared code
with the C searcher -- the whole point is that it re-derives the covering from scratch.

Usage:
  python verify273.py <witness.json> [--require-H] [--exclude-2]
  python verify273.py --selfcheck          # verifies the two known controls
"""
import json, sys
from math import gcd


def isprime(n: int) -> bool:
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


def lcm(a: int, b: int) -> int:
    return a // gcd(a, b) * b


def check_cover(pairs):
    """pairs = [(residue, modulus)].  Returns (ok, L, n_uncovered, first_uncovered)."""
    L = 1
    for _, m in pairs:
        L = lcm(L, m)
    covered = bytearray(L)
    for r, m in pairs:
        r %= m
        for j in range(r, L, m):
            covered[j] = 1
    bad = [i for i in range(L) if not covered[i]]
    return (len(bad) == 0, L, len(bad), bad[:5])


def report(pairs, require_H=False, exclude_2=False, label="witness"):
    mods = [m for _, m in pairs]
    out = {"label": label, "n_classes": len(pairs)}
    out["moduli_distinct"] = (len(set(mods)) == len(mods))
    if require_H:
        bad = [m for m in mods if not (m >= 2 and isprime(2 * m + 1))]
        out["all_in_H"] = (len(bad) == 0)
        out["not_in_H"] = bad
        out["primes_2m_plus_1"] = sorted(2 * m + 1 for m in mods)
        out["all_primes_ge_5"] = all(p >= 5 for p in out["primes_2m_plus_1"])
    if exclude_2:
        out["excludes_modulus_2"] = (2 not in mods)
    ok, L, nbad, first = check_cover(pairs)
    out["lcm"] = L
    out["covers_all_residues"] = ok
    out["uncovered_count"] = nbad
    out["first_uncovered"] = first
    out["reciprocal_sum"] = sum(1.0 / m for m in mods)
    out["VERDICT"] = "COVERING_VERIFIED" if ok else "NOT_A_COVERING"
    return out


def selfcheck():
    # Control 1: Selfridge's half, divisors of 180 that lie in H
    self180 = [(0, 2), (1, 3), (3, 5), (5, 6), (0, 9), (0, 15), (3, 18), (11, 20), (9, 30), (87, 90), (33, 36)]
    r1 = report(self180, require_H=True, label="CONTROL-1 Selfridge half mod 180")
    # Control 2: Krukenberg Z/144 pool -- no known layout hardcoded, only pool density
    pool144 = [3, 4, 6, 8, 9, 12, 16, 18, 24, 36, 48]
    r2 = {"label": "CONTROL-2 pool Z/144", "pool": pool144,
          "reciprocal_sum": sum(1.0 / m for m in pool144),
          "expected": 23 / 18}
    print(json.dumps([r1, r2], indent=1))
    return 0 if r1["VERDICT"] == "COVERING_VERIFIED" else 1


def main():
    if "--selfcheck" in sys.argv:
        sys.exit(selfcheck())
    path = sys.argv[1]
    with open(path, "r", encoding="utf-8") as f:
        d = json.load(f)
    pairs = [(int(a), int(b)) for a, b in d["pairs"]]
    out = report(pairs,
                 require_H=("--require-H" in sys.argv),
                 exclude_2=("--exclude-2" in sys.argv),
                 label=path)
    # doubled / lifted form, for pasting into Lean
    out["doubled_odd_lift"] = ["%d mod %d" % (2 * (r % m) + 1, 2 * m) for r, m in pairs]
    out["doubled_even_lift"] = ["%d mod %d" % (2 * (r % m), 2 * m) for r, m in pairs]
    print(json.dumps(out, indent=1))
    sys.exit(0 if out["VERDICT"] == "COVERING_VERIFIED" else 1)


if __name__ == "__main__":
    main()
