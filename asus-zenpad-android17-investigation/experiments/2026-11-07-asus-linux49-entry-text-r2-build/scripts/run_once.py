from pathlib import Path
import base64,datetime,hashlib,importlib.util,json,sys
R=Path(__file__).resolve().parents[1];W=R.parent
spec=importlib.util.spec_from_file_location('remote',W/'2026-11-06-asus-product-input-build-kit/scripts/remote.py');remote=importlib.util.module_from_spec(spec);spec.loader.exec_module(remote)
fix=W/'2026-11-07-asus-entry-checkpoint-dt-guard-fix'
pins=json.loads((fix/'evidence/post-pins.json').read_text())
for n,h in pins.items():assert hashlib.sha256((fix/n).read_bytes()).hexdigest()==h,n
files={}
for n in ['head.S','asus_retained_trace.c','asus_entry_text.S','asus_entry_tag.h']:files['kernel/arch/arm64/kernel/'+n]=(fix/'source/arch/arm64/kernel'/n).read_bytes()
for n in ['build.py','verify_remote.py']:files['scripts/'+n]=(R/'scripts'/n).read_bytes()
files['source/identity.json']=(R/'evidence/identity.json').read_bytes()
files['source/expected-runtime.dtb']=(R/'source/expected-runtime.dtb').read_bytes()
payload={n:base64.b64encode(d).decode() for n,d in files.items()}
selected=json.loads((W/'2026-11-07-asus-linux49-entry-text-checkpoint/evidence/source-copy.json').read_text())['selected_baseline']
script=r'''from pathlib import Path
import base64,json,subprocess,hashlib,shutil,os,datetime
R=Path('/srv/android/asus-linux49-entry-text-r2-build-20261107');B=Path('/srv/android/asus-early-watchdog-handoff-20261107')
assert not R.exists(),'Existing owned revision; no retry'
R.mkdir();[(R/n).mkdir() for n in ['out','tmp','source','scripts','evidence']]
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
selected=SELECTED
assert sha(B/'out/arch/arm64/boot/Image.gz-dtb')=='a49b87313d35d803e3ffaa2be2c60a3c678ccbc46efd5831651d2bd44ae4ee03'
for n,h in selected.items():assert sha(B/'kernel'/n)==h,n
subprocess.run(['cp','-a',str(B/'kernel'),str(R/'kernel')],check=True)
copy={n:{'sha256':sha(R/'kernel'/n),'independent_inode':(B/'kernel'/n).stat().st_ino!=(R/'kernel'/n).stat().st_ino} for n in selected}
assert all(v['independent_inode'] and v['sha256']==selected[n] for n,v in copy.items())
(R/'evidence/source-copy.json').write_text(json.dumps({'selected_baseline':selected,'selected_copy':copy,'full_tree_rehash':False},indent=2)+'\n')
shutil.copyfile(B/'out/.config',R/'out/.config')
assert sha(R/'out/.config')=='708a88175ea777c09410000dfe5cf562ccbf764955eb9deaadda7326d0a966e1'
files=PAYLOAD
for n,data in files.items():
 p=R/n;p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(base64.b64decode(data))
assert not (R/'kernel/arch/arm64/kernel/asus_entry_expected.inc').exists()
(R/'evidence/build-launch.json').write_text(json.dumps({'uploaded':{n:sha(R/n) for n in files},'compile_attempts':1,'no_build_wall_deadline':True},indent=2)+'\n')
with (R/'evidence/build-job.stdout').open('w') as out,(R/'evidence/build-job.stderr').open('w') as err:q=subprocess.run(['python3','-B',str(R/'scripts/build.py')],stdout=out,stderr=err)
assert q.returncode==0,(R/'evidence/build-job.stderr').read_text()[-2000:]
q=subprocess.run(['python3','-B',str(R/'scripts/verify_remote.py'),str(R)],capture_output=True,text=True)
(R/'evidence/linked-verification.stdout').write_text(q.stdout);(R/'evidence/linked-verification.stderr').write_text(q.stderr)
assert q.returncode==0,q.stderr[-2000:]
fetch={'artifacts/Image.gz-dtb':'out/arch/arm64/boot/Image.gz-dtb','artifacts/resolved.config':'out/.config'}
for n in ['source-copy.json','build-launch.json','build-status.json','build-receipt.json','linked-entry.json','compiled-initcalls.json','entry.disasm']:fetch['evidence/'+n]='evidence/'+n
result={n:{'base64':base64.b64encode((R/p).read_bytes()).decode(),'sha256':sha(R/p)} for n,p in fetch.items()}
log=R/'evidence/Image.gz-dtb.log';result['evidence/build-log-summary.json']={'text':json.dumps({'bytes':log.stat().st_size,'sha256':sha(log),'tail':log.read_text(errors='replace').splitlines()[-15:]},indent=2)+'\n'}
print(json.dumps(result))
'''.replace('SELECTED',repr(selected)).replace('PAYLOAD',repr(payload))
assert not (R/'evidence/parent-build-dispatch.json').exists()
(R/'evidence/parent-build-dispatch.json').write_text(json.dumps({'at':datetime.datetime.now(datetime.timezone.utc).isoformat(),'remote_root':'/srv/android/asus-linux49-entry-text-r2-build-20261107','attempts':1,'new_revision':True},indent=2)+'\n')
print('One complete build and linked verification dispatched; no automatic retry.',flush=True)
result=remote.run(script)
summary={}
for n,v in json.loads(result).items():
 p=R/n;p.parent.mkdir(parents=True,exist_ok=True)
 if 'base64' in v:
  data=base64.b64decode(v['base64']);assert hashlib.sha256(data).hexdigest()==v['sha256'];p.write_bytes(data);summary[n]={'bytes':len(data),'sha256':v['sha256']}
 else:p.write_text(v['text'])
(R/'evidence/fetch-receipt.json').write_text(json.dumps(summary,indent=2)+'\n')
print(json.dumps({k:v for k,v in summary.items() if k.startswith('artifacts/')}),flush=True)
