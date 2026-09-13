#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Assemble  base CNF + one cube  ->  a standalone DIMACS file, header corrected.

WHY NOT ASSUMPTIONS
-------------------
`kissat` has no CLI assumption interface and `cadical` reads cubes only inside a `p inccnf`
file, which would mean one 164 MB copy of the base per shard.  Appending the cube's units and
rewriting the `p cnf` line is solver-agnostic (kissat, cadical, DRAT output, drat-trim all
work unchanged) and costs one streamed copy that the runner deletes when the cube finishes.

Write the output to tmpfs (`/dev/shm`) on the box: at N=360360 the file is ~164 MB, so 32
concurrent cubes hold ~5.3 GB of the 251 GB.  The runner unlinks each one immediately.

    python3 mkcube.py --base cnf/hard-half-only-N360360.cnf \\
                      --cube cubes/N360360/cube-c00042.cube \\
                      --out /dev/shm/hh360360-c00042.cnf

Stdlib only, streaming, constant memory.
"""
from __future__ import annotations
import argparse, os, sys


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--base", required=True)
    ap.add_argument("--cube", required=True)
    ap.add_argument("--out", required=True)
    a = ap.parse_args()

    with open(a.cube, "rb") as f:
        cube = f.read()
    n_units = sum(1 for line in cube.split(b"\n") if line.strip())

    with open(a.base, "rb") as src:
        first = src.readline().decode("ascii").split()
        if len(first) != 4 or first[0] != "p" or first[1] != "cnf":
            raise SystemExit("base is not a DIMACS `p cnf` file: %r" % (" ".join(first),))
        nv, ncl = int(first[2]), int(first[3])
        tmp = a.out + ".partial"
        last = b"\n"
        with open(tmp, "wb") as out:
            out.write(("p cnf %d %d\n" % (nv, ncl + n_units)).encode("ascii"))
            while True:
                chunk = src.read(1 << 22)
                if not chunk:
                    break
                out.write(chunk)
                last = chunk[-1:]
            if last != b"\n":                 # a base without a trailing newline would glue
                out.write(b"\n")              # its last clause onto the first cube unit
            out.write(cube)
    os.replace(tmp, a.out)      # a killed assembly is never mistaken for a finished CNF
    sys.stdout.write("%s vars=%d clauses=%d (+%d cube units)\n"
                     % (a.out, nv, ncl + n_units, n_units))


if __name__ == "__main__":
    main()
