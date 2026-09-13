import json, os, sys
C = sys.argv[1]
rows = json.load(open(os.path.join(C, "receipt-manifest.json"), encoding="utf-8"))
onfs = set()
for dp, _, fs in os.walk(C):
    for f in fs:
        if f in ("RECEIPT-MANIFEST.md", "receipt-manifest.json"):
            continue
        onfs.add(os.path.relpath(os.path.join(dp, f), C).replace(os.sep, "/"))
man = set(r["file"] for r in rows)
print("manifested:", len(man), " on disk:", len(onfs))
print("missing from manifest:", sorted(onfs - man)[:5] or "none")
print("stale manifest rows:", sorted(man - onfs)[:5] or "none")
