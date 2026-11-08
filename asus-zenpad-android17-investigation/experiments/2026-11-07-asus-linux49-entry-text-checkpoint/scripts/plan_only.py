"""Exactly one isolated installer main() PLAN; no private/device input readers."""
from pathlib import Path
import contextlib
import hashlib
import importlib.util
import io
import json
import sys

sys.dont_write_bytecode = True
ROOT = Path(__file__).resolve().parents[1]
TEMPLATE = ROOT.parent / '2026-11-07-asus-stock-kernel-version-control/artifacts/original.img'
assert not (ROOT / 'evidence/install-plan.json').exists(), 'One PLAN only'


def boundary(event, args):
    if event == 'open':
        path = str(args[0])
        assert not any(s in path for s in ('/private/', '/device-backup/', 'root_shell_wifi.py', 'mtk-su-mirror-b', '/dev/')), ('Prohibited input', path)
    if event.startswith(('subprocess.', 'socket.')) or event in ('os.system', 'os.posix_spawn'):
        raise RuntimeError('PLAN cannot run subprocesses or contact device: ' + event)


sys.addaudithook(boundary)
public = TEMPLATE.read_bytes()
assert len(public) == 7804928 and hashlib.sha256(public).hexdigest() == 'f0bf4834a2d3ec207590c6742d0adb4fd9a3adc9a2dab5d0ec7c28f27963b140'
installer = ROOT / 'source/install.py'
before = installer.read_bytes()
spec = importlib.util.spec_from_file_location('linux49_entry_text_installer', installer)
m = importlib.util.module_from_spec(spec)
spec.loader.exec_module(m)
assert 'd6949069eaa498fcfbc27be707d01dffd7099992c5eb71e2c7c3926639851355' in m.INSTALL_PREIMAGES
assert '902b2f06a01cca574b4aa374e67c4e7f8f0ed53f6e6a55017b6d96351f0f1f20' in m.INSTALL_PREIMAGES
m.b.local_inputs = lambda: (public, [dict(public_header_template=str(TEMPLATE))])
m.a.check_sources = lambda: None
sys.argv = [str(installer)]
out = io.StringIO()
with contextlib.redirect_stdout(out):
    code = m.main()
assert code == 0 and installer.read_bytes() == before
result = json.loads(out.getvalue())
assert result['mode'] == 'PLAN_ONLY' and result['device_contacted'] is False and result['reboot'] is False
(ROOT / 'evidence/install-plan.json').write_text(json.dumps(result, indent=2) + '\n')
receipt = dict(
    exit=code, actual_installer_main_calls=1, mode='ISOLATED_PLAN_ONLY',
    delivered_installer_modified=False, device_contacted=False, subprocesses_allowed=False,
    prohibited_input_access=False, original_stock_and_parent_current_preimages_admitted=True,
    public_header_template_sha256=hashlib.sha256(public).hexdigest(),
    delivered_installer_sha256=hashlib.sha256(before).hexdigest(),
    in_memory_substitutions=[
        'b.local_inputs: pinned public known-working original.img for stock header geometry comparison',
        'a.check_sources: no-op to avoid preserved manifest root-helper reads',
    ],
    limitation='Private stock backup and root dependency/source hashes were deliberately not validated. Delivered installer retains every original guard and input reader. Parent owns fresh identity/preimage checks and all physical operations. No physical/fullOS GO.',
)
(ROOT / 'evidence/plan-isolation-receipt.json').write_text(json.dumps(receipt, indent=2) + '\n')
print(out.getvalue(), end='')
