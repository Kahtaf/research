from pathlib import Path
import remote,json
s=r'''
from pathlib import Path
import json,struct,hashlib,datetime
A=Path('/srv/android/lineage24');R=Path('/srv/android/asus-reviewed-build-kit/r9');F=Path('/srv/android/asus-reviewed-build-kit/r9-fixtures');p=A/'out/.siso_deps'
targets={'out/soong/.intermediates/system/bpf/loader/bpfloader/android_arm64_armv8-a/unstripped/bpfloader','out/soong/.intermediates/system/vold/libvold/android_arm64_armv8-a_static/obj/system/vold/model/PublicVolume.o','out/soong/.intermediates/system/vold/vold/android_arm64_armv8-a/unstripped/vold'}
alias={t:t for t in targets};alias.update({str(A/t):t for t in targets});selected_ids={};records={};node=0;h=hashlib.sha256()
def stream():
 with p.open('rb') as f:
  header=f.read(16);assert header==b'# ninjadeps\n'+struct.pack('<I',4)
  while True:
   b=f.read(4)
   if not b:return
   assert len(b)==4
   raw=struct.unpack('<I',b)[0];n=raw&0x7fffffff;assert n%4==0 and n<16*1024*1024
   data=f.read(n);assert len(data)==n
   yield bool(raw&0x80000000),data
for dep,data in stream():
 if not dep:
  name=data[:-4].rstrip(b'\0').decode();checksum=struct.unpack('<I',data[-4:])[0];assert checksum==(~node&0xffffffff)
  if name in alias:selected_ids[node]=alias[name]
  node+=1
 else:
  assert len(data)>=12;out,lo,hi=struct.unpack_from('<III',data)
  if out in selected_ids:records[selected_ids[out]]=dict(output_mtime_ns=lo|(hi<<32),dependency_ids=list(struct.unpack_from('<'+'I'*((len(data)-12)//4),data,12)))
needed={i for row in records.values() for i in row['dependency_ids']};names={};node=0
for dep,data in stream():
 if dep:continue
 if node in needed:names[node]=data[:-4].rstrip(b'\0').decode()
 node+=1
assert needed<=names.keys()
full={t:dict(output_mtime_ns=row['output_mtime_ns'],dependencies=[names[i] for i in row['dependency_ids']]) for t,row in records.items()}
with (F/'selected-native-dependencies.json').open('x') as f:json.dump(full,f,indent=2);f.write('\n')
with p.open('rb') as f:
 for b in iter(lambda:f.read(1048576),b''):h.update(b)
state=json.loads((R/'evidence/selected-siso-state-v2.json').read_text())['selected_entries']
r=dict(utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),source_deps_sha256=h.hexdigest(),format='Ninja deps v4 path-node records and output mtime/dependency-ID records; no per-input content digest fields',selected={t:dict(output_mtime_ns=row['output_mtime_ns'],dependency_count=len(row['dependencies']),dependency_paths_sha256=hashlib.sha256(json.dumps(row['dependencies'],separators=(',',':')).encode()).hexdigest(),current_siso_output_mtime_ns=state[t]['mod_time_ns'],matches_current_siso_output_mtime=row['output_mtime_ns']==state[t]['mod_time_ns']) for t,row in full.items()},vm_only_dependency_names_path=str(F/'selected-native-dependencies.json'),historical_input_content_identity_proven=False,cache_admitted=False)
with (R/'evidence/selected-siso-dependencies.json').open('x') as f:json.dump(r,f,indent=2);f.write('\n')
print(json.dumps(r,indent=2))
'''
r=remote.run(s);Path('2026-11-06-asus-r9-webview-continuation/evidence/selected-siso-dependencies.json').write_text(r);print(r)
