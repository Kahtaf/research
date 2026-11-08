from pathlib import Path
import hashlib,json,shutil,datetime,re
R=Path('/srv/android/asus-build-continuation');E=R/'integration-r5/runtime-evidence';E.mkdir(exist_ok=True)
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def take(root,rel,owner):
 p=root/rel
 if not p.exists():return {'exists':False}
 assert p.stat().st_size<2_000_000,(p,p.stat().st_size)
 q=E/owner/rel;q.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(p,q);return dict(sha256=sha(p),bytes=p.stat().st_size)
F=Path('/srv/android/asus-firstboot-runtime');N=Path('/srv/android/asus-network-runtime');records={}
frels=['evidence/kernel-r7-status.json','evidence/kernel-r7-hashes.json','evidence/kernel-r7-command.json','evidence/firstboot-config-equivalence-r3.json','evidence/qualification-r2-equivalence-failure.json','evidence/qualification-r3.json']
for run in ['run-boot-r9','run-boot-r10','run-boot-r11','run-cpuset-r2','run-cpuset-r3','run-policy-r3','run-policy-r4','run-locks-r1']:
 frels.extend(run+'/'+n for n in ['status.json','command.json','serial.log'])
for rel in frels:records['firstboot/'+rel]=take(F,rel,'firstboot')
assert json.loads((F/'evidence/kernel-r7-status.json').read_text())['returncode']==0
hashes=json.loads((F/'evidence/kernel-r7-hashes.json').read_text())
for p,h in hashes.items():assert sha(F/p)==h
# The existing r7 compile is terminal; there is no r7 runtime receipt to adopt.
command=json.loads((F/'run-boot-r10/command.json').read_text());assert 'kernel-build-r6' in command[command.index('-kernel')+1]
for rel in ['manifest.json','evidence/run-r14/result.json','evidence/run-r14/serial.log','evidence/network-config-equivalence.json','evidence/network-source-equivalence.json']:
 records['network/handoff-r1/'+rel]=take(N/'handoff-r1',rel,'network/handoff-r1')
for run in ['run-r16','run-r18']:
 for rel in ['result.json','serial.log','inputs.json','qemu-command.json']:
  records['network/'+run+'/'+rel]=take(N,run+'/'+rel,'network')
first=json.loads((R/'evidence/firstboot-cgroups-applied.json').read_text())
for rel,h in first['patches'].items():
 p=R/'inputs/firstboot-cgroups-r1'/rel
 assert sha(p)==h
 records['firstboot/patches/'+rel]=take(R/'inputs/firstboot-cgroups-r1',rel,'firstboot/patches')
for row in first['files']:assert sha(R/'kernel'/row['path'])==row['after_sha256']
summary=dict(utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),files=records,firstboot_r7_compile_exit=0,firstboot_r7_hashes_verified=hashes,firstboot_r10_kernel=command[command.index('-kernel')+1],firstboot_r7_runtime_accepted=False,missing_firstboot_runs=[r for r in ['run-boot-r11','run-cpuset-r3','run-policy-r4','run-locks-r1'] if not (F/r/'status.json').exists()],firstboot_runtime_limit='Earlier r6 cpuset/init/ueventd/property observations retained; FILE_LOCKING=y parity rerun missing. Do not claim r7 full runtime qualification.',network_manifest=sha(N/'handoff-r1/manifest.json'),optional_patch12_applied=False,optional_patch12_reason='No frozen qualified supplement found in inspected local/remote handoff or artifacts; run16 alone does not close real property-service/full-product boundary.',full_Android_Java_WiFi_metrics_runtime_qualified=False)
(E/'summary.json').write_text(json.dumps(summary,indent=2)+'\n')
print('Captured',len(records),'compact evidence entries; firstboot r7 compile passed; runtime parity remains unproved.')
