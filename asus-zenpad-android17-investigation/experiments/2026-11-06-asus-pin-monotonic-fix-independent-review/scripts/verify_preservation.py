"""Read-only verification of originals and exact reviewed snapshot inputs."""
import difflib
import json
from pathlib import Path
import sys
sys.dont_write_bytecode = True
from snapshot import ROOT, WS, PARENT, ORIGINAL, PRIOR, digest, manifest, save

def receipt(directory):
    files = {name: digest(directory / name) for name in
             ('profile.json', 'source/adapter.py', 'source/engine.py',
              'source/root_dispatch.py', 'source/preserved.json')}
    import hashlib
    return {'files': files, 'sha256': hashlib.sha256(json.dumps(
        files, sort_keys=True, separators=(',', ':'), allow_nan=False).encode()).hexdigest()}

def compare(expected, base):
    return [name for name, pin in expected.items()
            if not (base / name).is_file() or digest(base / name) != pin]

def main():
    before = json.loads((ROOT / 'evidence/originals.before.json').read_text())
    after = {}
    for directory in (PARENT, ORIGINAL, PRIOR):
        after.update(manifest(directory))
    inputs = json.loads((ROOT / 'evidence/inputs.json').read_text())
    for name in inputs:
        after[name] = digest(WS / name)
    save('originals.after.json', after)
    baseline = json.loads((PRIOR / 'evidence/reviewed-tree.before.json').read_text())
    prior_inputs = json.loads((PRIOR / 'evidence/original-inputs.before.json').read_text())
    snapshot_before = json.loads((ROOT / 'evidence/snapshot.before.json').read_text())
    snap = ROOT / 'snapshot' / PARENT.name
    current = receipt(PARENT)
    original = receipt(ORIGINAL)
    copied = receipt(snap)
    handoff = json.loads((PARENT / 'HANDOFF.json').read_text())
    old_text = (ORIGINAL / 'source/adapter.py').read_text()
    new_text = (PARENT / 'source/adapter.py').read_text()
    delta = ''.join(difflib.unified_diff(old_text.splitlines(keepends=True),
                    new_text.splitlines(keepends=True),
                    fromfile='original/source/adapter.py', tofile='fixed/source/adapter.py'))
    (ROOT / 'evidence/adapter-fix.regenerated.patch').write_text(delta)
    unchanged_code = [name for name in current['files'] if current['files'][name] == original['files'][name]]
    result = dict(original_file_count=len(before),
                  original_manifest_changes=[name for name in sorted(set(before) | set(after)) if before.get(name) != after.get(name)],
                  prior_review_original_file_count=len(baseline),
                  prior_review_original_changes=compare(baseline, WS),
                  original_public_input_count=len(prior_inputs),
                  original_public_input_changes=compare(prior_inputs, WS),
                  negative_fixture_changes=compare(inputs, WS),
                  snapshot_original_file_changes=compare(snapshot_before, WS),
                  current_code=current, original_code=original, copied_code=copied,
                  handoff_receipt_matches=(current == handoff['code']),
                  unchanged_code_files=unchanged_code,
                  patch_matches=(delta == (PARENT / 'evidence/adapter-fix.patch').read_text()))
    save('preservation.json', result)
    save('pins.json', {'current': current, 'original': original, 'snapshot': copied,
                       'public_inputs': inputs})
    assert not any(result[name] for name in ('original_manifest_changes', 'prior_review_original_changes',
                   'original_public_input_changes', 'negative_fixture_changes', 'snapshot_original_file_changes'))
    assert current == copied == handoff['code']
    assert current['sha256'] == '24196e415ac61a56fac5ef1ce145181c90915323129600cc16d67096d1afc62e'
    assert original['sha256'] == '5f20aece6bfa3ede3e937766ff390e6a575cbbc97759cbe52a3f8a09b68f5a72'
    assert unchanged_code == ['profile.json', 'source/engine.py', 'source/root_dispatch.py', 'source/preserved.json']
    assert result['patch_matches']
    print(json.dumps({k: result[k] for k in ('original_file_count', 'prior_review_original_file_count',
                     'original_public_input_count', 'handoff_receipt_matches', 'patch_matches')}))

if __name__ == '__main__':
    main()
