from pathlib import Path
import json,struct,time
A=Path('/srv/android/lineage24');p=A/'out/.siso_deps'
B='out/soong/.intermediates/system/bpf/loader/bpfloader/android_arm64_armv8-a/unstripped/bpfloader'
V='out/soong/.intermediates/system/vold/libvold/android_arm64_armv8-a_static/obj/system/vold/model/PublicVolume.o'
L='out/soong/.intermediates/system/vold/vold/android_arm64_armv8-a/unstripped/vold'
wanted={B,V,L};out={'read_started_ns':time.time_ns(),'before':{'bytes':p.stat().st_size,'mtime_ns':p.stat().st_mtime_ns},'targets':{}};ids={};deps={};names={}
def records():
 with p.open('rb') as f:
  assert f.read(16)==b'# ninjadeps\n\x04\x00\x00\x00'
  idx=0
  while h:=f.read(4):
   assert len(h)==4
   v=struct.unpack('<I',h)[0];n=v&0x7fffffff;assert 4<=n<=4*1024*1024
   b=f.read(n);assert len(b)==n
   if v>>31:yield 'deps',struct.unpack_from('<I',b)[0],b
   else:
    assert (struct.unpack_from('<I',b,n-4)[0]^0xffffffff)==idx
    yield 'path',idx,b[:-4].rstrip(b'\x00');idx+=1
for kind,i,b in records():
 if kind=='path':
  name=b.decode()
  if name in wanted:ids[i]=name;names[i]=name
 elif i in ids:
  vals=struct.unpack('<'+'I'*(len(b)//4),b);deps[i]={'mtime_ns':vals[1]|vals[2]<<32,'dependency_ids':list(vals[3:])}
needed={j for v in deps.values() for j in v['dependency_ids']}
for kind,i,b in records():
 if kind=='path' and i in needed:names[i]=b.decode()
for i,name in ids.items():
 d=deps.get(i)
 if d:
  d['dependencies']=[names[j] for j in d.pop('dependency_ids')];d['count']=len(d['dependencies']);d['output_mtime_ns']=(A/name).stat().st_mtime_ns
 out['targets'][name]=d
out['missing_target_entries']=sorted(wanted-set(ids.values()));out['after']={'bytes':p.stat().st_size,'mtime_ns':p.stat().st_mtime_ns};out['read_finished_ns']=time.time_ns()
print(json.dumps(out,indent=2))
