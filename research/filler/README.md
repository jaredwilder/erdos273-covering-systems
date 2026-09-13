# THE FILLER LANE — Erdős 273 cube-and-conquer

**What this is.** The box's slack absorber. Every core no other queue is using goes here, and
every unit of work is ONE CUBE, so a kill costs one cube and never a run.

**What it can produce.** A `UNSAT_TO_N` bound at N = 3,960 or N = 360,360 (nonexistence with an
explicit ceiling `lcm | 2N`), or a `SAT_HARD_HALF` — which is **half** of an Erdős 273 witness
and never more than that until stage two closes and the Lean kernel signs it.

---

## The one-screen run

```bash
python3 f273_hardhalf.py  --selfcheck                      # 3/3 MATCH  (must pass first)
python3 f273_hardhalf.py  --N 360360                       # regenerate the 164 MB CNF, ~2.5 min
python3 f273_cube_split.py --N 360360 --cnf cnf/hard-half-only-N360360.cnf
python3 partition_check.py --N 360360 --cnf cnf/hard-half-only-N360360.cnf   # MANDATORY

python3 -c "import json;print('\n'.join(c['cube_id'] for c in json.load(open('cubes/N360360/manifest.json',encoding='utf-8'))['cubes']))" \
  | xargs -P 30 -I{} nice -n 10 bash run_cube.sh 360360 {} 3600 kissat

python3 aggregate.py --N 360360
```

N = 3,960 is already built and split in this directory (439 KB CNF, 72 cubes) — start it with
`bash run_cube.sh 3960 <cube_id> 3600 cadical drat` and the DRAT proofs get checked in place.

---

## The files

| file | job |
|---|---|
| `f273_hardhalf.py` | the hard-half-only encoder. `--selfcheck` reproduces the receipted box exports exactly |
| `f273_cube_split.py` | deterministic cube splitter → `cubes/N<N>/` + manifest |
| `partition_check.py` | **proves** the cubes partition the model space, both arms |
| `mkcube.py` | base CNF + cube units → one standalone DIMACS file, header corrected |
| `run_cube.sh` | run one cube: assemble → solve → drat-trim → checkpoint → clean up |
| `decode_cube_model.py` | decode + independently verify a SAT model; prints the stage-two command |
| `aggregate.py` | cube checkpoints → one rung verdict. Fails closed |
| `smoke_test.py` | 25 s pipeline-shape probe (this PC has no solver binaries) |
| `filler-config.json` | everything the box runner consumes |

---

## Three things that are easy to get wrong

**1. A hard half is HALF.** Every SAT in this lane is a distinct-moduli covering of ℤ drawn
from `H ∩ divisors(N) \ {2}`. Erdős 273 needs **two disjoint** such halves. `SAT_HARD_HALF` is
stage one of two; `decode_cube_model.py` prints the stage-two command and nothing may be
claimed before it closes.

**2. UNSAT is a bound, never a refutation.** `UNSAT_TO_N` says no covering system of ℤ has
distinct moduli `p−1` (`p ≥ 5`) with `lcm | 2N`. The problem quantifies over an infinite
modulus pool. No finite N settles the negative branch. Ever.

**3. A killed process is not a timeout.** Exit 137/143 is recorded as `STOPPED_NO_VERDICT`.
This campaign refiled four receipts over exactly this distinction on 2026-09-02.

And one more: **`aggregate.py` only reports `UNSAT_TO_N` when every cube is decided.** A
partial sweep is not a partial bound.

---

## Provenance — this encoder is a reconstruction, and here is its proof

The `--mode hardhalf` that produced `receipts/receipt-export-hardhalf-N{27720,83160,360360}.json`
lived on the Scaleway box and went away with it; the committed `scripts/f273_sat.py` has only
`symmetric | fixedhalf | onehalf`. `f273_hardhalf.py` re-implements the mode and
`--selfcheck` reproduces all three receipts on **vars, x_vars, clauses and literals** — 3/3,
no tolerance. One detail was recovered from the counts rather than from code: the receipted
metadata carries `translate_half0` **and** `r3_eq_0` as separate flags, and the clause counts
demand six unit clauses where the two rules together need four, so the box emitted the two
modulus-3 units twice. Duplicate units are inert; they are replicated so the bytes match.

`cnf/hard-half-only-N3960.layout.json` has a sibling `*.onehalf-compat.layout.json` whose only
difference is `mode: "onehalf"`. That lets the campaign's own, independently written
`scripts/decode_model.py` read a hard-half model **unmodified** — two decoders, one instance,
no shared decoding code.
