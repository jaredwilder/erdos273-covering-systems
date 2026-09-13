"""Small replay of the preserved programs; does not rerun historical large searches."""
import json
from pathlib import Path
import subprocess
import sys

root = Path(__file__).resolve().parents[1]
manifest = json.loads((root / 'SOURCE-MANIFEST.json').read_text(encoding='utf-8'))

def run(script, *args):
    return subprocess.run([sys.executable, '-B', '-X', 'utf8',
                           str(root / 'research' / 'scripts' / script), *args],
                          capture_output=True, encoding='utf-8', check=True).stdout

if manifest['source_prefix'] == 'erdos850':
    selftest = run('e850_verify.py', '--selftest').strip()
    two = json.loads(run('e850_naive.py', '--bound', '30000', '--k', '2'))
    three = json.loads(run('e850_naive.py', '--bound', '30000', '--k', '3'))
    expected = {(2,8), (6,48), (14,224), (30,960), (75,1215), (62,3968), (126,16128)}
    if {(r[0],r[1]) for r in two['first_pairs']} != expected or two['pair_count'] != 7:
        raise SystemExit('Known-answer pair set mismatch')
    if three['pair_count'] != 0:
        raise SystemExit('Unexpected three-term control result')
    for x,y in sorted(expected):
        run('e850_verify.py', '--witness', f'{x},{y}', '--k', '2')
    result = {'result':'PASS', 'bound':30000, 'two_term_pairs':7,
              'three_term_pairs':0, 'independent_pair_rechecks':7, 'selftest':selftest,
              'scope':'Small control only; historical 464637500000 frontier not rerun'}
else:
    out = json.loads(run('f273_core.py'))
    control = out['step1_reduction']
    keys = ['parity_split_identity_verified', 'selfridge_half_distinct',
            'selfridge_verify_stride_sieve', 'selfridge_verify_independent',
            'doubled_all_legal', 'doubled_all_divide_360',
            'odd_class_fully_covered_mod360', 'even_class_untouched_mod360']
    if not all(control[k] is True for k in keys):
        raise SystemExit('Parity or covering control failed')
    result = {'result':'PASS', 'checks':{k:control[k] for k in keys},
              'selfridge_search_nodes':control['selfridge_half_search_nodes'],
              'scope':'Parity identity and one-half covering controls; no two-half solution claimed'}
print(json.dumps(result, indent=2))
