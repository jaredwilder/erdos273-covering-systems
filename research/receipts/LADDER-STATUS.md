# LADDER STATUS — Erdős 273 symmetric two-halves (live, 15:28Z)

`NEED = 2`. Curve: `DENSITY-CURVE.md`. Byte integrity: `MANIFEST.md` (**12 instances, 12 intact,
0 corrupt**). Decode a model with `decode_model.py` + the rung's `.layout.json`; spec: `ENCODING.md`.

## ⚠ UNCLAIMED AND READY — highest value first

| N | slack S−2 | vars | clauses | MB | sha256 | note |
|---|---|---|---|---|---|---|
| **360,360** | **+0.2114** | 1,693,521 | 3,260,809 | 389 | `e407d64bdccf0e39` | **BEST SLACK under the 2M cap. By the density curve this is the likeliest home for a witness — take it first.** |
| **277,200** | +0.1728 | 1,092,798 | 2,193,418 | 273 | `4576590f627cea84` | second best |
| **166,320** | +0.1658 | 1,603,929 | 2,738,363 | 184 | `b8760846b1ea230e` | |
| **221,760** | +0.1474 | 834,076 | 1,694,471 | 200 | `1cf7ecfdc24a5c92` | |

## Claimed

| N | slack | owner |
|---|---|---|
| 27,720 | +0.0873 | peer (kissat+cadical) · me (`kissat --unsat`) |
| 50,400 | +0.0002 | peer (kissat+cadical) · me (`kissat --unsat`) |
| 55,440 | +0.1197 | **me, sole** — cap expires 16:04Z |
| 83,160 | +0.1333 | **me, sole** — cap expires 16:04Z |
| 110,880 | +0.1394 | **peer, sole** |
| 138,600 | +0.1404 | **peer, sole** |

Building: `332,640` (+0.1860), ETA ~15:45Z.

## NOT emitted — with the measurement that excludes it

| N | S(N) | vars | why not |
|---|---|---|---|
| 720,720 | 2.2470 | **2,547,328** | 27 % over the 2M soft cap; ≈1.1 GB. Sized, not built — say the word. |
| 1,441,440 | 2.2671 | 7,034,867 | 3.5× cap |
| 2,162,160 | 2.2945 | 18,421,240 | 9× cap |

## No CNF at all — UNSAT by density, nothing to solve

`3,960 · 5,040 · 7,920 · 10,080 · 20,160 · 25,200 · 45,360` — `S(N) ≤ 2`, so two disjoint
distinct-moduli covering systems cannot exist at that ceiling. Reciprocal-mass proof, **no solver
invoked**. Their `READY-N<N>.txt` reads `NO-CNF reason=UNSAT_BY_DENSITY`. The entire
`fixed-selfridge-half` formulation dies the same way at **every** N through 720,720 (needs
`S > 2.5556`, first reachable near `N ≈ 1.6·10¹¹`).

## Verdict semantics — binding

* **UNSAT at N** → no covering system of ℤ with distinct moduli `p−1` (`p ≥ 5`) **all dividing 2N**.
  Bound with an explicit ceiling, filed `COMPUTED_BOUNDED`. **Never a refutation of Erdős 273.**
* **SAT at N** → `WITNESS_UNVERIFIED` until independently re-verified **and** Lean-kernel checked.
* **TIMEOUT** → establishes nothing. Not weak evidence of UNSAT.
* Two paths disagreeing on the same sha256 = a bug in one of them. Report it; do not prefer either.

## Measured, so you can trust the caps

CPU-vs-wall audit at 15:13Z (box load 44 on 32 cores): all four of my nice-10 solvers showed
`cpu_secs == elapsed_secs` to within 1 s. Nice 10 is not being starved; a `--time=N` cap delivers
≈N seconds of real CPU. Receipt: `f273_cpu_check.txt`.
