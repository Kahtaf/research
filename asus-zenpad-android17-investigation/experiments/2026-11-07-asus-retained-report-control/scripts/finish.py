from pathlib import Path
import hashlib,json,importlib.util,base64
R=Path(__file__).resolve().parents[1];W=R.parent
sha=lambda data:hashlib.sha256(data).hexdigest()
pkg=json.loads((R/'evidence/packaging-receipt.json').read_text());plan=json.loads((R/'evidence/install-plan.json').read_text());patch=json.loads((R/'evidence/next-trace-patch.json').read_text());remote=json.loads((R/'evidence/remote-delivery.json').read_text())
for rel,expect in [('artifacts/candidate.img',pkg['image']),('artifacts/candidate.p10.raw',pkg['full_p10']),('artifacts/init',{k:pkg['init'][k] for k in ['bytes','sha256']})]:
 data=(R/rel).read_bytes();assert dict(bytes=len(data),sha256=sha(data))==expect
for rel,expect in remote.items():
 data=(R/rel).read_bytes();assert dict(bytes=len(data),sha256=sha(data))==expect
assert plan['mode']=='PLAN_ONLY' and plan['device_contacted'] is False and plan['candidate_sha256']==pkg['image']['sha256'] and plan['full_p10_sha256']==pkg['full_p10']['sha256']
assert json.loads((R/'evidence/helper-compile.json').read_text())['compiler_invocations']==1
size=sum(p.stat().st_size for p in R.rglob('*') if p.is_file());assert size<32*1024**2
receipt=dict(status='ONE_STOCK_CONTROL_READY_PLAN_ONLY_NEXT_TRACE_PATCH_STAGED',remote_prefix='/srv/android/asus-retained-report-control-20261107',candidate=pkg['image'],full_p10=pkg['full_p10'],init=pkg['init'],marker=pkg['marker'],kmsg_bytes=95,next_trace_patch=patch['patch_sha256'],next_trace_compiled=False,helper_compiler_invocations=1,actual_plan=plan,public_packet_bytes_before_receipt_and_sums=size,below_32MiB=True,device_contact=False,deployment=False,physical_retention_proven=False,full_linux49_rebuild=False,old_sources_artifacts_preserved=True,next_action='Root preserves prior SD report, owns one physical stock control and immediate complete last_kmsg collection; use README commands and exact pins.')
(R/'evidence/RECEIPT.json').write_text(json.dumps(receipt,indent=2)+'\n')
sums=''.join(f'{sha(p.read_bytes())}  {p.relative_to(R)}\n' for p in sorted(R.rglob('*')) if p.is_file() and p.name!='SHA256SUMS')
(R/'SHA256SUMS').write_text(sums)
# Final small manifest/docs sync; no compiler, device or active-source operations.
spec=importlib.util.spec_from_file_location('remote',W/'2026-11-06-asus-product-input-build-kit/scripts/remote.py');m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
payload={p:base64.b64encode((R/p).read_bytes()).decode() for p in ['README.md','evidence/RECEIPT.json','SHA256SUMS']}
result=json.loads(m.run(f'''from pathlib import Path
import base64,hashlib,json
R=Path('/srv/android/asus-retained-report-control-20261107')
for rel,data in {payload!r}.items():(R/rel).write_bytes(base64.b64decode(data))
print(json.dumps({{rel:hashlib.sha256((R/rel).read_bytes()).hexdigest() for rel in {list(payload)!r}}}))'''))
assert all(result[p]==sha((R/p).read_bytes()) for p in payload)
print(json.dumps(receipt,indent=2))
