"""One actual installer main() PLAN, with explicitly limited public dependency readers."""
from pathlib import Path
import contextlib,hashlib,importlib.util,io,json,sys
sys.dont_write_bytecode=True
R=Path(__file__).resolve().parents[1];T=R.parent/'2026-11-07-asus-stock-kernel-version-control/artifacts/original.img'
assert not (R/'evidence/install-plan.json').exists(),'Exactly one PLAN main call'
def boundary(event,args):
 if event=='open' and any(s in str(args[0]) for s in ['/private/','/device-backup/','root_shell_wifi.py','mtk-su-mirror-b','/dev/']):raise RuntimeError('Prohibited input '+str(args[0]))
 if event.startswith(('subprocess.','socket.')) or event in ['os.system','os.posix_spawn']:raise RuntimeError('PLAN boundary '+event)
sys.addaudithook(boundary)
public=T.read_bytes();assert len(public)==7804928 and hashlib.sha256(public).hexdigest()=='f0bf4834a2d3ec207590c6742d0adb4fd9a3adc9a2dab5d0ec7c28f27963b140'
installer=R/'source/install.py';before=installer.read_bytes()
spec=importlib.util.spec_from_file_location('isolated_minimal_installer',installer);m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
assert m.INSTALL_PREIMAGES[-1]=='d78e6ddd7f4a555201515df3aef6d8d7f15203c20e3b8d201ea7eb2f4c5df081'
paths=[installer,Path(m.WIFI),Path(m.a.__file__),Path(m.b.__file__),Path(m.a.__file__).parent/'root_dispatch.py',R/'source/adb',R/'source/legacy_adb.py',R/'source/bootformat.py',R/'source/fdt.py',R/'source/minimal-profile.json']
pins={str(p):hashlib.sha256(p.read_bytes()).hexdigest() for p in paths}
def public_sources_only():
 for p,h in pins.items():assert hashlib.sha256(Path(p).read_bytes()).hexdigest()==h,p
# These are the only in-memory substitutions. The delivered readers/guards stay unchanged.
m.a.check_sources=public_sources_only
m.b.local_inputs=lambda:(public,[dict(public_header_template=str(T))])
sys.argv=[str(installer)];out=io.StringIO()
with (R/'evidence/plan-attempt.json').open('x') as f:json.dump(dict(main_calls_authorized=1,execute=False),f)
with contextlib.redirect_stdout(out):code=m.main()
result=json.loads(out.getvalue());assert code==0 and result['mode']=='PLAN_ONLY' and result['device_contacted'] is False and result['reboot'] is False
assert installer.read_bytes()==before
(R/'evidence/install-plan.json').write_text(json.dumps(result,indent=2)+'\n')
receipt=dict(exit=code,actual_main_PLAN_calls=1,delivered_installer_unchanged=True,no_device_contact=True,no_subprocess_or_socket=True,no_private_reads=True,public_code_pins=pins,substitutions=['a.check_sources: fixed public code/input-reader pins only, omitting inherited private root/source manifest chain','b.local_inputs: pinned public known-working original.img for stock header comparison only'],limitation='Private stock backups, root binary/helper dependencies and real current target identity/preimage were deliberately not validated. Delivered guards/readers remain original. Parent must run real PLAN/execute with complete private guards before a separately authorized physical trial; this is not physical GO.')
(R/'evidence/plan-isolation-receipt.json').write_text(json.dumps(receipt,indent=2)+'\n')
print(out.getvalue(),end='')
