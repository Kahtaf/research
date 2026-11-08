"""Exactly one main PLAN, isolated from devices, private data and stock payloads."""
from pathlib import Path
import contextlib,hashlib,importlib.util,io,json,sys
sys.dont_write_bytecode=True
R=Path(__file__).resolve().parents[1];B=R.parent/'2026-11-08-asus-minimal-platform-build-r3'
assert not (R/'evidence/plan-attempt.json').exists(),'One isolated PLAN only'
reads=[]
def boundary(event,args):
 if event=='open':
  p=str(args[0])
  if any(s in p for s in ['/private/','/device-backup/','root_shell_wifi.py','mtk-su-mirror-b','/dev/','/original.img','/.ssh/']):raise RuntimeError('Prohibited input '+p)
  if isinstance(args[0],str):reads.append(p)
 if event.startswith(('subprocess.','socket.')) or event in ['os.system','os.posix_spawn']:raise RuntimeError('PLAN boundary '+event)
sys.addaudithook(boundary)
fixture=B/'artifacts/candidate.img';public=fixture.read_bytes();assert hashlib.sha256(public).hexdigest()=='7ccd7d4554a764d0717c79d30668626c1fbd032218f8598bf7e4a2913bce30a1'
installer=R/'source/install.py';before=installer.read_bytes();spec=importlib.util.spec_from_file_location('isolated_delay_installer',installer);m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
assert m.INSTALL_PREIMAGES[-1]=='9939e802ab349dd01fe5ab9c643f2ce0d3219846e3f54513a9b1e9982146965c'
paths=[installer,Path(m.WIFI),Path(m.a.__file__),Path(m.b.__file__),Path(m.a.__file__).parent/'root_dispatch.py',R/'source/adb',R/'source/legacy_adb.py',R/'source/bootformat.py',R/'source/fdt.py',R/'source/minimal-profile.json']
pins={str(p):hashlib.sha256(p.read_bytes()).hexdigest() for p in paths}
def public_sources_only():
 for p,h in pins.items():assert hashlib.sha256(Path(p).read_bytes()).hexdigest()==h,p
m.a.check_sources=public_sources_only
m.b.local_inputs=lambda:(public,[dict(public_diagnostic_ancestor_header_fixture=str(fixture))])
sys.argv=[str(installer)];out=io.StringIO()
with (R/'evidence/plan-attempt.json').open('x') as f:json.dump(dict(main_calls_authorized=1,execute=False),f)
with contextlib.redirect_stdout(out):code=m.main()
result=json.loads(out.getvalue());assert code==0 and result['mode']=='PLAN_ONLY' and result['device_contacted'] is False and result['reboot'] is False
assert installer.read_bytes()==before
(R/'evidence/install-plan.json').write_text(json.dumps(result,indent=2)+'\n')
receipt=dict(exit=code,actual_main_PLAN_calls=1,delivered_installer_unchanged=True,no_device_contact=True,no_subprocess_or_socket=True,no_private_or_stock_payload_reads=True,public_code_pins=pins,substitutions=['a.check_sources: fixed public code/input pins, without private root/source manifest chain','b.local_inputs: exact public r3 diagnostic candidate, solely for inherited header geometry comparison; no original/stock payload read'],reads=sorted(set(reads)),limitation='Private stock backup/root dependency chains, real current identity/preimage, real stock header comparison and physical transport were not validated. Delivered readers, execute, Transport and Guard remain unchanged. Parent must run real PLAN with its existing complete dependency chain before any separately owned physical phase. No physical GO.')
(R/'evidence/plan-isolation-receipt.json').write_text(json.dumps(receipt,indent=2)+'\n');print(out.getvalue(),end='')
