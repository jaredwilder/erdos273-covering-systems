"""Check every migrated public source file against the pinned source commit."""
import hashlib
import json
from pathlib import Path

root = Path(__file__).resolve().parents[1]
manifest = json.loads((root / 'SOURCE-MANIFEST.json').read_text(encoding='utf-8'))
for item in manifest['files']:
    data = (root / item['destination']).read_bytes()
    digest = hashlib.sha256(data).hexdigest()
    blob = hashlib.sha1(f'blob {len(data)}\0'.encode() + data).hexdigest()
    if len(data) != item['bytes'] or digest != item['sha256'] or blob != item['source_blob']:
        raise SystemExit('FAIL: ' + item['destination'])
print(json.dumps({'result': 'PASS', 'public_source_files': len(manifest['files']),
                  'source_commit': manifest['source_commit']}))
