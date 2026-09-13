import hashlib, os, sys, time, json
root = sys.argv[1]
rows = []
for dirpath, _, files in os.walk(root):
    for fn in sorted(files):
        if fn in ("RECEIPT-MANIFEST.md", "receipt-manifest.json"):
            continue
        p = os.path.join(dirpath, fn)
        h = hashlib.sha256()
        with open(p, "rb") as f:
            while True:
                b = f.read(1 << 20)
                if not b: break
                h.update(b)
        rel = os.path.relpath(p, root).replace("\\", "/")
        rows.append({"file": rel, "bytes": os.path.getsize(p), "sha256": h.hexdigest()})
rows.sort(key=lambda r: r["file"])
out = ["# RECEIPT MANIFEST — Erdős 273 campaign, 2026-09-02",
       "",
       f"{len(rows)} files, sha256. Generated {time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime())}.",
       "",
       "| file | bytes | sha256 |", "|---|---|---|"]
for r in rows:
    out.append(f"| `{r['file']}` | {r['bytes']:,} | `{r['sha256']}` |")
txt = "\n".join(out) + "\n"
open(os.path.join(root, "RECEIPT-MANIFEST.md"), "w", encoding="utf-8").write(txt)
json.dump(rows, open(os.path.join(root, "receipt-manifest.json"), "w", encoding="utf-8"), indent=1)
print(f"manifested {len(rows)} files")
