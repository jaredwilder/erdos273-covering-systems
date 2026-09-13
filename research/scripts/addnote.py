import io
p = 'fixer-273sat-report.md'
s = io.open(p, encoding='utf-8').read()
anchor = "## RESUME COMMANDS"
note = """## ⛔ BOX LOST BEFORE THE LAST CERTIFICATE RETURNED (16:4xZ)

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
complete (0 missing, 0 stale), and `MINE\fixer-273sat-report.md` byte-identical to the campaign copy.
The only casualty is the one certificate that had not yet produced a result.

"""
s = s.replace(anchor, note + anchor, 1)
s = s.replace(
    "| 7 | cadical + DRAT on hard-half-only N=27,720 | **STILL RUNNING — NO VERDICT CLAIMED.** Proof **4,877,094,912 bytes** (4.88 GB) at hand-off, 37 min CPU, disk 69 GB free. |",
    "| 7 | cadical + DRAT on hard-half-only N=27,720 | **NO VERDICT — EVER. BOX LOST.** Proof reached 5,147,684,864 bytes; the box became unreachable (SSH timeout, 100 % packet loss) before any SAT/UNSAT line appeared, and `drat-trim` never ran. **Contributes nothing.** |")
io.open(p, 'w', encoding='utf-8').write(s)
print("note added")
