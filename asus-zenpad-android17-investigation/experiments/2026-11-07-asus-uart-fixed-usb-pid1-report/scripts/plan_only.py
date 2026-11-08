"""Exactly one isolated main() PLAN; restricted readers replaced in memory only."""
from pathlib import Path
import contextlib
import hashlib
import importlib.util
import io
import json
import sys

sys.dont_write_bytecode = True
R = Path(__file__).resolve().parents[1]
T = R.parent / '2026-11-07-asus-early-uart-disabled-kernel/artifacts/candidate.img'
assert not (R / 'evidence/install-plan.json').exists(), 'One PLAN only'


def boundary(event, args):
    if event == 'open':
        path = str(args[0])
        assert not any(s in path for s in ['/private/', '/device-backup/', 'root_shell_wifi.py', 'mtk-su-mirror-b', '/dev/']), ('Prohibited input', path)
    if event.startswith(('subprocess.', 'socket.')) or event in ['os.system', 'os.posix_spawn']:
        raise RuntimeError('PLAN cannot run subprocesses or contact device: '+event)


sys.addaudithook(boundary)
public = T.read_bytes()
assert len(public) == 8038400 and hashlib.sha256(public).hexdigest() == '1d406f3416e94e54219935cb76de338e10d3155fe555baad6cb7c2e38068c95d'
installer = R / 'source/install.py'
before = installer.read_bytes()
spec = importlib.util.spec_from_file_location('uart_fixed_usb_installer', installer)
m = importlib.util.module_from_spec(spec)
spec.loader.exec_module(m)
m.b.local_inputs = lambda: (public, [dict(public_header_template=str(T))])
m.a.check_sources = lambda: None
sys.argv = [str(installer)]
out = io.StringIO()
with contextlib.redirect_stdout(out):
    code = m.main()
assert code == 0 and installer.read_bytes() == before
result = json.loads(out.getvalue())
assert result['mode'] == 'PLAN_ONLY' and result['device_contacted'] is False and result['reboot'] is False
(R / 'evidence/install-plan.json').write_text(json.dumps(result, indent=2)+'\n')
receipt = dict(exit=code, actual_installer_main_calls=1, mode='ISOLATED_PLAN_ONLY', delivered_installer_modified=False, device_contacted=False, subprocesses_allowed=False, prohibited_input_access=False, public_header_template_sha256=hashlib.sha256(public).hexdigest(), delivered_installer_sha256=hashlib.sha256(before).hexdigest(),
    in_memory_substitutions=['b.local_inputs: pinned public current UART-disabled candidate for geometry comparison', 'a.check_sources: no-op to avoid preserved manifest root-helper reads'],
    limitation='Private stock backups and root dependency hashes were deliberately not validated by this isolated PLAN. Delivered installer retains all original input/source guards. This is no physical/fullOS GO.')
(R / 'evidence/plan-isolation-receipt.json').write_text(json.dumps(receipt, indent=2)+'\n')
print(out.getvalue(), end='')
