from pathlib import Path
import json,gzip,struct,hashlib,time
A=Path('/srv/android/lineage24')
B='out/soong/.intermediates/system/bpf/loader/bpfloader/android_arm64_armv8-a/'
V='out/soong/.intermediates/system/vold/'
paths=[B+'unstripped/bpfloader',B+'bpfloader',V+'libvold/android_arm64_armv8-a_static/obj/system/vold/model/PublicVolume.o',V+'vold/android_arm64_armv8-a/unstripped/vold',V+'vold/android_arm64_armv8-a/vold','out/target/product/p00a/system/bin/bpfloader','out/target/product/p00a/system/bin/vold','system/bpf/loader/bpfloader.rs','system/vold/model/PublicVolume.cpp','prebuilts/clang/host/linux-x86/clang-r584948b/bin/clang++','prebuilts/rust-toolchain/linux-x86/1.93.1/bin/rustc']
wanted=set(paths)|{str(A/p) for p in paths}
def vi(f):
 n=0;s=0
 while True:
  b=f.read(1)
  if not b:
   if s:raise EOFError()
   return None
  k=b[0];n|=(k&127)<<s
  if k<128:return n
  s+=7
  assert s<70

def fields(b):
 import io
 f=io.BytesIO(b);out={}
 while (tag:=vi(f)) is not None:
  num,typ=tag>>3,tag&7
  if typ==0:v=vi(f)
  elif typ==2:
   n=vi(f);v=f.read(n);assert len(v)==n
  elif typ==1:v=f.read(8)
  elif typ==5:v=f.read(4)
  else:raise ValueError(typ)
  out.setdefault(num,[]).append(v)
 return out

def one(d,k,default=None):return d.get(k,[default])[0]
def dg(b):
 if not b:return None
 d=fields(b);return {'hash':one(d,1,b'').decode(),'size_bytes':one(d,2,0)}
def entry(b):
 d=fields(b);return {'name':one(d,2,b'').decode(),'mtime_ns':one(fields(one(d,1,b'')),1,0),'digest':dg(one(d,3)),'cmd_hash_hex':one(d,6,b'').hex(),'edge_hash_hex':one(d,9,b'').hex(),'action':dg(one(d,7)),'updated_time_ns':one(d,8,0),'local':one(d,10,0),'target':one(d,5,b'').decode()}
paths=['out/soong/.intermediates/system/vold/libvold/android_arm64_armv8-a_static/libvold.a']
wanted=set(paths)|{str(A/p) for p in paths}
out={'read_started_ns':time.time_ns(),'selected_paths':paths,'fs_state_entries':[],'selected_files':{},'current_ninja_rows':[]}
p=A/'out/.siso_fs_state';s=p.stat();out['state_before']={'bytes':s.st_size,'mtime_ns':s.st_mtime_ns}
with gzip.open(p,'rb') as f:
 entries=0;plain=0
 while (tag:=vi(f)) is not None:
  assert tag&7==2,tag
  n=vi(f);assert n<4*1024*1024;nbytes=f.read(n);assert len(nbytes)==n;plain+=n
  assert plain<1024**3
  if tag>>3==1:
   entries+=1
   # Filter before decoding fields; retain only the selected paths.
   if any(x.encode() in nbytes for x in paths):
    e=entry(nbytes)
    if e['name'] in wanted:out['fs_state_entries'].append(e)
 out['state_scanned_entries']=entries;out['state_uncompressed_payload_bytes']=plain
s=p.stat();out['state_after']={'bytes':s.st_size,'mtime_ns':s.st_mtime_ns}
for path in paths:
 p=A/path
 if p.is_file():
  s=p.stat();h=hashlib.sha256();assert s.st_size<128*1024*1024
  with p.open('rb') as f:
   while b:=f.read(1024*1024):h.update(b)
  out['selected_files'][path]={'bytes':s.st_size,'mtime_ns':s.st_mtime_ns,'sha256':h.hexdigest(),'symlink':p.is_symlink()}
for line in (A/'out/.ninja_log').open():
 f=line.rstrip().split('\t')
 if len(f)==5 and f[3] in wanted:out['current_ninja_rows'].append(line.rstrip())
out['read_finished_ns']=time.time_ns()
print(json.dumps(out,indent=2))
