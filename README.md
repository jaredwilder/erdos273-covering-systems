# Erdős #273 — covering systems with `p-1` moduli

Does there exist a finite covering system of the integers with pairwise distinct moduli, every modulus of the form `p-1` for a prime `p>=5`?

This repository contains an exact parity reduction, SAT/search encodings, density calculations, and finite exclusion results for that problem.

## Parity reduction

Every allowed modulus is even. Splitting the integers by parity and dividing by two gives an equivalent problem:

> Find two coverings with disjoint sets of half-moduli drawn from
>
> \[
> H=\{(p-1)/2:p\text{ prime},\ p\ge5\}.
> \]

A half-cover residue `(r,h)` lifts to `(2r+ε,2h)` for parity `ε∈{0,1}`.

This reduction is the organizing coordinate for the finite search.

## Finite search ladder

For a finite rung `N`, restrict the half-moduli to divisors of `N`. An UNSAT result at that rung proves that no covering exists whose original moduli all divide `2N`.

The repository records SAT encodings, branch-and-bound searches, density calculations, and alternative annealing/filler searches. Timeouts and unbuilt instances remain unresolved rather than being counted as negative results.

The research report also corrects an earlier proposed `4/3` density floor and preserves a counterexample to it.

## Start here

| File | Content |
|---|---|
| [`research/scripts/ENCODING.md`](research/scripts/ENCODING.md) | Exact parity reduction and SAT variables |
| [`research/SAT-LADDER-REPORT-2026-09-02.md`](research/SAT-LADDER-REPORT-2026-09-02.md) | Finite results and search limits |
| [`research/DENSITY-CURVE.md`](research/DENSITY-CURVE.md) | Density calculations |
| [`research/receipts/`](research/receipts/) | Search and control records |
| [`research/scripts/`](research/scripts/) | Encoders, decoders, and covering checks |

## Reproduce the portable controls

```sh
python verification/verify_source.py
python verification/run_controls.py
```

The controls replay the parity identity, reconstruct the Selfridge one-half covering, verify it independently, and check that its lift covers exactly one parity class.

The full permitted-modulus covering problem remains open in this package.

Author: Jared Wilder. License: Apache-2.0.
