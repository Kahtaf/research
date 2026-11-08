"""One isolated real main() PLAN branch; prohibited dependency readers substituted in memory only."""
from pathlib import Path
import contextlib,hashlib,importlib.util,io,json,sys
R=Path(__file__).resolve().parents[1]
T=R.parent/'2026-11-07-asus-early-retained-kernel-probe/artifacts/candidate.img'
public=T.read_bytes()
assert len(public)==8044544 and hashlib.sha256(public).hexdigest()=='2a0d400811292ece957bb00f632f56aef8e5967643bd5a0184c10eaeea051533'
assert not (R/'evidence/install-plan.json').exists(), 'One PLAN call only'
def boundary(event,args):
 if event=='open':
  p=str(args[0])
  assert not any(s in p for s in ['/private/','/device-backup/','root_shell_wifi.py','mtk-su-mirror-b','/dev/']), ('Prohibited input',p)
 if event.startswith(('subprocess.','socket.')) or event in ['os.system','os.posix_spawn']:
  raise RuntimeError('PLAN may not contact device or run subprocess: '+event)
sys.addaudithook(boundary)
spec=importlib.util.spec_from_file_location('linux_owned_installer',R/'source/install.py')
m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
# The unchanged default inputs() otherwise hashes a root binary and reads stock backups.
# Preserve the delivered file and exercise its candidate/hash/header PLAN path with public geometry.
m.b.local_inputs=lambda:(public,[dict(public_header_template=str(T))])
m.a.check_sources=lambda:None
sys.argv=[str(R/'source/install.py')]
out=io.StringIO()
with contextlib.redirect_stdout(out):exit_code=m.main()
assert exit_code==0
result=json.loads(out.getvalue());assert result['mode']=='PLAN_ONLY' and result['device_contacted'] is False and result['reboot'] is False
(R/'evidence/install-plan.json').write_text(json.dumps(result,indent=2)+'\n')
receipt=dict(exit=exit_code,actual_installer_main_calls=1,mode='ISOLATED_PLAN_ONLY',delivered_installer_modified=False,device_contacted=False,subprocesses_allowed=False,prohibited_input_access=False,public_header_template_sha256=hashlib.sha256(public).hexdigest(),in_memory_substitutions=['b.local_inputs: pinned public prior candidate for stock header comparison','a.check_sources: no-op to avoid preserved manifest root-helper reads'],limitation='Private stock backups and root dependency hashes are deliberately not validated by this isolated PLAN. Parent execution retains all original input/source guards.')
(R/'evidence/plan-isolation-receipt.json').write_text(json.dumps(receipt,indent=2)+'\n')
print(out.getvalue(),end='')
