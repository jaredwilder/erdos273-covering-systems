# FIXER REPORT — erdos:273, compiled local search for HALF B — **FINAL**

## NO WITNESS FOUND. `NO_WITNESS_FOUND_LOCAL_SEARCH`.

**Terminated early on coordinator order** (box reallocated to the factory: decomposer sweep, ladder,
orphan-declaration kernel pass). **Processes I left behind on the box: ZERO** — verified by `ps`
after the kill; every peer/factory process (`f273_minhalf.py`, the peer's
`cadical … hard-half-only-N27720.cnf`, `leaf_prove.py`, the Lean/lake sweep) was left running and
untouched.

**Question lock:** `oracle/ledger/question-locks/erdos273-covering-sat-ladder.json` — passed on every
launch command and written into the header of every searcher log
(`# question-lock: /root/peer/anneal273/erdos273-covering-sat-ladder.json`). A copy sits beside the
receipts at `oracle/evidence/msl-machine/campaigns/erdos273-sat-2026-09-02/anneal/`.

**What was searched.** Half B alone: *a covering system of ℤ with distinct moduli drawn from
`H \ {2}` where `H = {(p−1)/2 : p prime ≥ 5}`, all moduli dividing N.* This needs only
`S_B(N) = Σ_{m∈H, m|N, m≠2} 1/m > 1`, satisfied on every rung with 36–79 % slack. **This is a
different question from the peer's symmetric-two-halves instance** (`NEED = 2`, slack 4–15 %). Do
not merge the two sets of receipts.

---

## 1. CONTROLS — BOTH MANDATORY CONTROLS PASSED, 16/16, INDEPENDENTLY RE-VERIFIED

| Control | Pool | Density | Result |
|---|---|---|---|
| **N = 180**, `H ∩ div(180)` **including 2** = `{2,3,5,6,9,15,18,20,30,36,90}` | 11 | 1.5556 | **PASS — covering found from random starts, 8/8 seeds, < 0.01 s each (max 1 iteration)** |
| **N = 144**, `{3,4,6,8,9,12,16,18,24,36,48}` (Krukenberg, 23/18) | 11 | 1.2778 | **PASS — covering found, 8/8 seeds, ≤ 154 iterations each** |

Control 1 returns coverings that are **not** Selfridge's layout — e.g. seed 3:
`1 mod 2; 0 mod 3; 0 mod 5; 4 mod 6; 5 mod 9; 2 mod 15; 8 mod 18; 8 mod 20; 26 mod 30; 2 mod 36; 74 mod 90`.
`verify273.py` — independent Python sharing no code with the C searcher — confirms 11 distinct
moduli, every `2m+1 ∈ {5,7,11,13,19,31,37,41,61,73,181}` prime, lcm 180, **0 uncovered**. The same
verifier independently re-confirms Selfridge's published half. Both controls also pass on the
weighted build. Receipt: `anneal/controls/receipt-CONTROLS.json` (`ALL_CONTROLS_PASS: true`).

**Third control, on the SAT path** (`anneal/controls/satctl-N180.receipt.json`): the CNF emitter →
kissat → model decoder → verifier chain was run end-to-end on N = 180 and returned **SAT** with a
model that decodes to a genuine, independently verified covering. **The encoder cannot silently
manufacture UNSAT.** This matters: it is the control that would have to pass before any UNSAT from
this pipeline could be believed. No UNSAT was obtained, so nothing rests on it — but it is receipted.

**The searcher hunts. The plateau below is not a broken searcher.**

---

## 2. THE LEDGER — cores × seconds × best uncovered, per N

`result` for every row: **`NO_WITNESS_FOUND_LOCAL_SEARCH`**. Machine-readable:
`anneal/logs/LEDGER.json`.

| N | \|pool\| | `S_B` | arms | **core-seconds** | **best uncovered** | % of N | restarts | iterations |
|---|---|---|---|---|---|---|---|---|
| 27,720 | 42 | 1.5873 | 3 | 2,100 | **570** | 2.056 % | 304 | 313,596,928 |
| 55,440 | 51 | 1.6197 | 2 | 960 | **870** | 1.569 % | 71 | 91,299,840 |
| 83,160 | 57 | 1.6333 | 3 | 2,100 | **789** | 0.949 % | 101 | 144,651,264 |
| 110,880 | 57 | 1.6394 | 1 | 60 | 1,463 | 1.319 % | 1 | 2,868,224 |
| 138,600 | 63 | 1.6404 | 1 | 60 | 1,785 | 1.288 % | 1 | 2,806,784 |
| 166,320 | 70 | 1.6658 | 2 | 960 | **971** | 0.584 % | 22 | 39,860,224 |
| 221,760 | 67 | 1.6474 | 1 | 60 | 2,664 | 1.201 % | 0 | 1,606,656 |
| 277,200 | 73 | 1.6728 | 1 | 60 | 2,658 | 0.959 % | 0 | 1,177,600 |
| 332,640 | 79 | 1.6860 | 3 | 2,100 | **1,430** | 0.430 % | 26 | 52,002,816 |
| 360,360 | 78 | 1.7114 | 1 | 60 | 4,589 | 1.273 % | 0 | 838,656 |
| 720,720 | 95 | 1.7470 | 1 | 60 | 6,938 | 0.963 % | 0 | 740,352 |
| 2,162,160 | 131 | 1.7945 | 3 | 1,624 | **8,787** | 0.406 % | 1 | 6,632,448 |

**Total annealer spend: 10,204 core-seconds (2.83 core-hours), 658 M iterations, 526 random
restarts.** Rows with 60 core-seconds are reconnaissance only — one seed, one minute — and are the
weakest rows in the table; treat them as unexplored, not as measured floors.
Exact-solver spend: a further ≈ 3,100 core-seconds (§4). Peak concurrency 12 cores of 32, `nice -n 8`.

**⛔ `NO_WITNESS_FOUND_LOCAL_SEARCH` IS NOT A BOUND.** It is a statement about my searcher and the
budget above. It is not evidence that half B does not exist at these N, and it is not a result about
Erdős 273.

---

## 3. THE ONE MEASUREMENT WORTH KEEPING — a seed-stable floor of exactly 570 at N = 27,720

**Three independent arms — recon seed 7 (60 s), plain seed 101 (1,080 s), weighted seed 201
(840 s) — all stopped at the identical value 570**, across **304 full random restarts and 314 million
iterations**. A local-search floor that is *numerically identical* across independent restarts and
two different objective functions is the fingerprint of a combinatorial bound rather than of a stuck
searcher. It is 2.06 % of N — **nowhere near "one modulus short."**

Two things that would have explained it cheaply, and do not:

1. **It is not the big moduli being wasted.** The seven largest moduli at N = 27,720
   (1155 … 27720) can between them cover at most 83 residues. The 570-point deficiency lives in the
   small-modulus layer, where `H` is missing **4, 7, 10, 12, 13** — and where the 2-adic ladder is
   broken: `8 ∈ H` but `4 ∉ H` (9 = 3²), `16 ∉ H` (33), `12 ∉ H` (25), `24 ∉ H` (49), `40 ∉ H` (81).
   Krukenberg's min-modulus-3 covering needs exactly 4, 12, 16, 24.
2. **It is NOT a counting obstruction.** I checked the per-prime-power density condition on every
   rung: for each prime power `q | N`, moduli coprime to `q` give free density to all `q` classes,
   and the rest is targetable. **Zero counting obstructions at any `q`, at any N on the ladder**
   (`anneal/controls/class-density-conditions.txt`, generated by `anneal/src/class_density.py`).
   The tightest condition anywhere is `mod 9` at N = 27,720: every class gets 0.6192 free and needs
   0.3808 more, against 8.71 of targetable mass. Enormous slack.

**So if half B does not exist at these N, it fails for a genuine combinatorial reason, not a density
one.** That is the honest content of the plateau, and it is consistent with the solver evidence in §4.

**Structure of the residual** (best state, N = 27,720, 570 uncovered): diffuse — 5 of 8 classes
mod 8, 5 of 9 mod 9, 4 of 5 mod 5, all 7 mod 7, 10 of 11 mod 11. No single small modulus explains it.

**Weighted vs plain (A/B, matched N and budget): no separation.** At 27,720 both pinned 570; at
83,160 plain 789 vs weighted 795; at 166,320 weighted 971 vs plain 1,069; at 332,640 plain 1,430 vs
weighted 1,549. PAWS-style point weighting bought nothing here. Reported because it is a negative
result about the method, not about the mathematics.

---

## 4. THE EXACT LANE — no verdict obtained, and that is itself informative

Because a local-search floor is not a bound, I encoded half-B-alone as CNF (cover clause per residue
of ℤ/N; Sinz sequential at-most-one per modulus; **no at-least-one — an unused modulus is allowed,
which is WLOG and keeps any UNSAT honest**) and ran real solvers.

| N | vars | clauses | solver | cap | outcome |
|---|---|---|---|---|---|
| 180 (control, incl. 2) | 457 | 838 | kissat | 120 s | **SAT in 0.0 s, model verified** |
| **3,960** | 5,648 | 12,377 | kissat | 600 s | **UNKNOWN — cap expired** |
| 3,960 | 5,648 | 12,377 | cadical (+DRAT) | 4,500 s | **no verdict — lane ended at reallocation, ~420 s in, partial 9.5 KB DRAT** |
| 3,960 | 5,648 | 12,377 | kissat (2nd) | 4,200 s | **no verdict — lane ended at reallocation, ~300 s in** |
| 7,920 | 14,540 | 29,665 | kissat | 900 s | stopped at ~600 s to redirect cores to the base rung |
| 55,440 | 239,481 | 414,534 | kissat | 3,000 s | **UNKNOWN — cap expired at 846.7 s** |
| 83,160 | 191,795 | 370,710 | kissat | 3,600 s | stopped at ~330 s (reallocation) |

Receipts: `anneal/logs/sat-N3960.receipt.json`, `sat-N55440.receipt.json`,
`controls/satctl-N180.receipt.json`. Each `UNKNOWN_TIMEOUT` receipt carries
`"meaning": "Cap expired. Establishes nothing."`

> **The load-bearing observation: a 5,648-variable / 12,377-clause CNF defeated kissat for 600 s.**
> Instances that size are normally dispatched in milliseconds. Together with the seed-stable 570 and
> the absence of any counting obstruction, this says the combinatorial core of half B is genuinely
> hard — which is the most useful thing this session produced, and it is a statement about
> *difficulty*, not about *existence*.

**Honesty on the two 3,960 lanes:** both terminated without writing a receipt and without emitting
`s SATISFIABLE` / `s UNSATISFIABLE`. **I did not establish why.** They establish nothing. The
N = 3,960 rung of half B remains **open and unsettled** — and it is the cheapest decisive experiment
left on the board.

> **CANDIDATE MECHANISM — flagged as unproven, recorded so the next session does not repeat it.**
> Both lanes were launched through an `ssh` wrapper that was later reaped client-side, and both died
> at roughly that time despite `nohup`. If SIGHUP on connection teardown reached the solver through
> the `sh -c` → `python` → `timeout` → `cadical` chain, that would explain a silent death with a
> partial DRAT and no receipt. **This is a hypothesis, not a diagnosis — I did not test it, and the
> timing evidence is not clean enough to call it.** The cheap defence next time is to detach properly
> (`setsid`, or `systemd-run --scope`) rather than relying on `nohup` through a nested `sh -c`, and to
> have the solver wrapper write a `STARTED`/`EXITED` stamp so a silent death is distinguishable from
> a cap expiry in the receipt itself.

**Independent cross-check, already in flight and left running:** the peer's
`hard-half-only-N27720.cnf` carries **the identical 42-modulus pool** to my N = 27,720 instance —
same mathematical question, independently written encoding, different solver (cadical with DRAT).
Note the divisibility direction: **UNSAT at 27,720 implies UNSAT at 3,960** (any covering with
`lcm | 3960` also has `lcm | 27720`), so the peer's run subsumes my base rung. If the two paths ever
disagree on the same question, one has a bug and neither should be preferred.

---

## 5. WHAT WAS AND WAS NOT ESTABLISHED

* **Nothing was established about Erdős 273.** No half B. No half A (never reached — half A is only
  searched once B exists). No `WITNESS-273.json`. No bound in either direction.
* Both mandatory known-answer controls **passed**, plus a third control on the SAT encoder.
* The measured content is: (a) a seed-stable local-search floor at ~0.4–2 % uncovered across the
  ladder, sharpest and most reproducible at N = 27,720 where it is exactly 570; (b) **no counting
  obstruction exists at any prime power on any rung** — so the plateau is real combinatorics;
  (c) modern CDCL does not dispatch even the 5.6 k-variable base rung in 10 minutes.
* **The single highest-value next move** is not more annealing — the A/B showed the method is
  saturated. It is to **settle N = 3,960 exactly** (5,648 vars) with cadical + DRAT and an hour of
  wall clock, and to let the peer's N = 27,720 cadical run finish. SAT there ends the hunt for half B
  immediately; UNSAT there is the first quantitative fact anyone has recorded about this problem, with
  the ceiling stated as *"no covering of ℤ with distinct moduli from `H \ {2}` has lcm dividing N"* —
  **never** as a refutation of Erdős 273.

---

## 6. FILES

Receipts, code and logs: **`oracle/evidence/msl-machine/campaigns/erdos273-sat-2026-09-02/anneal/`**

| path | what |
|---|---|
| `erdos273-covering-sat-ladder.json` | the question lock, copied beside the receipts |
| `src/anneal273.c` | compiled searcher: coverage-count array + explicit uncovered list, O(N/m + \|U\|) delta-evaluated best-residue move, tabu on modulus, WalkSAT noise, perturbation, random restart, `r₃ ≡ 0` symmetry break, `--question-lock` |
| `src/anneal273w.c` | + PAWS point weights on the uncovered set |
| `src/verify273.py` | independent exact verifier; `--selfcheck` re-verifies Selfridge's half |
| `src/emit_halfB.py` | CNF emitter, half-B-alone (cover + Sinz AMO, no at-least-one) |
| `src/solve_halfB.py` | emit → kissat/cadical → decode → independent verify → receipt |
| `src/class_density.py` | per-prime-power counting conditions |
| `controls/receipt-CONTROLS.json` | 16/16 control witnesses, all re-verified — `ALL_CONTROLS_PASS: true` |
| `controls/satctl-N180.receipt.json` | SAT-pipeline encoder control (SAT + verified model) |
| `controls/class-density-conditions.txt` | **0 counting obstructions**, whole ladder |
| `logs/LEDGER.json` | cores × seconds × best-uncovered per N, machine-readable |
| `logs/*.log`, `logs/*.best.json` | every trajectory and every best state found |

Remote scratch `/root/peer/anneal273/` is left in place with its `out/` directory; **no processes of
mine remain on the box.**
