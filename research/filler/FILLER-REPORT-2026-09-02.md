# FIXER REPORT — the Erdős 273 filler lane, built and smoke-tested

**Session:** 2026-09-02, local PC (no box). **Budget honoured:** no solver run over 25 s, no
model spend, RAM well inside the 3 GB cap
(the encoder streams to disk; the only large structure is the AMO clause list), 0 git commands.
**Write scope respected:** everything new is under
`oracle/evidence/msl-machine/campaigns/erdos273-sat-2026-09-02/filler/` plus this report.
No file in `scripts/`, `receipts/` or anywhere else was touched.

---

## 1. THE FIRST PROBLEM WAS NOT CUBING — THE ENCODER WAS GONE

The brief says "regenerate them here from the committed encoder … read `f273_sat.py`'s CLI."
**The committed `scripts/f273_sat.py` has no hard-half mode.** Its `--mode` accepts
`symmetric | fixedhalf | onehalf`, full stop. The `hardhalf` mode that produced
`receipts/receipt-export-hardhalf-N{27720,83160,360360}.json` lived only on the Scaleway box
and went away with it.

So the lane could not start until the mode was rebuilt. `filler/f273_hardhalf.py` does that,
and it does not ask to be believed:

```
python f273_hardhalf.py --selfcheck
N=27720   MATCH  (6.4s)
N=83160   MATCH  (9.2s)
N=360360  MATCH  (145.2s)
3/3 MATCH against receipted box metadata
```

Exact agreement on **vars, x_vars, clauses and literals** against all three surviving box
receipts. No tolerance, no rounding.

**One detail was recovered from arithmetic, not from code, and it is stated as an inference.**
The first pass came up **exactly 2 clauses and 2 literals short at every N** — a constant
independent of `|pool|` and of `N`, so it had to be two fixed unit clauses on small moduli
common to all three pools. The receipted metadata lists `translate_half0: true` **and**
`r3_eq_0: true` as two separate flags, and for `h0 = 3` those two rules emit the same two
units. The box wrote them twice. Duplicated unit clauses are semantically inert; they are
replicated verbatim so the reconstruction matches the lost bytes. The three receipts jointly
pin this down as the unique fixed +2.

### The "5,648 vars" number in BOX-RUN-PLAN reconciled

The plan calls the 3,960 hard-half rung "5,648 vars". The built instance declares **8,483**.
Both are right and they describe the same file:

| | count |
|---|---|
| live x-variables (`Σ h` over pool\\{2}, 22 moduli) | 2,835 |
| Sinz at-most-one auxiliaries (`Σ (h−1)`) | 2,813 |
| **live total** | **5,648** ← the plan's number |
| dead half-1 x-variables the box's layout allocates | 2,835 |
| **declared in the `p cnf` header** | **8,483** |

The box's `build()` always laid out both halves and only ever constrained one, so half 1's
2,835 variables appear in no clause. They are kept because dropping them would change
`x_vars` and break the match against the receipts. Every solver eliminates them on the first
sweep; they cost a larger header and nothing else.

### One claim in the brief has no receipt behind it

The brief says the 3,960 hard-half rung is one "kissat could not settle in 600 s." **There is
no such receipt in this campaign.** The only hard-half exports are N=27,720 / 83,160 / 360,360,
and the only hard-half *solve* receipt is `receipt-hh-N27720.json`, which is
`STOPPED_NO_VERDICT` at 180.9 s — killed, not capped. The 3,960 hard-half instance had never
been built. **It was built for the first time tonight.** Recording that so nobody later cites a
600-second timeout that never happened.

---

## 2. WHAT WAS BUILT

```
filler/
  f273_hardhalf.py       encoder (reconstruction) + --selfcheck against the receipts
  f273_cube_split.py     deterministic cube splitter
  partition_check.py     proves the cube set is a partition — both arms
  mkcube.py              base CNF + cube units -> one standalone DIMACS, header corrected
  run_cube.sh            per-cube box runner: assemble -> solve -> drat-trim -> checkpoint
  decode_cube_model.py   decode + independent verify + prints the stage-two command
  aggregate.py           checkpoints -> one rung verdict, fails closed
  smoke_test.py          25 s pipeline probe (no solver binaries on this PC)
  filler-config.json     what the box runner consumes
  README.md
  cnf/                   N=3960 CNF + layout + onehalf-compat layout + build receipt
  cubes/N3960/           72 cubes + manifest + cubes.icnf + partition-check
  cubes/N360360/         560 cubes + manifest + partition-check   (CNF regenerated on the box)
  out/                   smoke receipts, aggregate
```

Total 1.9 MB on disk; the 164 MB ceiling CNF is deliberately **not** committed — the encoder is
byte-deterministic (verified: a full rebuild of the 3,960 CNF reproduced sha256
`bf74e29f…3392ee` exactly), so the bytes are regenerated in ~2.5 minutes on the box instead of
carried in a repo that already has a 2 GiB-pack scar.

### Cube counts

| N | pool\\{2} | S₂ | CNF | cubes | split moduli | window | in repo |
|---|---|---|---|---|---|---|---|
| **3,960** | 22 | 1.36288 | 8,483 v / 12,383 c / 439 KB | **72** | {3, 5, 8} | 64–256 ✓ | **yes** |
| **360,360** | 78 | 1.71142 | 1,270,116 v / 1,630,248 c / 164 MB | **560** | {3, 5, 6, 9} | 512–4096 ✓ | cubes only |

**How the split moduli are chosen (deterministic, no tuning).** Branching on the *smallest*
moduli is what prunes — a class of modulus `h` covers `N/h` cells of ℤ/N — and its branch
factor is only `|allowed(h)| + 1`. Over the 8 smallest moduli of pool\\{2} the splitter takes
the largest-cardinality subset whose cube count lands in the window, tie-broken to the
lexicographically smallest ascending tuple (i.e. preferring the smallest, most-constraining
moduli). Both instances landed inside the brief's requested windows on the first pass.

**A cube is a branch of a case split, not a heuristic guess.** For each chosen modulus the
branches are: *used at residue r*, for each residue the symmetry units leave alive; or
*unused*. `allowed(h)` is imported from the encoder, never re-derived, so a branch set cannot
drift away from the units actually in the CNF.

---

## 3. THE PARTITION IS PROVED, NOT ASSERTED

"All cubes UNSAT ⇒ the rung is UNSAT" is only sound if the cubes partition the model space. An
aggregation rule that is merely asserted is how a partial sweep becomes a fake bound, so
`partition_check.py` proves it in two arms:

* **Arm 1 (structural, exhaustive, no solver).** For each split modulus, enumerate *every*
  assignment the CNF can admit — at most one residue true, true only where the units allow —
  and check exactly one branch matches. `h+1` cases against `h+1` branches: a complete case
  check, not a sample. Per-modulus partition × product ⇒ global partition.
* **Arm 2 (the premise, against the real bytes).** Arm 1 is sound only if the CNF genuinely
  forbids two residues of one modulus and genuinely kills the residues the symmetry units
  claim to kill. So: assume each pair, require refutation; assume each supposedly-dead residue,
  require refutation. Any survivor means Arm 1's case list was incomplete and the aggregation
  is **invalid** — reported as a failure, never as a caveat.

```
N=3960    arm1 true   n_cubes_implied 72    arm2_run true   arm2 true   PARTITION_PROVED
N=360360  arm1 true   n_cubes_implied 560   arm2_run false              PARTITION_PROVED
```

**Arm 2 has not run at N=360,360** — the CNF is regenerated on the box, so the check must run
there. `filler-config.json` lists it as a mandatory preflight step and `aggregate.py`'s
`UNSAT_TO_N` branch names it as a precondition.

---

## 4. THE 30-SECOND SMOKE TEST — pipeline shape, no verdict

No `cadical`, `kissat` or `drat-trim` binary exists on this PC, so the probe drives pysat's
bundled CaDiCaL 1.5.3. Two runs, both under the cap:

| probe | path | result | seconds |
|---|---|---|---|
| cube `c00000`, base CNF + cube as **assumptions** | library path | INDETERMINATE | 15.3 |
| cube `c00007`, **assembled `base + cube units` file** | *the exact box path* | INDETERMINATE | 4.3 |

Both `header_intact: true` (declared clause count = actual, 12,383 and 12,386). `mkcube.py`
assembled the second file and rewrote the header correctly (`12,383 → 12,386`, +3 cube units).

**INDETERMINATE is the expected and only honest outcome** of a 25-second probe on a job budgeted
at 3,600 seconds per cube. It establishes nothing about the rung, and the receipts say so in
those words.

---

## 5. THE EXACT LAUNCH LINES FOR THE BOX

Working directory:
`<estate>/oracle/evidence/msl-machine/campaigns/erdos273-sat-2026-09-02/filler`

```bash
# 0 — prove the encoder is the box's encoder (must print 3/3 MATCH)
python3 f273_hardhalf.py --selfcheck

# 1 — regenerate the ceiling CNF  (~150 s, 164,407,862 bytes,
#     1,270,116 vars / 1,630,248 clauses — assert these against the receipt it writes)
python3 f273_hardhalf.py --N 360360

# 2 — cubes + the mandatory partition proof, both arms
python3 f273_cube_split.py --N 360360 --cnf cnf/hard-half-only-N360360.cnf
python3 partition_check.py --N 360360 --cnf cnf/hard-half-only-N360360.cnf   # PARTITION_PROVED

# 3 — THE FILLER: 560 cubes across every spare core, 1 h each, checkpointed
python3 -c "import json;print('\n'.join(c['cube_id'] for c in json.load(open('cubes/N360360/manifest.json',encoding='utf-8'))['cubes']))" \
  | xargs -P 30 -I{} nice -n 10 bash run_cube.sh 360360 {} 3600 kissat

# 4 — the cheap decisive rung, WITH proofs (439 KB instance, drat-trim can finish)
python3 -c "import json;print('\n'.join(c['cube_id'] for c in json.load(open('cubes/N3960/manifest.json',encoding='utf-8'))['cubes']))" \
  | xargs -P 8 -I{} nice -n 10 bash run_cube.sh 3960 {} 3600 cadical drat

# 5 — the verdict, whatever it is
python3 aggregate.py --N 360360
python3 aggregate.py --N 3960
```

`-j` / `-P` is the only knob the box runner needs: raise it when other queues drain, lower it
when they refill. Cubes killed mid-flight are simply re-run — `run_cube.sh` skips any cube whose
checkpoint already holds SAT or UNSAT. **A kill costs one cube, never a run.** That is the whole
reason this lane is the right thing to point at spare cores.

Assembly cost at the ceiling: ~164 MB per in-flight cube in `/dev/shm`, so 30 concurrent hold
~4.9 GB of the box's 251 GB, each unlinked the moment its cube finishes.

---

## 6. WHAT A RESULT WOULD AND WOULD NOT MEAN

Written into `aggregate.py`, `filler-config.json`, `decode_cube_model.py` and the README — four
places, deliberately.

**Any cube SAT → `SAT_HARD_HALF`.** A distinct-moduli covering of ℤ drawn from
`H ∩ divisors(N) \ {2}` exists. **This is not an Erdős 273 witness. It is one half of one.**
Erdős 273 needs two disjoint halves. `decode_cube_model.py` decodes it, re-verifies it on a
fresh code path (direct enumeration of ℤ/N, primality re-tested from scratch, cube consistency
checked), and prints the exact stage-two command — the search for the complementary half, the
one that may hold modulus 2, in `pool \ used`. Only if stage two closes *and* the lifted object
re-verifies is there a candidate, and it stays `WITNESS_UNVERIFIED` until the Lean kernel signs
it. The compat layout lets the campaign's own `scripts/decode_model.py` read the same model
unmodified, so a SAT gets two independent decoders with no shared decoding code.

**Every cube UNSAT → `UNSAT_TO_N`.** No covering system of ℤ has distinct moduli all of the form
`p−1` (`p ≥ 5`) with `lcm | 2N`. A bound with an explicit ceiling. **Never a refutation of
Erdős 273** — the problem quantifies over an infinite modulus pool and no finite N settles the
negative branch.

**Anything else → `INCOMPLETE`.** A partial sweep is not a partial bound. `aggregate.py` counts
missing checkpoints and cube-sha mismatches as undecided and refuses to report a bound.

**A DRAT proof is not a certificate until `drat-trim` accepts it.** `run_cube.sh` runs drat-trim
*in place*, while the assembled CNF still exists, and records `drat_verified` separately from
`result` so the two can never be conflated. The lost box burned 37 minutes into a 5.1 GB DRAT
proof that was never checked and contributed nothing; that shape is now impossible here.

---

## 7. THE HONEST ODDS ON THIS LANE

`DENSITY-CURVE.md` is the controlling document and it is not encouraging. A 273 witness would
need two disjoint halves inside a pool carrying only 4–13 % total reciprocal slack, where the
only comparable object in the literature (Selfridge) spends 56 % on *one* half. The hard half
alone at N=360,360 has S₂ = 1.711 against a requirement of >1 — that is where the room is, and
it is why this rung is the ceiling shot.

**The realistic yield of this lane is a bound, not a witness**, and the plan already says so.
What tonight changed is that the lane can now actually run: the encoder exists again, the split
is proved to be a partition, the runner is restart-safe, and the aggregation refuses to
overclaim in either direction.

---

## 8. LEFT UNDONE, NAMED

* **Arm 2 of the partition check at N=360,360** — needs the CNF, which is regenerated on the
  box. Listed as a mandatory preflight in `filler-config.json`.
* **No verdict on any cube.** Nothing was solved to completion here and nothing should have
  been; the PC cap is 30 s and a cube is budgeted at 3,600 s.
* **N=27,720 and N=83,160 hard-half instances were not split.** They are the rungs the lost box
  was working; the brief pointed at 3,960 and 360,360 and that is what was built. Adding them
  is `f273_hardhalf.py --N 27720` + `f273_cube_split.py --N 27720` — the same two lines.
* **`--dead-subsets` is implemented but empty by default and refuses any entry without a cited
  receipt.** The campaign record contains no *proved* dead subset, so none is emitted. Inventing
  exclusions to shrink the search would be exactly the fabrication this estate exists to kill.
