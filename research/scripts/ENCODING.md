# ENCODING.md — Erdős 273 SAT instances in `/root/peer/sat273/cnf/`

Written for the independent (cadical + seed-replica portfolio) solver path.
Everything below is exact; nothing is approximate. Question lock:
`/root/peer/sat273/erdos273-covering-sat-ladder.json`.

---

## 0. What the instance decides

**Erdős 273:** is there a covering system of ℤ, finitely many congruence classes,
**distinct** moduli, every modulus of the form `p − 1` for a prime `p ≥ 5`?

Any finite covering system has `L = lcm(moduli)` and every modulus divides `L`.
So the ladder over `N` is a **complete stratification**: the instance for a given
`N` decides *"is there a witness with `lcm | 2N`"*. UNSAT is therefore a bounded
nonexistence fact for that `2N`, **never** a refutation of 273.

## 1. The parity split (why the instance is in half-space)

Every `p − 1` with `p ≥ 5` is **even**. A class `a mod m` with `m` even lies
entirely inside one residue class mod 2. So the system splits with no loss:

* classes with **even** residue must cover all of `2ℤ`;
* classes with **odd** residue must cover all of `2ℤ + 1`.

Writing `m = 2h`, `n = 2t + ε`, `a = 2r + ε`:
`2t + ε ≡ 2r + ε (mod 2h)  ⟺  t ≡ r (mod h)`.

> **273 ⟺ `H = {(p−1)/2 : p prime ≥ 5}` contains TWO DISJOINT distinct-moduli covering systems of ℤ.**

`H = 2, 3, 5, 6, 8, 9, 11, 14, 15, 18, 20, 21, 23, 26, 29, 30, 33, 35, 36, 39, 41, 44, 48, 50, …`
(absent below 60: 1, 4, 7, 10, 12, 13, 16, 17, 19, 22, 24, 25, 27, 28, 31, 32, 34, 37, 38, 40, 42,
43, 45, 46, 47, 49, 52, 55, 57, 58, 59).

Selfridge's `p ≥ 3` example supplies one legal half and modulus 2 (`p = 3`) for
the other parity; the open problem is exactly the **second, disjoint** half.

## 2. `pool` — which moduli exist, and which are excluded and why

For a rung `N`:

```
pool = [ h : h divides N,  h >= 2,  2h+1 is prime ]        (ascending)
```

Three independent exclusions, all already applied in the CNF:

| excluded | why |
|---|---|
| `h ∤ N` | a witness with `lcm \| 2N` uses only moduli dividing `2N`, i.e. `h \| N` |
| `2h + 1` composite | modulus `2h` would not be `p − 1` for a prime `p` |
| `h = 1` | `2h + 1 = 3 < 5`; `p = 3` is exactly what the `p ≥ 5` problem forbids |

In the **`fixed-selfridge-half`** formulation there is a fourth exclusion:
`h ∈ {2, 3, 5, 6, 9, 15, 18, 20, 30, 36, 90}` (the divisors of 180 lying in `H`)
is pinned to half 0 with the residues
`(0,2) (1,3) (3,5) (5,6) (0,9) (0,15) (3,18) (11,20) (9,30) (33,36) (87,90)`
and forbidden in half 1.

The exact `pool` for each rung is in `<formulation>-N<N>.layout.json`.

## 3. Variable index → (half, modulus, residue)

Let `pool = [h₁ < h₂ < … < h_k]`, `total = Σ pool`, `prefix(h) = Σ_{h' ∈ pool, h' < h} h'`.

```
var(half, h, r) = 1 + half*total + prefix(h) + r        half ∈ {0,1}, h ∈ pool, 0 ≤ r < h
```

Variables `1 … 2*total` are exactly these; **every variable above `2*total` is an
auxiliary of the at-most-one encoding and carries no meaning** (`x_vars` in the
layout json is `2*total`).

Meaning of `var(half, h, r) = TRUE`:

> the congruence class **`r mod h`** is chosen in half `half` of the half-space problem
> — equivalently, in the actual covering system of ℤ, the class
> **`2r + half  (mod  2h)`** is chosen, with `2h = p − 1`, `p = 2h + 1` prime.

Both formulations use the **same** layout; a formulation that leaves a half
unused simply forces all of that half's variables to `FALSE` by unit clauses.

## 4. Clause structure

| # | clauses | count | shape |
|---|---|---|---|
| 1 | **coverage** (at-least-one per cell) | `N` per active half | for cell `c ∈ [0,N)`: `⋁_{h ∈ pool} var(half, h, c mod h)` — length `\|pool\|` |
| 2 | **at-most-one per modulus** | one AMO per `h ∈ pool` | over **all** `2h` literals `{var(0,h,·)} ∪ {var(1,h,·)}` — Sinz sequential counter (`pysat` `EncType.seqcounter`), `~2h` aux vars |
| 3 | **forced-use** (at-least-one per modulus, only for `h` with `1/h ≥ S − NEED`) | ≤ `\|pool\|` | `⋁_{half, r} var(half, h, r)` |
| 4 | **symmetry breaking** | units | see §5 |
| 5 | **pinning units** (`fixed-selfridge-half` only) | units | half 0 pinned to Selfridge, its moduli banned from half 1 |

There is **no** explicit "at least one residue per modulus" except clause type 3:
a modulus may legitimately go **unused**. Clause 2 spans both halves, so it
simultaneously encodes *one residue per modulus* **and** *the two halves are
disjoint as sets of moduli* — which is exactly Lean's `injective_moduli`.

## 5. Soundness of the two prunings (both are WLOG / derived, not heuristic)

**Forced-use.** Let `S = Σ_{h ∈ pool} 1/h` and `NEED = 2` (symmetric) or `1`
(single half). A distinct-moduli covering system of ℤ has `Σ 1/m > 1` **strictly**:
`≥ 1` by density, and equality would be an exact cover, impossible for ≥ 2 distinct
moduli by the Mirsky–Newman argument (the largest modulus must repeat). Two
disjoint such systems therefore need `> 2`. Hence if `S − 1/h ≤ NEED`, modulus `h`
cannot be omitted. This is a **derived implication of the instance**, so it removes
no solutions.

**Symmetry breaking** (symmetric formulation only), with `h₀ = min(pool)`:
* *half swap* — the two halves are interchangeable, so `h₀` never sits in half 1:
  units `¬var(1, h₀, r)` for all `r`.
* *translation of half 0* — translating a covering of ℤ by `t` is a covering, so
  if `h₀` is used in half 0 its residue may be taken `0`:
  units `¬var(0, h₀, r)` for `r ≠ 0`. Vacuous if `h₀` is unused.

Both are solution-preserving in the sense that **the instance stays SAT iff the
unbroken instance is SAT**; a model of the broken instance is a model of the
unbroken one. Disable with `--no-forced` / `--no-symbreak` if the independent path
wants the raw instance.

## 6. Files per rung

```
cnf/<formulation>-N<N>.cnf            DIMACS
cnf/<formulation>-N<N>.layout.json    pool, x_vars, vars, clauses, lift rule
cnf/READY-N<N>.txt                    appended when a rung's files are complete
                                      (or: NO-CNF + the density reason)
```
`<formulation> ∈ { symmetric-two-halves, fixed-selfridge-half, single-half-control }`.

If `READY-N<N>.txt` says `NO-CNF reason=UNSAT_BY_DENSITY` there is **no CNF and no
work to do**: `S ≤ NEED`, so the rung is UNSAT by the density argument of §5 alone.

## 7. Decoding and re-verification

```
python3 decode_model.py --layout cnf/symmetric-two-halves-N27720.layout.json \
                        --model  <solver stdout or bare int list>
```
It prints the two halves, the lifted covering `(residue, modulus)` over ℤ, the primes
`p = m + 1`, the reciprocal sum, and `VERDICT`. The check is a **fresh code path**:
`lcm` of the chosen moduli is computed and every integer of `[0, lcm)` is tested for
membership individually — no striding sieve, no shared code with the encoder.
`VERDICT: ERDOS_273_WITNESS_VERIFIED` requires *all* of: both halves cover ℤ,
moduli pairwise distinct across both halves, the lift covers ℤ, every `m + 1` prime
and `≥ 5`.

## 8. Cross-check protocol

The pysat/kissat path and the independent cadical portfolio run the **same DIMACS
bytes**. The receipt is agreement:
* both **UNSAT** → `UNSAT_TO_N` for that `2N`;
* both **SAT**, each model decoded and independently verified (models may differ) →
  `WITNESS_UNVERIFIED` until a Lean kernel check upgrades it to `WITNESS_KERNEL_CHECKED`.
Disagreement is a bug in one of the two paths and must be reported as such, not resolved
by preferring either.
