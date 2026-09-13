#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Decode + INDEPENDENTLY VERIFY a SAT model from a hard-half cube run.

    python3 decode_cube_model.py --layout cnf/hard-half-only-N3960.layout.json \\
                                 --model out/hh3960-c00007.solverlog \\
                                 --cube  cubes/N3960/cube-c00007.cube \\
                                 --out   out/witness-hh3960-c00007.json

WHAT THIS DOES AND DOES NOT ESTABLISH
-------------------------------------
A SAT hard-half model is a distinct-moduli covering system of Z drawn from
`H n divisors(N) \\ {2}`.

  ** IT IS NOT AN ERDOS 273 WITNESS. **  It is HALF of one.

Erdos 273 needs TWO DISJOINT such halves.  A SAT here is stage one of two.  The script
therefore ends by printing the EXACT stage-two command: search for the complementary half in
`pool \\ (moduli this half used)` -- the half that may hold modulus 2.  Only if stage two also
closes, and the lifted object re-verifies, is there a candidate witness, and even then the
status is WITNESS_UNVERIFIED until the Lean kernel accepts it.

The verification below is a FRESH CODE PATH: it re-derives coverage by direct enumeration of
Z/N and re-tests primality of every 2h+1 from scratch.  It never trusts the solver, the
encoder's variable map beyond the published formula, or the cube.
"""
from __future__ import annotations
import argparse, json, math, os, re, sys

_HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(os.path.dirname(_HERE), "scripts"))
from f273_sat import is_prime  # noqa: E402   (fresh-path primality, same as the ladder used)


def read_model(path):
    """Accept a kissat/cadical `v ...` log, or a bare whitespace-separated list of ints."""
    txt = open(path, encoding="utf-8", errors="replace").read()
    vs = re.findall(r"^v (.*)$", txt, flags=re.M)
    toks = (" ".join(vs) if vs else txt).split()
    pos = set()
    for t in toks:
        try:
            i = int(t)
        except ValueError:
            continue
        if i > 0:
            pos.add(i)
    return pos


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--layout", required=True)
    ap.add_argument("--model", required=True, help="solver log with `v` lines, or a raw model")
    ap.add_argument("--cube", default=None, help="cube file -- checked for consistency")
    ap.add_argument("--out", required=True)
    a = ap.parse_args()

    lay = json.load(open(a.layout, encoding="utf-8"))
    N, pool = lay["N"], lay["pool"]
    base, v = {}, 1
    for half in (0, 1):
        for h in pool:
            base[(half, h)] = v
            v += h

    model = read_model(a.model)
    pairs = [(r, h) for h in pool for r in range(h) if base[(0, h)] + r in model]

    rep = {"N": N, "layout": os.path.abspath(a.layout), "model_file": os.path.abspath(a.model),
           "pairs_residue_modulus": sorted(pairs, key=lambda t: t[1]),
           "k": len(pairs), "moduli": sorted(h for _, h in pairs)}

    # --- cube consistency: the decoded half must satisfy the cube it came from
    if a.cube:
        units = [int(l.split()[0]) for l in open(a.cube, encoding="utf-8") if l.strip()]
        bad = [u for u in units if (u > 0) != (abs(u) in model)]
        rep["cube"] = os.path.abspath(a.cube)
        rep["cube_consistent"] = not bad
        rep["cube_violations"] = bad[:20]

    # --- FRESH-PATH verification of the half
    hit = bytearray(N)
    for r, m in pairs:
        for x in range(r % m, N, m):
            hit[x] = 1
    L = 1
    for _, m in pairs:
        L = L * m // math.gcd(L, m)
    rep["covers_Z_mod_N"] = all(hit)
    rep["lcm"] = L
    rep["lcm_divides_N"] = (N % L == 0)
    # covering Z/N with every modulus dividing N is exactly covering Z
    rep["covers_Z"] = bool(rep["covers_Z_mod_N"] and rep["lcm_divides_N"])
    rep["distinct_moduli"] = len(set(h for _, h in pairs)) == len(pairs)
    rep["two_excluded"] = 2 not in set(h for _, h in pairs)
    rep["all_legal_p_ge_5"] = all(is_prime(2 * m + 1) and 2 * m + 1 >= 5 for _, m in pairs)
    rep["sum_recip"] = sum(1.0 / m for _, m in pairs)
    rep["sum_recip_gt_1"] = rep["sum_recip"] > 1.0
    rep["HARD_HALF_VALID"] = bool(rep["covers_Z"] and rep["distinct_moduli"]
                                  and rep["two_excluded"] and rep["all_legal_p_ge_5"]
                                  and rep.get("cube_consistent", True))

    used = sorted(set(h for _, h in pairs))
    full_pool_note = ("stage 2 searches the OTHER half in pool \\ used; that half MAY hold "
                      "modulus 2 and must itself be a distinct-moduli covering of Z")
    rep["status"] = ("HARD_HALF_ONLY -- NOT an Erdos 273 witness. Stage 1 of 2."
                     if rep["HARD_HALF_VALID"] else
                     "SAT_BUT_VERIFICATION_FAILED -- do not file, investigate the encoder")
    rep["stage2"] = {
        "note": full_pool_note,
        "excluded_moduli": used,
        "command": ("python3 ../scripts/f273_minhalf.py --Ns %d --exclude %s "
                    "--budget 99 --node-cap 400000000 --secs-per-N 3000 "
                    "--out stage2-N%d.json --question-lock "
                    "../erdos273-covering-sat-ladder.json"
                    % (N, ",".join(str(h) for h in used), N)),
        "budget_note": ("--budget 99 disables the density cut: stage 2 is a pure existence "
                        "search, not a minimum-density certificate. Its `found:true` gives the "
                        "second half; `exhaustive:true, found:false` proves this hard half "
                        "cannot be completed and the cube's model must be blocked and the "
                        "cube re-run."),
    }

    with open(a.out, "w", encoding="utf-8", errors="replace") as f:
        json.dump(rep, f, indent=1)
    print(json.dumps({k: rep[k] for k in ("N", "k", "moduli", "sum_recip", "covers_Z",
                                          "HARD_HALF_VALID", "status")}, ensure_ascii=False))
    print("report " + a.out)
    print("STAGE 2: " + rep["stage2"]["command"])
    raise SystemExit(0 if rep["HARD_HALF_VALID"] else 2)


if __name__ == "__main__":
    main()
