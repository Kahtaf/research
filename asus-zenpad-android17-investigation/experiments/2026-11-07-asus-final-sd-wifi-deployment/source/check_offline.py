"""Focused source/refusal checks only; never runs a writer, process or device call."""
from pathlib import Path
import ast
import contextlib
import hashlib
import importlib.util
import io
import json
import sys

sys.dont_write_bytecode = True
ROOT = Path(__file__).resolve().parents[1]
WORK = ROOT.parent
results = {}


def digest(data):
    return hashlib.sha256(data).hexdigest()


def block(source, name):
    node = next(n for n in ast.parse(source).body if getattr(n, 'name', None) == name)
    return ''.join(source.splitlines(keepends=True)[node.lineno - 1:node.end_lineno]).encode()


old = (WORK / '2026-11-07-asus-wifi-microsd-probe/source/install.py').read_text()
new = (ROOT / 'source/install.py').read_text()
for name in ('execute', 'Transport'):
    before, after = block(old, name), block(new, name)
    assert before == after
    results[name + '_byte_preserved'] = dict(bytes=len(after), sha256=digest(after))

# The explicit-execute tail retains dispatch, lock, idempotence and cleanup;
# only PATH's source directory points back to the frozen original shim.
old_tail = old[old.index(' os.umask(0o077)'):old.index("if __name__=='__main__'")]
new_tail = new[new.index(' os.umask(0o077)'):new.index("if __name__=='__main__'")]
assert new_tail == old_tail.replace("str(ROOT/'source')", 'str(SHIM_DIR)')
results['execute_tail_preserved_except_frozen_shim_path'] = True

spec = importlib.util.spec_from_file_location('offline_final_installer', ROOT / 'source/install.py')
installer = importlib.util.module_from_spec(spec)
spec.loader.exec_module(installer)
admission = installer.admission
assert installer.INSTALL_PREIMAGES == (
    '902b2f06a01cca574b4aa374e67c4e7f8f0ed53f6e6a55017b6d96351f0f1f20',
    '78005304291706fe2ad2affa185467c89464dc2f3216f97d572a29a1e058afa9')
results['only_stock_and_installed_sd_probe_preimages'] = True

core = admission.load_core()  # Pinned source only; no package()/main()/artifacts.
assert core.package.__globals__['KERNEL_SHA'] == 'e9cde06e85e752aec0433ea37fa926c31b4f7a72cd55453762ec6870e5bb5bf1'
assert core.package.__globals__['CONFIG_SHA'] == '10b212cabd28aad012582e86c64695ccd450650b4e09ec8da30c21e094f377c2'
results['pinned_existing_parsers_loaded_without_artifact_or_process_operations'] = True

for label, callback in (
    ('duplicate_receipt_key', lambda: admission.parse_receipt(b'{"status":1,"status":2}')),
    ('nonassembly_receipt', lambda: admission.parse_receipt(b'{}')),
    ('missing_five_role_manifest', lambda: core.five_roles(b'')),
):
    try:
        callback()
    except ValueError as exc:
        results[label + '_refused'] = str(exc)
    else:
        raise AssertionError(label + ' accepted')

saved_pin = admission.SOURCE_PINS['source/bootformat.py']
admission.SOURCE_PINS['source/bootformat.py'] = '0' * 64
try:
    try:
        admission.check_sources()
    except ValueError as exc:
        results['source_drift_refused'] = str(exc)
    else:
        raise AssertionError('source drift accepted')
finally:
    admission.SOURCE_PINS['source/bootformat.py'] = saved_pin

assert not admission.DEFAULT_ASSEMBLY.exists(), 'Real assembly appeared; do not read it in worker checks'


def forbidden(*args, **kwargs):
    raise AssertionError('Forbidden process/network/helper/stock-image access in offline check')


# Default main must refuse the actual missing directory before these operations.
installer.a.check_sources = forbidden
installer.b.local_inputs = forbidden
installer.socket.create_connection = forbidden
installer.b.subprocess.run = forbidden
saved_argv = sys.argv
try:
    sys.argv = [str(ROOT / 'source/install.py')]
    out, err = io.StringIO(), io.StringIO()
    with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
        rc = installer.main()
    response = json.loads(err.getvalue())
    assert rc == 2 and not out.getvalue() and response['mode'] == 'PLAN_ONLY'
    assert response['outcome'] == 'refused' and response['device_contacted'] is False
    assert response['reboot'] is False and 'Actual parent final assembly directory required' in response['error']
    results['actual_absent_assembly_default_main'] = dict(returncode=rc, response=response)
finally:
    sys.argv = saved_argv

results['boundary'] = 'No genuine final assembly exists; no positive complete image/manifest admission or execution claim.'
results['writer_invocations'] = 0
results['device_network_process_helper_operations'] = 0
(ROOT / 'evidence/focused-offline.json').write_text(json.dumps(results, indent=2) + '\n')
print(json.dumps(results, indent=2))
