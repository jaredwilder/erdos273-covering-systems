# B&B KNOWN-ANSWER CONTROLS — the licence for every D(N) claim

A searcher that has not demonstrated it **finds** a covering when one exists cannot certify
absence. These two controls run the **same code path** as the D(N) runs — same
`search()`, same least-uncovered-cell branching, same reciprocal-mass bound, no special-casing.
The only non-default argument is `--pool`, which supplies an explicit modulus set for control (b)
because Krukenberg's moduli are not of the form `(p−1)/2`.

## Control (a) — N = 180, FULL pool (2 included)

```
pool    = H ∩ divisors(180) = {2, 3, 5, 6, 9, 15, 18, 20, 30, 36, 90}   (11 moduli)
budget  = 1.60
```

| | |
|---|---|
| **found** | **YES** — `{2,3,5,6,9,15,18,20,30,36,90}`, residues verified to cover ℤ/180 |
| density | **1.5555556 = 14/9** |
| nodes | 63,135,084 |
| seconds | 67.16 |
| **exhaustive** | **YES** |
| lcm | 180 · BBMST filter `2\|L or 9\|L or 15\|L` → **satisfied** |
| all moduli `(p−1)/2` with `p ≥ 5` prime | **yes** |

> Because the search **exhausted**, this is stronger than the control required:
> **D(180) = 14/9 exactly** — no covering drawn from `H ∩ divisors(180)` is cheaper.
> This is Selfridge's half, recovered as a *proved minimum*, not merely found.

## Control (b) — ℤ/144, Krukenberg's pool (least modulus 3)

```
pool    = {3, 4, 6, 8, 9, 12, 16, 18, 24, 36, 48}   (11 moduli, all dividing 144)
budget  = 1.30
```

| | |
|---|---|
| **found** | **YES** — all 11 moduli, residues verified to cover ℤ/144 |
| density | **1.2777778 = 23/18** |
| nodes | 46,558,529 |
| seconds | 44.74 |
| **exhaustive** | **YES** |
| lcm | 144 · BBMST filter → **satisfied** |
| `all_legal` | **false**, correctly — 4, 12, 16, 24, 48 are not `(p−1)/2` for prime `p ≥ 5`. This pool is a search-engine control, not an Erdős-273 object. |

> Again stronger than required: the search **exhausted**, so
> **D(144, Krukenberg pool) = 23/18 exactly.**

### Independent confirmation that the 4/3 floor is false

Krukenberg's system `{[2,3],[0,4],[1,6],[2,8],[0,9],[3,12],[6,16],[3,18],[6,24],[33,36],[46,48]}`
was checked here by a separate code path (direct sieve over ℤ/144):

```
covers ℤ/144      : True     (zero uncovered residues)
distinct moduli   : True
least modulus     : 3
Σ 1/m             : 23/18 = 1.2777… < 4/3 = 1.3333…
```

**So the "Krukenberg 4/3 floor" is refuted by Krukenberg's own system — verified here, not taken
on report.** This is why the earlier `NEED_KRUK = 7/3` gate was retracted in full.

## VERDICT

**BOTH CONTROLS PASS, BOTH EXHAUSTIVELY. The searcher is trusted**, and D(N) values it emits may be
filed — subject to the standing rule that a run is decisive **only** when it reports
`exhaustive: true`. Any run that hits the node cap or the deadline is `INCONCLUSIVE_NODE_CAP`
and proves nothing in either direction.

⚠ **Scale caveat, stated in advance.** Both controls have **11-modulus** pools and needed 47–63 M
nodes to exhaust. The live D(N) runs have **42–57** moduli. Exhaustion there is a far larger
computation and may well not complete; if it does not, the honest output is INCONCLUSIVE, not
"dead by density".
