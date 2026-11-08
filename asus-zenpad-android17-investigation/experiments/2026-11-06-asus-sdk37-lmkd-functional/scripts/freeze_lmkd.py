from pathlib import Path
import subprocess as s,shlex,json,hashlib,re,shutil,datetime
A=Path('/srv/android/lineage24');R=Path('/srv/android/asus-sdk37-lmkd-functional');I=R/'inputs/native-r1';I.mkdir()
D=A/'out/soong/.intermediates/system/memory/lmkd/lmkd/android_arm64_armv8-a/unstripped/lmkd'
pending=[D];selected={};rsps={};manifest=[]
def sha(f):return hashlib.sha256(f.read_bytes()).hexdigest()
while pending:
 f=pending.pop();name=f.name
 if name in selected:
  assert sha(f)==sha(selected[name]),(f,selected[name]);continue
 assert f.is_file(),f
 selected[name]=f
 rp=Path(str(f)+'.rsp') if 'unstripped' in str(f) else f.parent/'unstripped'/(name+'.rsp')
 if rp.exists():
  txt=rp.read_text();rsps[str(rp)]=txt
  pending += [A/v for v in shlex.split(txt) if v.endswith('.so')]
needed={}
for name,f in selected.items():
 p=s.run(['aarch64-linux-gnu-readelf','-hld',str(f)],capture_output=True,text=True,check=True);(I/(name+'.readelf')).write_text(p.stdout)
 needed[name]=re.findall(r'\(NEEDED\).*?\[(.*?)\]',p.stdout)
for name,libs in needed.items():
 for lib in libs:assert lib in selected,(name,'missing transitive library',lib)
# Existing linker ELF is a genuine frozen r5 output, sourced in the earlier firstboot manifest.
selected['linker64']=Path('/srv/android/asus-firstboot-runtime/inputs/boot-r10/root/system/bin/linker64')
before={name:sha(f) for name,f in selected.items()}
for name,f in selected.items():
 dst=I/name;shutil.copyfile(f,dst);dst.chmod(0o755)
 manifest.append(dict(name=name,source=str(f),bytes=dst.stat().st_size,sha256=sha(dst),mtime_ns=f.stat().st_mtime_ns))
after={name:sha(f) for name,f in selected.items()};assert before==after;assert all(x['sha256']==before[x['name']] for x in manifest)
(I/'manifest.json').write_text(json.dumps(manifest,indent=2));(I/'link-response-files.json').write_text(json.dumps(rsps,indent=2));(I/'needed.json').write_text(json.dumps(needed,indent=2))
provenance={'utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'source_head':s.check_output(['git','-C',str(A/'system/memory/lmkd'),'rev-parse','HEAD'],text=True).strip(),'source_status':s.check_output(['git','-C',str(A/'system/memory/lmkd'),'status','--porcelain'],text=True),'coherent_double_hash':before==after,'total_bytes':sum(x['bytes'] for x in manifest),'parent_build':'/srv/android/asus-genuine-service-build-r1','full_build_success_claim':False}
(I/'provenance.json').write_text(json.dumps(provenance,indent=2));print(json.dumps(provenance,indent=2));print('files',len(manifest))
