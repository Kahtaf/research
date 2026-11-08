"""Extend actual configuration binding only by the approved profile/namespace delta."""
from pathlib import Path
import json
import shlex
from admission import need, read
def prepare_config_receipt(home, binding):
    home = Path(home)
    plan = read(home / 'inputs/plan.json')
    p = home / 'logs/full-build-combined-r1.vars'
    actual = {}
    for line in p.read_text().splitlines():
        key, sep, value = line.partition('=')
        if sep: actual[key] = ' '.join(shlex.split(value))
    baseline = read(home / 'inputs/baseline-variables.json')
    expected = dict(baseline)
    expected['PRODUCT_PACKAGES'] = ' '.join(sorted(set(baseline['PRODUCT_PACKAGES'].split()) | {'p00a_experimental_legacy_fcm3.xml'}))
    approval = read(binding['parent_acceptance'])
    for name, row in approval.get('approved_variable_changes', {}).items():
        need(name != 'PRODUCT_NOT_DEBUGGABLE_IN_USERDEBUG' and baseline.get(name) == row['before'], 'Unapproved variable preimage/root change')
        expected[name] = row['after']
    need(actual.keys() == expected.keys(), 'Unknown/missing captured variables')
    for name in actual:
        need(set(actual[name].split()) == set(expected[name].split()) if name == 'PRODUCT_PACKAGES'
             else actual[name] == expected[name], 'Unapproved configuration change: ' + name)
    from verify_config_paths import verify
    receipt = verify(p, plan)
    old = read(home / 'inputs/baseline-config-paths.json')
    need({k:v for k,v in receipt.items() if k != 'dumpvars_sha256'} ==
         {k:v for k,v in old.items() if k != 'dumpvars_sha256'}, 'Unproved configuration-path semantic change')
    with (home / 'inputs/expected-config-paths.json').open('x') as f: json.dump(receipt, f, indent=2); f.write('\n')
