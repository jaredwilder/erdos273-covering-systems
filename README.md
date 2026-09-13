# Erdős #273: covering systems with prime-minus-one moduli

Does a finite covering system of the integers exist with pairwise distinct
moduli, every modulus of the form `p-1` for a prime `p>=5`?

This is the focused home for Jared Wilder's parity reduction, finite search
ladder, SAT encodings, density computations, controls and correction history.
The problem remains open in this research package.

## Start here

| Read | Purpose |
|---|---|
| [Encoding and reduction](research/scripts/ENCODING.md) | Exact problem, parity split, variables and model decoding |
| [Research report](research/SAT-LADDER-REPORT-2026-09-02.md) | Results, finite limits, retractions and unresolved cases |
| [Density curve](research/DENSITY-CURVE.md) | Why particular finite ceilings are ruled out |
| [Receipts](research/receipts/) | Controls and bounded computation records |
| [Scripts](research/scripts/) | Encoder, decoder, covering checks and search tools |
| [Annealing](research/anneal/) and [filler search](research/filler/README.md) | Alternative searches and their outcomes |

## The organizing reduction

All permitted moduli are even. Dividing each parity class by two gives an
equivalence: find **two coverings with disjoint sets of moduli**, both drawn
from `H={(p-1)/2 : p prime, p>=5}`. Their residues lift back via
`(r,h) -> (2r+epsilon,2h)` for parity `epsilon`.

A finite rung `N` restricts the half-moduli to divisors of `N`. Consequently,
UNSAT at that rung means no witness whose original moduli all divide `2N`.
Timeouts and unbuilt instances remain unresolved; finite exclusions do not
refute the full problem. A single covering half is a control, not a solution.

## Corrections beside the evidence

The research report withdraws a claimed `4/3` density floor, retains a
counterexample to it, and distinguishes complete searches from capped runs.
It also records an oversized, incomplete proof tree. Those boundaries travel
with this package. The report and receipts, rather than file counts, determine
what can be claimed for each run.

## Run the checks

Python 3, standard library only, from the repository root:

```sh
python verification/verify_source.py
python verification/run_controls.py
```

The second command replays the parity identity and reconstructs the Selfridge
one-half control, checks the covering by two implementations, and verifies
its lift covers exactly one parity class. The
[dated replay](verification/REPLAY-2026-09-13.json) records these checks.
It does not rerun the SAT or large branch-and-bound searches.

SAT work additionally uses the solver dependencies recorded in the research
report. Original remote paths are preserved in orchestration scripts; the
portable control above needs no remote machine or solver installation.

## Provenance

All 916 files under `research/` are exact copies of the public source subtree.
[The source manifest](SOURCE-MANIFEST.json) pins its commit, original paths,
Git blob IDs and SHA-256 hashes. This includes the small per-instance receipts
as well as the principal reports; the reading map above is the entry point.
The former [mixed repository](https://github.com/jaredwilder/erdos-computational-searches)
remains the archive; this repository is the preferred problem-level entry.

Author: Jared Wilder. Source campaign: 2026-09-02. Focused release: 2026-09-13.
License: Apache-2.0, inherited from the public source.
