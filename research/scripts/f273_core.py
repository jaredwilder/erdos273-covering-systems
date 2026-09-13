#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Erdos 273 -- STEP 0 (statement firewall arithmetic) + STEP 1 (reduction, verified in code)
+ the N=180 KNOWN-ANSWER CONTROL (Selfridge half), all by exact enumeration.

$0, deterministic, stdlib only.  Nothing here is a search over a big space.
"""
from __future__ import annotations
import json, sys, math
from itertools import product

OUT = {}

# ---------------------------------------------------------------- primality
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
    ds = []
    i = 1
    while i * i <= n:
        if n % i == 0:
            ds.append(i)
            if i != n // i:
                ds.append(n // i)
        i += 1
    return sorted(ds)


# M = {p-1 : p prime >= 5}   (the moduli the Lean statement allows)
def in_M(m: int) -> bool:
    return m >= 4 and is_prime(m + 1)


# H = {(p-1)/2 : p prime >= 5}  (the halved pool after the parity split)
def in_H(h: int) -> bool:
    return h >= 2 and is_prime(2 * h + 1)


# ------------------------------------------------------- exact cover checks
def covers_Zmod(pairs, N: int) -> bool:
    """pairs = [(residue, modulus)].  True iff every class of Z/N is hit.
    Every modulus MUST divide N for this to be equivalent to covering Z."""
    hit = bytearray(N)
    for r, m in pairs:
        assert N % m == 0, f"modulus {m} does not divide {N}"
        r %= m
        for x in range(r, N, m):
            hit[x] = 1
    return all(hit)


def covers_Z_independent(pairs) -> bool:
    """INDEPENDENT check, no divisibility assumption: enumerate Z/lcm directly
    with a fresh code path (per-integer test, not a striding sieve)."""
    L = 1
    for _, m in pairs:
        L = L * m // math.gcd(L, m)
    for n in range(L):
        if not any((n - r) % m == 0 for r, m in pairs):
            return False
    return True


# ============================================================== STEP 0
def step0_firewall():
    """Arithmetic half of the statement firewall.  The predicate-reading half is
    prose in the report; here we CHECK the numeric consequences."""
    f = {}
    # every allowed modulus p-1, p>=5, is >= 4 -> ne_bot (m != 0) and ne_top (m != 1) hold free
    Mlist = [p - 1 for p in range(5, 4000) if is_prime(p)]
    f["M_first_30"] = Mlist[:30]
    f["M_min"] = min(Mlist)
    f["ne_bot_free"] = all(m != 0 for m in Mlist)
    f["ne_top_free"] = all(m != 1 for m in Mlist)
    f["all_even"] = all(m % 2 == 0 for m in Mlist)
    f["nat_sub_safe"] = all((p - 1) >= 4 for p in range(5, 4000) if is_prime(p))
    # Ideal.span{m} = Ideal.span{m'} in Z  <=>  |m| = |m'| ; moduli positive => injective_moduli == distinct m
    f["span_injectivity_note"] = ("In Z, Ideal.span {m} = Ideal.span {m'} iff m = +-m'. "
                                  "All p-1 are positive, so injective_moduli is exactly 'the m_i are distinct'.")
    # the subset-vs-equality question
    f["moduli_condition"] = ("Lean reads: forall i, exists p prime, 5<=p and c.moduli i = span{p-1}. "
                             "This is a MEMBERSHIP condition on each modulus (subset of {p-1}), NOT set equality "
                             "with the infinite set {p-1 : p>=5}. The index type carries [Fintype], so the system "
                             "is finite. NOT VACUOUS. No statement defect on this axis.")
    # N vs Z
    f["N_vs_Z_note"] = ("Sibling .variants.three is over StrictCoveringSystem N. In the semiring N, "
                        "Ideal.span {m} = m*N, so a 'coset' is the ONE-SIDED AP {a, a+m, a+2m, ...}. "
                        "Equivalence: (Z=>N) take residues a_i in [0,m_i); each class a_i + m_i Z meets N in "
                        "exactly a_i + m_i N, so a Z-covering restricts to an N-covering with the same moduli. "
                        "(N=>Z) the union of the congruence classes a_i mod m_i is periodic with period "
                        "L = lcm(m_i); an N-covering shows it contains every n >= 0, hence a full period "
                        "[0,L), hence all of Z. Distinctness and finiteness are untouched. "
                        "So the witness object is THE SAME; only the ambient presentation differs.")
    OUT["step0_firewall"] = f
    return f


# ============================================================== STEP 1
def selfridge_pool():
    return [d for d in divisors(180) if in_H(d)]


def dfs_cover(pool, N, need_all=False, node_cap=5_000_000):
    """Exact DFS: cover Z/N using a SUBSET of `pool` (distinct moduli, one residue
    each).  Branch on the least uncovered cell.  Returns the first covering found."""
    pool = sorted(pool)
    nodes = [0]
    covered = bytearray(N)
    chosen = []

    def first_uncov():
        for i in range(N):
            if not covered[i]:
                return i
        return -1

    def rec(used_mask):
        nodes[0] += 1
        if nodes[0] > node_cap:
            raise RuntimeError("node cap")
        c = first_uncov()
        if c < 0:
            return True
        # density prune: remaining reciprocal mass must cover remaining cells
        rem = sum(1.0 / m for k, m in enumerate(pool) if not (used_mask >> k) & 1)
        uncov = sum(1 for i in range(N) if not covered[i])
        if rem * N < uncov - 1e-9:
            return False
        for k, m in enumerate(pool):
            if (used_mask >> k) & 1:
                continue
            r = c % m
            added = [x for x in range(r, N, m) if not covered[x]]
            for x in added:
                covered[x] = 1
            chosen.append((r, m))
            if rec(used_mask | (1 << k)):
                return True
            chosen.pop()
            for x in added:
                covered[x] = 0
        return False

    ok = rec(0)
    return (list(chosen) if ok else None), nodes[0]


def step1_reduction_and_control():
    r = {}
    # ---- 1a. the parity split, verified as an identity on a concrete instance
    # claim: for m = 2m', the class (2b mod 2m') inside 2Z corresponds to (b mod m') in Z
    ok = True
    for mp in range(2, 40):
        m = 2 * mp
        for b in range(mp):
            lhs = set((2 * t) % m for t in range(200) if (t - b) % mp == 0)
            if lhs != {(2 * b) % m}:
                ok = False
        for b in range(mp):
            # every n with n = 2t and t = b mod m'  <=>  n = 2b mod 2m'
            A = set(n for n in range(-400, 400) if n % 2 == 0 and ((n // 2) - b) % mp == 0)
            B = set(n for n in range(-400, 400) if (n - 2 * b) % m == 0)
            if A != B:
                ok = False
    r["parity_split_identity_verified"] = ok
    r["parity_split_identity_range"] = "m' in [2,40), all residues b, n in [-400,400)"

    # ---- 1b. Selfridge's half at N=180, found by exhaustive DFS (not copied)
    pool180 = selfridge_pool()
    r["divisors_of_180_in_H"] = pool180
    r["divisors_of_180_in_H_sum_recip"] = round(sum(1 / m for m in pool180), 6)
    cov, nodes = dfs_cover(pool180, 180)
    r["selfridge_half_search_nodes"] = nodes
    assert cov is not None, "control FAILED: no covering of Z/180 from divisors of 180 in H"
    cov = sorted(cov, key=lambda t: t[1])
    r["selfridge_half_pairs_residue_modulus"] = cov
    r["selfridge_half_moduli"] = sorted(m for _, m in cov)
    r["selfridge_half_distinct"] = len(set(m for _, m in cov)) == len(cov)
    r["selfridge_half_sum_recip"] = round(sum(1 / m for _, m in cov), 6)
    # exact verification, two independent code paths
    r["selfridge_verify_stride_sieve"] = covers_Zmod(cov, 180)
    r["selfridge_verify_independent"] = covers_Z_independent(cov)

    # ---- 1c. doubling back into M-space: 2h must be p-1 for a prime p >= 5
    doubled = []
    for _, h in cov:
        m = 2 * h
        p = m + 1
        doubled.append({"h": h, "m_eq_p_minus_1": m, "p": p, "p_prime": is_prime(p), "p_ge_5": p >= 5})
    r["doubled_moduli"] = doubled
    r["doubled_all_legal"] = all(d["p_prime"] and d["p_ge_5"] for d in doubled)
    r["doubled_primes"] = sorted(d["p"] for d in doubled)
    r["doubled_moduli_list"] = sorted(d["m_eq_p_minus_1"] for d in doubled)
    r["doubled_all_divide_360"] = all(360 % d["m_eq_p_minus_1"] == 0 for d in doubled)

    # ---- 1d. the round trip: half-space witness -> M-space covering of a PARITY CLASS
    # take the Selfridge half as the ODD-side half; residues 2h+1 ... verify it covers the odds of Z/360
    odd_pairs = [(2 * rr + 1, 2 * h) for rr, h in cov]
    hit = bytearray(360)
    for a, m in odd_pairs:
        for x in range(a % m, 360, m):
            hit[x] = 1
    r["odd_class_fully_covered_mod360"] = all(hit[i] for i in range(1, 360, 2))
    r["even_class_untouched_mod360"] = not any(hit[i] for i in range(0, 360, 2))
    r["round_trip_note"] = ("A half-space covering {(r,h)} lifted by (a,m) = (2r+eps, 2h) covers EXACTLY the "
                            "parity class eps of Z and nothing else. Two disjoint half-space coverings, lifted "
                            "with eps=0 and eps=1, give a covering of Z with distinct even moduli 2h.")
    OUT["step1_reduction"] = r
    return r


# ============================================================== pool ladder
def pool_table(Ns):
    rows = []
    for N in Ns:
        pool = [d for d in divisors(N) if in_H(d)]
        s = sum(1 / m for m in pool)
        rows.append({
            "N": N,
            "factorization": factor_str(N),
            "pool_size": len(pool),
            "sum_recip_H": round(s, 6),
            "sum_recip_minus_2": round(s - 0.5, 6) if 2 in pool else round(s, 6),
            "two_half_density_ok": s > 2.0,
            "two_half_slack_pct": round((s - 2.0) / 2.0 * 100, 4),
            "cnf_vars_est": 2 * sum(pool),
            "cnf_cover_clauses": 2 * N,
            "cnf_cover_literals": 2 * N * len(pool),
            "pool": pool if len(pool) <= 80 else pool[:80] + ["..."],
        })
    return rows


def factor_str(n):
    out, d = [], 2
    while d * d <= n:
        e = 0
        while n % d == 0:
            n //= d
            e += 1
        if e:
            out.append(f"{d}^{e}" if e > 1 else str(d))
        d += 1
    if n > 1:
        out.append(str(n))
    return "*".join(out)


def main():
    step0_firewall()
    step1_reduction_and_control()

    # H itself
    H = sorted(h for h in range(2, 600) if in_H(h))
    OUT["H_up_to_600"] = H
    OUT["H_first_40"] = H[:40]
    OUT["integers_lt_60_absent_from_H"] = [h for h in range(1, 60) if not in_H(h)]

    # the instructed ladder + extra candidates chosen for divisor-richness
    ladder = [180, 3960, 7920, 27720, 55440, 110880, 221760, 332640, 720720,
              5040, 10080, 20160, 25200, 45360, 50400, 65520, 75600, 83160,
              98280, 131040, 138600, 166320, 196560, 249480, 277200, 360360,
              498960, 554400, 655200, 831600, 1081080, 1441440, 2162160]
    OUT["pool_table"] = pool_table(sorted(set(ladder)))

    print(json.dumps(OUT, indent=1))


if __name__ == "__main__":
    main()
