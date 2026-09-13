#!/usr/bin/env python3
"""Exact settlement of the HALF-B-ALONE instance at one N, with kissat.

  emit CNF -> kissat -> decode model -> INDEPENDENT re-verification -> receipt

SAT  => a covering of Z with distinct moduli from H\\{2}, lcm | N.  That is half B.
UNSAT=> no such covering exists with lcm | N.  A bound with an explicit ceiling,
        NEVER a refutation of Erdos 273.
TIMEOUT => establishes nothing.

Usage: python solve_halfB.py --N 27720 --secs 3600 --out out/sat-N27720 \
         --question-lock <path> [--include-2]
"""
import json
import os
import subprocess
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from verify273 import report as verify_report  # noqa: E402


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
    a = sys.argv
    N = int(a[a.index("--N") + 1])
    secs = int(a[a.index("--secs") + 1]) if "--secs" in a else 3600
    out = a[a.index("--out") + 1]
    qlock = a[a.index("--question-lock") + 1] if "--question-lock" in a else "(none)"
    inc2 = "--include-2" in a

    cnf = out + ".cnf"
    t0 = time.time()
    rc = subprocess.run([sys.executable, os.path.join(os.path.dirname(os.path.abspath(__file__)), "emit_halfB.py"),
                         str(N), cnf] + (["--include-2"] if inc2 else []),
                        capture_output=True, text=True)
    print(rc.stdout.strip(), flush=True)
    layout = json.load(open(cnf + ".layout.json", encoding="utf-8"))
    emit_secs = time.time() - t0

    solver = a[a.index("--solver") + 1] if "--solver" in a else "kissat"
    if solver == "cadical":
        cmd = ["timeout", str(secs), "cadical", "--no-binary", cnf, out + ".drat"]
    else:
        cmd = ["kissat", "--time=%d" % secs, cnf]
    print("%s starting N=%d vars=%d clauses=%d cap=%ds"
          % (solver, N, layout["n_vars"], layout["n_clauses"], secs), flush=True)
    t1 = time.time()
    k = subprocess.run(cmd, capture_output=True, text=True)
    solve_secs = time.time() - t1
    log = out + "." + solver + ".txt"
    with open(log, "w", encoding="utf-8") as f:
        f.write(k.stdout)
        f.write(k.stderr)

    res = {10: "SAT", 20: "UNSAT"}.get(k.returncode, "UNKNOWN_TIMEOUT")
    rec = {"instance": "half-B-alone", "N": N, "pool": layout["pool"], "pool_size": len(layout["pool"]),
           "reciprocal_sum_S_B": layout["S"], "need": 1.0, "include_2": inc2,
           "n_vars": layout["n_vars"], "n_clauses": layout["n_clauses"],
           "solver": solver, "cap_seconds": secs, "emit_seconds": round(emit_secs, 1),
           "solve_seconds": round(solve_secs, 1), "exit_code": k.returncode,
           "result": res, "question_lock": qlock}

    if res == "SAT":
        true_vars = set()
        for line in k.stdout.splitlines():
            if line.startswith("v "):
                for t in line[2:].split():
                    v = int(t)
                    if v > 0:
                        true_vars.add(v)
        pairs = []
        for key, v in layout["x"].items():
            if v in true_vars:
                m, r = key.split(",")
                pairs.append((int(r), int(m)))
        pairs.sort(key=lambda t: t[1])
        rec["pairs"] = pairs
        rec["verification"] = verify_report(pairs, require_H=True, exclude_2=(not inc2),
                                            label="kissat model N=%d" % N)
        rec["human"] = "; ".join("%d mod %d" % (r, m) for r, m in pairs)
        rec["doubled_odd_lift"] = ["%d mod %d" % (2 * r + 1, 2 * m) for r, m in pairs]
        if rec["verification"]["VERDICT"] == "COVERING_VERIFIED":
            print("WITNESS FOUND N=%d -- HALF B EXISTS" % N, flush=True)
        else:
            rec["result"] = "SAT_BUT_VERIFICATION_FAILED"
            print("BUG: kissat SAT but independent check failed at N=%d" % N, flush=True)
    elif res == "UNSAT":
        rec["meaning"] = ("No covering system of Z with distinct moduli from H minus {2} has lcm dividing "
                          "%d. Bounded nonexistence with an explicit ceiling. NOT a refutation of Erdos 273."
                          % N)
        print("UNSAT N=%d in %.1fs" % (N, solve_secs), flush=True)
    else:
        rec["meaning"] = "Cap expired. Establishes nothing."
        print("UNKNOWN/TIMEOUT N=%d after %.1fs" % (N, solve_secs), flush=True)

    with open(out + ".receipt.json", "w", encoding="utf-8") as f:
        json.dump(rec, f, indent=1)
    print("receipt -> %s.receipt.json  result=%s" % (out, rec["result"]), flush=True)


if __name__ == "__main__":
    main()
