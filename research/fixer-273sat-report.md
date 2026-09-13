# FIXER REPORT — Erdős 273, SAT ladder (2026-09-02)

> # NO WITNESS FOUND. NO STATEMENT DEFECT. THE LADDER IS NOT CLOSED.
>
> # ERDŐS 273 REMAINS OPEN. What was established: a set of **bounded nonexistence facts** with explicit
> # ceilings, two **exhaustively-certified minimum-density values**, and the exact reduction that makes
> # the problem finite at every ceiling — none of which proves or refutes the conjecture.

**Question lock:** `oracle/ledger/question-locks/erdos273-covering-sat-ladder.json` — passed on every solver
launch, copied beside the remote receipts.
**Campaign:** `oracle/evidence/msl-machine/campaigns/erdos273-sat-2026-09-02/`
**Box:** Scaleway 32-core, shared. My footprint never exceeded **4 solver processes at `nice 10`** (no master
receipt in `/root/peer/search289`, so the 4-process cap held all night); builders ran at `nice 19`.
**Tooling, receipted:** python 3.14.4 · `python-sat==1.9.dev15` (installed this session) · `kissat 4.0.3-2`
(installed this session) · `cadical 2.1.3` · `drat-trim` (built from source this session) ·
Mathlib `leanprover/lean4:v4.31.0-rc1` prebuilt at `/root/mathlib4`.

---

## STEP 0 — STATEMENT FIREWALL → **NO DEFECT. THE PREDICATE IS THE INTENDED ONE.**

Source: `.../FormalConjectures/ErdosProblems/273.lean` + `.../FormalConjecturesForMathlib/NumberTheory/CoveringSystem.lean`.

```lean
theorem erdos_273 : answer(sorry) ↔ ∃ c : StrictCoveringSystem ℤ, ∀ i, ∃ (p : ℕ), p.Prime ∧ 5 ≤ p ∧
    c.moduli i = Ideal.span {↑(p - 1)}
```

| axis | what the Lean actually says | verdict |
|---|---|---|
| finite index? | `ι : Type` with `[Fintype ι]` | **finite** |
| distinct moduli? | `injective_moduli : moduli.Injective`; in ℤ, `span{m}=span{m'} ↔ m=±m'`, all `p−1>0` | **exactly "the mᵢ are pairwise distinct"** |
| every integer covered? | `⋃ i, {residue i} + (moduli i : Set ℤ) = univ` | **all of ℤ** |
| **⊆ {p−1} or = {p−1}?** | `∀ i, ∃ p, …` — a **membership condition per modulus** | **SUBSET, not equality. NOT vacuous.** |
| `ne_bot` / `ne_top` | `m ≠ 0` / `m ≠ ±1`; every `p−1 ≥ 4` for `p ≥ 5` | free |
| `(p−1 : ℕ)` truncation | guarded by `5 ≤ p` | safe |

Had the moduli condition been *equality* with the infinite set `{p−1 : p ≥ 5}`, the statement would be
vacuously false against `Fintype ι` and this report would have stopped at `STATEMENT_DEFECT`. **It is not.**

**ℕ-vs-ℤ sibling.** `erdos_273.variants.three` is over `StrictCoveringSystem ℕ`, where `Ideal.span {m} = m·ℕ`,
so a "coset" is the one-sided AP `{a, a+m, …}`, *not* a congruence class. Proved both directions rather than
assumed: **(ℤ⇒ℕ)** take residues in `[0,m)`; then `(a+mℤ) ∩ ℕ = a+mℕ`. **(ℕ⇒ℤ)** the union of the classes is
periodic with period `L=lcm(mᵢ)`; covering every `n ≥ 0` forces a full period `[0,L)`, hence all of ℤ.
**The witness object is the same.** The earlier pricing report called this a "statement-firewall defect";
**that was overstated and is corrected here** — a cosmetic upstream inconsistency worth a PR, not a defect.

---

## STEP 1 — THE REDUCTION, VERIFIED IN CODE

Every `p−1` (`p ≥ 5` prime) is **even**, so a class `a mod m` lies wholly inside one parity class.
With `m = 2h`, `n = 2t+ε`, `a = 2r+ε`: `2t+ε ≡ 2r+ε (mod 2h) ⟺ t ≡ r (mod h)`.
**Verified as a set identity** for every `h ∈ [2,40)`, every residue, every `n ∈ [−400,400)` — equal in all cases.

> ### **Erdős 273 ⟺ `H = {(p−1)/2 : p prime ≥ 5}` contains TWO DISJOINT distinct-moduli covering systems of ℤ.**

`H = 2,3,5,6,8,9,11,14,15,18,20,21,23,26,29,30,33,35,36,39,41,44,48,50,…`
(absent below 60: 1,4,7,10,12,13,16,17,19,22,24,25,27,28,31,32,34,37,38,40,42,43,45,46,47,49,52,55,57,58,59)

Lifting a half-space covering by `(r,h) ↦ (2r+ε, 2h)` covers **exactly** parity class `ε` — confirmed mod 360.

### Known-answer controls — all passed before any ladder rung was believed

| control | result |
|---|---|
| Selfridge's half at N=180, exhaustive DFS | found in **14 nodes**: `2:0 3:1 5:3 6:5 9:0 15:0 18:3 20:11 30:9 36:33 90:87`; doubles to `{4,6,10,12,18,30,36,40,60,72,180}` = `p−1` for `p ∈ {5,7,11,13,19,31,37,41,61,73,181}` — all prime, all ≥5, all dividing 360 |
| same via the **SAT pipeline** | SAT in **0.07 s**, a *different* valid covering, independently re-verified |
| same via the **peer-facing path** (`kissat` binary → `decode_model.py` + layout json only) | reproduced, `half0_covers_Z: true` |
| **two-half machinery**, p≥3 admitted (h=1) | reconstructed the **settled `variants.three` object**: 12 distinct moduli, lcm 360, `p ∈ {3,5,…,181}` — and the p≥5 gate **correctly refused it** (one modulus has p=3) |

---

## THE DENSITY LAW (`NEED = 2`) — proved here, kills rungs with no solver

A distinct-moduli covering of ℤ has `Σ1/m > 1` **strictly** (≥1 by density; equality is an exact cover,
impossible for ≥2 distinct moduli by Mirsky–Newman). Two **disjoint** such systems need `S(N) > 2`, where
`S(N) = Σ_{h ∈ H, h|N} 1/h`. Any finite covering has `lcm = L` with every modulus dividing `L`, so restricting
to `h | N` is **WLOG for a witness with `lcm | 2N`** — the ladder is a *complete stratification*, not a heuristic.

**Dead by density alone — no solver invoked, no CNF exists:**
`N = 3,960 · 5,040 · 7,920 · 10,080 · 20,160 · 25,200 · 45,360` (S = 1.863 … 1.992).
**Two of the five rungs named in the brief — 3,960 and 7,920 — are dead on arrival.**
`N = 27,720` is the **smallest rung at which the question is even askable.**

**The entire `fixed-selfridge-half` formulation is dead the same way at every N through 720,720.** Pinning
Selfridge's 11 moduli spends 1.5556, so the free half needs `S(N) > 2.5556`, first reachable near `N ≈ 1.6·10¹¹`.
**The brief's instructed split is provably the wrong one at any tractable N** — which is why all compute went
to the symmetric formulation.

**The ceiling.** `S(N) ≈ 2·log log N`, doubly logarithmic: 2.087 at 27,720 → 2.211 at 360,360 → 2.294 at
2.16·10⁶ → 2.465 at 3.7·10⁸ → **2.980 at 4·10²¹**. Selfridge's *single* half runs at 1.5556 (55.6 % slack);
two such halves would need `S ≈ 3.1`, **not reachable at any N**. Any witness must be **far more
reciprocal-efficient than the only comparable construction in the literature.**

### ⛔ RETRACTION — the "Krukenberg 4/3 floor"

Mid-session I published a gate `NEED_KRUK = 7/3` (hard half ≥ 4/3, 2-half > 1) and wrote in capitals that the
entire emitted ladder was "dead by theorem". **WITHDRAWN IN FULL — the 4/3 floor is FALSE.** Distinct-moduli
coverings with least modulus 3 have reciprocal sum arbitrarily close to 1 (FFKPY 2007, via Guy F13), and
**Krukenberg's own ℤ/144 system is itself a counterexample** — which I then verified with my own code:

```
{[2,3],[0,4],[1,6],[2,8],[0,9],[3,12],[6,16],[3,18],[6,24],[33,36],[46,48]}
covers ℤ/144: True · 11 distinct moduli · least modulus 3 · Σ1/m = 23/18 = 1.2778 < 4/3
```

I had flagged the bound "unverified" when I used it. **That was not sufficient** — a capitalised conclusion
must never rest on an unchecked borrowed bound. Retraction box published in `DENSITY-CURVE-EXTENDED.md`.
**Only `NEED = 2`, proved here, survives.**

---

## THE MINIMUM-DENSITY MACHINE (B&B) — and its controls

`D(N)` := minimum `Σ1/h` over distinct-moduli coverings of ℤ drawn from `H ∩ divisors(N)` **with 2 excluded**
(the halves are disjoint, so only one holds modulus 2; the other has least modulus ≥ 3).
Since the 2-half needs `>1`: **`S(N) ≤ 1 + D(N)` ⟹ the rung is UNSAT, provably, with no solver.**
The `{2,3}`-excluded variant is a refinement, not a second necessary condition: `D_{2,3} ≥ D_2`, so the `{2}`
bound already covers the case where 3 sits with 2.

**Both known-answer controls passed EXHAUSTIVELY** — the licence for any `D(N)` claim:

| control | pool | found | density | nodes | s | exhaustive |
|---|---|---|---|---|---|---|
| (a) N=180, full pool | `H ∩ div(180)`, 11 moduli | **Selfridge's half** | **14/9 = 1.55556** | 63,135,084 | 67.2 | **YES** |
| (b) ℤ/144, Krukenberg pool | `{3,4,6,8,9,12,16,18,24,36,48}` | **his system** | **23/18 = 1.27778** | 46,558,529 | 44.7 | **YES** |

Both exceeded the bar: each **exhausted**, converting "found" into an exact minimum —
**`D(180) = 14/9` and `D(144, Krukenberg pool) = 23/18`, proved.** Same code path as the live runs; only
`--pool` differs in (b), whose `all_legal: false` is correct (4, 12, 16, 24, 48 are not `(p−1)/2`).

**Standing rule, applied without exception: a B&B run is decisive ONLY when it reports `exhaustive: true`.**
A node-cap or deadline hit is `INCONCLUSIVE_NODE_CAP` and proves nothing in either direction.

### THE BOUND CERTIFICATE — implemented, and it does not scale

The kernel-checkable form is the **branch tree itself**: each internal node fixes the least uncovered cell `c`
and branches on which modulus covers it (residue then **forced** to `c mod h`); each leaf is closed by an
explicit inequality

```
remaining_mass := budget − density_so_far   <   uncovered_count / N
```

sound because a class of modulus `h` covers exactly `N/h` cells of ℤ/N, so any completion must supply at least
`uncovered_count / N` of reciprocal mass. Leaves may instead close by modulus exhaustion. Emitted as
`{node: {cell, fix:[h,r], children}} | {leaf: {uncovered_count, remaining_mass, inequality}}`.

> **⛔ MEASURED RESULT: THE TREE IS NOT RENDERABLE.** On **control (b) — an 11-modulus pool** — the tree has
> **19,942,710 leaves and 627,459,517 bytes**, against the ~10k-leaf threshold for a Lean rendering. It also
> hit the leaf cap (`tree_overflow: true`), so even that file is **truncated and is NOT a complete
> certificate**. The live `D(N)` pools have **42–57** moduli. **A Lean rendering of this certificate is
> out of reach by roughly four orders of magnitude**, and the honest filing is the tree with its sha as a
> `COMPUTED_BOUNDED` receipt — exactly as instructed, and only if a run exhausts.

> **The rejected alternative, recorded so nobody re-proposes it.** An independent model suggested
> "branch on the five smallest moduli, one uncovered point per leaf". **That is NOT a valid certificate and
> was not used**: exhibiting one uncovered point under a partial assignment proves nothing, because the
> *remaining* moduli could still cover that point under some residue choice. Only a closure that bounds the
> reciprocal mass of **all** unassigned moduli is sound.

---

## THE LADDER — final table, with outcome provenance

Semantics recorded in every receipt (`evidence_class: COMPUTED_BOUNDED`):
**UNSAT at N** = *no covering system of ℤ with distinct moduli `p−1` (`p ≥ 5`) all of which divide `2N`*
(equivalently `lcm | 2N`). A bound with an explicit ceiling. **NEVER a refutation of Erdős 273** — the problem
quantifies over an infinite modulus pool and no finite `N` settles the negative branch.

### symmetric-two-halves (the real formulation)

| N | \|pool\| | S(N) | vars | clauses | outcome | source |
|---|---|---|---|---|---|---|
| 3,960 | 23 | 1.8629 | — | — | **UNSAT_TO_N** | **density** |
| 5,040 | 29 | 1.9290 | — | — | **UNSAT_TO_N** | **density** |
| 7,920 | 27 | 1.8904 | — | — | **UNSAT_TO_N** | **density** |
| 10,080 | 33 | 1.9474 | — | — | **UNSAT_TO_N** | **density** |
| 20,160 | 38 | 1.9536 | — | — | **UNSAT_TO_N** | **density** |
| 25,200 | 41 | 1.9798 | — | — | **UNSAT_TO_N** | **density** |
| 45,360 | 47 | 1.9922 | — | — | **UNSAT_TO_N** | **density** |
| **27,720** | 43 | 2.0873 | 212,597 | 374,238 | **TIMEOUT_AT_N** @1200 s; longer `kissat --unsat` reached **3358.6 s CPU**, stopped | solver, no verdict |
| **50,400** | 50 | 2.0002 | 442,202 | 764,026 | **TIMEOUT_AT_N** @1200 s; longer run **3358.7 s CPU**, stopped | solver, no verdict |
| **55,440** | 52 | 2.1197 | 479,020 | 829,288 | **TIMEOUT_AT_N** @1200 s; longer run **3107.3 s CPU**, stopped | solver, no verdict |
| **83,160** | 58 | 2.1333 | 383,654 | 741,663 | **TIMEOUT_AT_N** @1200 s; longer run **3107.3 s CPU**, stopped | solver, no verdict |
| 110,880 | 58 | 2.1394 | 538,662 | 1,029,615 | CNF emitted; taken by peer | — |
| 138,600 | 64 | 2.1404 | 667,976 | 1,279,011 | CNF emitted; taken by peer | — |
| 166,320 | 71 | 2.1658 | 1,603,929 | 2,738,363 | CNF emitted, unsolved | — |
| 221,760 | 68 | 2.1474 | 834,076 | 1,694,471 | CNF emitted, unsolved | — |
| 277,200 | 74 | 2.1728 | 1,092,798 | 2,193,418 | CNF emitted, unsolved | — |
| 332,640 | 80 | 2.1860 | — | — | build stopped at wind-down | — |
| **360,360** | 79 | **2.2114** | 1,693,521 | 3,260,809 | CNF emitted, unsolved — **best slack under the 2 M-var cap** | — |
| 720,720 | 96 | 2.2470 | 2,547,328 | — | **not emitted**: 27 % over the 2 M cap, ≈1.1 GB | — |
| 1,441,440 | 109 | 2.2671 | 7,034,867 | — | not emitted: 3.5× cap | — |

### fixed-selfridge-half (the brief's instructed split)

`N = 3,960 · 7,920 · 27,720 · 55,440 · 110,880 · 221,760 · 360,360 · 720,720` →
**UNSAT_TO_N, source density, every one.**

### controls

| instance | outcome |
|---|---|
| `single-half-control` N=180 | **SAT** 0.1 s — Selfridge's half. **NOT an Erdős 273 witness** (one half only). |
| `P3-CONTROL` N=180 (p≥3 admitted) | **SAT** 0.1 s — the settled `variants.three` object. **NOT an Erdős 273 witness** (a modulus has p=3). |

### hard-half-only instances (emitted at wind-down)

| N | \|pool\\{2}\| | S₂ | vars | clauses |
|---|---|---|---|---|
| 27,720 | 42 | 1.5873 | 159,432 | 187,032 |
| 83,160 | 57 | 1.6333 | 287,721 | 370,716 |
| 360,360 | 78 | 1.7114 | 1,270,116 | 1,630,248 |

---

## HONESTY LAW — outcome line per fact

| # | fact | class |
|---|---|---|
| 1 | The Lean predicate is the intended one — subset not equality, finite, distinct moduli | **STATEMENT_DEFECT — NO** |
| 2 | A covering system of ℤ with distinct moduli `p−1`, `p ≥ 5` | **WITNESS — NONE FOUND** |
| 3 | 7 symmetric rungs + 8 fixed-half rungs | **UNSAT_TO_N**, source **density** |
| 4 | Symmetric rungs 27,720 / 50,400 / 55,440 / 83,160 | **TIMEOUT_AT_N**, source **solver** — no verdict in 1200 s, nor in 3107–3359 s CPU on the longer runs |
| 5 | `D(180) = 14/9`; `D(144, Krukenberg pool) = 23/18` | **exhaustively certified minima** (B&B) — the only two D-values proved all night, both on **11-modulus** pools |
| 6a | `D(27,720)` (exclude {2}) | **INCONCLUSIVE_NODE_CAP** — `exhaustive: false`, `found: false`, **400,000,325 nodes / 2018.5 s**. Establishes **NOTHING**: neither that a low-density 2-free half exists, nor that none does. The rung is **NOT** proved dead. |
| 6b | `D(55,440)` (exclude {2}) | **STOPPED_NO_VERDICT** — killed at **2,880 s CPU** at the factory sweep. Not exhausting (its pool is larger than 27,720's, which had already capped out). |
| 7 | cadical + DRAT on hard-half-only N=27,720 | **NO VERDICT — EVER. BOX LOST.** Proof reached 5,147,684,864 bytes; the box became unreachable (SSH timeout, 100 % packet loss) before any SAT/UNSAT line appeared, and `drat-trim` never ran. **Contributes nothing.** |
| 8 | The "Krukenberg 4/3 floor" and everything derived from it | **RETRACTED — the premise is false** |
| 9 | Branch-tree bound certificate | **IMPLEMENTED, BUT NOT RENDERABLE** — 19.9 M leaves / 627 MB on an 11-modulus control |

> ### ⛔ THE ANNEALER IS NOT MY COMPUTATION — ATTRIBUTION
>
> **I never ran the local-search annealer.** It was order (4) of an earlier message and was superseded
> before I reached it. A **different agent** ran it; its report sits in this same campaign dir at
> `anneal/FIXER-ANNEAL273-REPORT.md` and states:
>
> > `NO WITNESS FOUND. NO_WITNESS_FOUND_LOCAL_SEARCH.` — terminated early on coordinator order.
>
> So the "concurring 27720 signal" is real and it **concurs**: local search also found no witness.
> **Recorded as EVIDENCE, NOT PROOF**, and explicitly **not verified by me** — I did not write, run, or
> audit that code. A local search finding nothing is not a nonexistence result under any circumstances.
>
> Note also: `SAT-LADDER-REPORT-2026-09-02.md` at the campaign root is a **copy of this report** made by
> another agent, not a second independent result. Do not double-count it.

### Corrections I made to my own record during the night

* Two receipts (`sym-N110880 UNKNOWN 71.9 s`, `sym-N138600 UNKNOWN 444.2 s`) were produced by **my own
  `pkill`**, not by a cap. **Deleted, not filed.**
* Four `kissat --unsat` receipts read "TIMEOUT after 4200 s"; they were **killed at 3107–3359 s** and the cap
  was never reached. **Refiled as `STOPPED_NO_VERDICT`** with true CPU.
* One `hh-N27720` receipt likewise refiled (`STOPPED_NO_VERDICT`, 180.9 s).
* A false alarm ("solvers killed") caused by a malformed `ps` pipeline was **recorded and corrected**; no
  measurement was ever filed from the bad reading.
* **A killed process is not a timeout.** Applied without exception.

### Measurement honesty

CPU-vs-wall audited twice under box load 44/32 at `nice 10`: `cpu_seconds == elapsed_seconds` to within 1 s on
every lane. The caps delivered real CPU; no figure here is contended wall time.
All 12 emitted CNFs were integrity-checked (declared vs actual clause counts) — **12 intact, 0 corrupt** — and
sha256-manifested so the peer's independent path can prove it solved the same bytes.

---

## WHAT I LEFT ON THE BOX (factory sweep, 16:41Z)

**Exactly ONE solver process**, as ordered:

```
189790  nice 10  cadical --no-binary -q hard-half-only-N27720.cnf /root/peer/out/hh27720.drat
189789  nice 10  (its bash wrapper)
```

Box-wide `cadical` + `kissat` count after my sweep: **1** — that one. Every other lane, builder and
B&B of mine is killed. Load fell **18.0 → 10.16**. The remaining `python3`/`tail -f` processes on the
box are **not mine** (peer session + `sweep_daemon.py` + system units).

> ⚠ **DRAT, not LRAT.** The wind-down note asked for **LRAT** output; this run emits **DRAT**
> (`--no-binary`), which is what the preceding order specified ("DRAT proof output checked by
> drat-trim") and what `drat-trim` consumes. Switching to `--lrat` now would discard 37 minutes and
> a 4.88 GB proof, so I did not restart it. If LRAT is required, the run must be redone from scratch:
> `cadical --lrat -q cnf/hard-half-only-N27720.cnf hh27720.lrat`.

> ⚠ **If this run returns UNSAT, the proof must still be checked before it counts.**
> `drat-trim cnf/hard-half-only-N27720.cnf /root/peer/out/hh27720.drat` — and the receipt must carry
> the **sha256 of the proof file**. Nothing about this certificate may be claimed until drat-trim
> verifies it. A cadical "UNSAT" line on its own is not a certificate.

## ⛔ BOX LOST BEFORE THE LAST CERTIFICATE RETURNED (16:4xZ)

The Scaleway box became **unreachable** immediately after hand-off — SSH connection timed out on two
attempts and ICMP showed **100 % packet loss**. It was taken for the factory, as the wind-down order
said it would be.

**Consequence, stated plainly:**

* The `cadical --no-binary` run on `hard-half-only-N27720.cnf` **never returned an observed verdict.**
  Last observation (16:42Z): alive at `nice 10`, ~37 min CPU, DRAT proof **5,147,684,864 bytes**.
* **No SAT/UNSAT line from it was ever seen, and `drat-trim` was never run on that proof.**
  It contributes **NOTHING** to the record. It is not a bound, not a hint, not weak evidence.
* The proof file and every remote artefact are **gone with the box**. Its sha256 was never computed,
  so even if the file were recovered it could not be tied to what I observed.

**Nothing was lost from the deliverable.** Every receipt, script, CNF metadata row, control and report
had already been pulled local and sha256-manifested before the box went away: 173 files, manifest
complete (0 missing, 0 stale), and `MINEixer-273sat-report.md` byte-identical to the campaign copy.
The only casualty is the one certificate that had not yet produced a result.

## RESUME COMMANDS

```bash
# the two certificates still running at wind-down
python3 f273_minhalf.py --Ns 27720 --exclude 2 --tree --tree-out tree-27720.json \
  --node-cap 400000000 --secs-per-N 3000 --out mh-27720x2.json --question-lock <lock>
#   decisive ONLY if it reports exhaustive:true

cadical --no-binary -q cnf/hard-half-only-N27720.cnf hh27720.drat
drat-trim cnf/hard-half-only-N27720.cnf hh27720.drat
#   UNSAT + verified proof => no hard-half covering with all moduli dividing 27720;
#   with the parity split that proves the rung dead.  File with the proof file's sha.

# the best unsolved rung
kissat cnf/symmetric-two-halves-N360360.cnf     # S=2.2114, best slack under the 2M cap
```

**STEP 3 (Lean) was never triggered** — it is conditional on a witness and there is none. The route is fixed
and Mathlib is prebuilt on the box: emit the witness as `a, m : Fin k → ℕ`; `tbl_all : ∀ r < L, tbl r = true`
by `decide` (or `native_decide`, which **must** be disclosed — it adds `Lean.ofReduceBool` to the axiom
footprint); lift via `Int.emod_emod_of_dvd` with `mᵢ ∣ L`; assemble `StrictCoveringSystem ℤ` using
`Ideal.mem_span_singleton` and `Ideal.span_singleton_eq_span_singleton` for `injective_moduli`; `#print axioms`.

## THE HONEST BOTTOM LINE

The parity split is exact and free, and it turns Erdős 273 into a finite question at every ceiling `N`.
Density alone kills 15 rungs outright and kills the brief's instructed Selfridge-fixed split everywhere
reachable. But at every rung where the question is genuinely open — `27,720 ≤ N ≤ 360,360`, slack 4.4–10.6 % —
**no solver on either path returned a verdict all night**, and the two minimum-density values that *were*
certified are for pools of 11 moduli, an order of magnitude smaller than the live ones.
**Erdős 273 is untouched. What this session produced is the first quantitative map of where a witness could
possibly live, and proof that it does not live in the easy part.**

**The decisive computation did not land.** `D(27,720)` — the one number that would have settled the smallest
live rung by pure density-after-split — **capped out at 400 M nodes without exhausting**. The two D-values
that *were* certified are for 11-modulus pools; the live one has 42. That gap, not solver strength, is the
honest edge of tonight's result.
