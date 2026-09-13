#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""MANIFEST for /root/peer/sat273/cnf/ -- sha256 + declared-vs-actual clause counts.

The cross-check protocol in ENCODING.md says the two solver paths must run the SAME
DIMACS bytes.  This makes that checkable instead of assumed, and it catches a
truncated build (declared clause count != actual clause lines) before anyone wastes
CPU on a corrupt instance.
"""
from __future__ import annotations
import hashlib, json, os, sys, glob, time

CNFDIR = sys.argv[1] if len(sys.argv) > 1 else "/root/peer/sat273/cnf"

rows = []
for f in sorted(glob.glob(os.path.join(CNFDIR, "*.cnf"))):
    h = hashlib.sha256()
    with open(f, "rb") as fh:
        while True:
            b = fh.read(1 << 22)
            if not b:
                break
            h.update(b)
    n, last, hdr = 0, "", ""
    with open(f, encoding="utf-8", errors="replace") as fh:
        hdr = fh.readline().strip()
        for line in fh:
            n += 1
            last = line
    parts = hdr.split()
    dv, dc = (int(parts[2]), int(parts[3])) if len(parts) == 4 else (None, None)
    ok = (dc == n) and last.rstrip().endswith("0")
    lay = f[:-4] + ".layout.json"
    L = json.load(open(lay, encoding="utf-8")) if os.path.exists(lay) else {}
    rows.append({"file": os.path.basename(f), "bytes": os.path.getsize(f),
                 "sha256": h.hexdigest(), "declared_vars": dv,
                 "declared_clauses": dc, "actual_clause_lines": n,
                 "INTACT": ok, "N": L.get("N"), "pool_size": len(L.get("pool", [])) or None,
                 "x_vars": L.get("x_vars"), "layout": os.path.basename(lay) if L else None})

out = ["# CNF MANIFEST — Erdős 273 ladder",
       f"\nGenerated {time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime())} by `f273_manifest.py`.",
       "\n`INTACT` = the DIMACS header's clause count equals the actual number of clause lines "
       "**and** the file ends on a terminated clause. A build that was interrupted fails this. "
       "Builds are written to `.partial` and renamed only on completion, so an incomplete instance "
       "should never appear here at all — this is the belt-and-braces check.\n",
       "| file | N | \\|pool\\| | x-vars | declared vars | declared clauses | actual clause lines | INTACT | bytes | sha256 (first 16) |",
       "|---|---|---|---|---|---|---|---|---|---|"]
for r in rows:
    v = lambda x: "—" if x is None else (f"{x:,}" if isinstance(x, int) else str(x))
    out.append(f"| `{r['file']}` | {v(r['N'])} | {v(r['pool_size'])} | {v(r['x_vars'])} | "
               f"{v(r['declared_vars'])} | {v(r['declared_clauses'])} | {v(r['actual_clause_lines'])} | "
               f"{'**YES**' if r['INTACT'] else '**NO — DO NOT SOLVE**'} | {v(r['bytes'])} | "
               f"`{r['sha256'][:16]}` |")
bad = [r for r in rows if not r["INTACT"]]
out.append("")
out.append(f"**{len(rows)} instances, {len(rows)-len(bad)} intact, {len(bad)} corrupt.**")
if bad:
    out.append("\n> ⛔ CORRUPT: " + ", ".join(r["file"] for r in bad))
out.append("\nFull sha256 values are in `manifest.json` beside this file.\n")
txt = "\n".join(out)
open(os.path.join(CNFDIR, "MANIFEST.md"), "w", encoding="utf-8", errors="replace").write(txt)
json.dump(rows, open(os.path.join(CNFDIR, "manifest.json"), "w",
                     encoding="utf-8", errors="replace"), indent=1)
print(txt)
