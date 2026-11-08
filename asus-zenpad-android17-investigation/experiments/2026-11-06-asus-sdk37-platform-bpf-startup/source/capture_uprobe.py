from pathlib import Path
import os,hashlib,json,subprocess as s,re,shutil
os.sched_setaffinity(0,{min(os.sched_getaffinity(0))})
O=Path('/srv/android/asus-sdk37-platform-bpf-startup-20261106');T=Path('/srv/android/lineage24');D=O/'inputs/runtime-root-r2';rel='apex/com.android.uprobestats/bin/uprobestatsbpfload';target='out/target/product/p00a/'+rel
assert rel in (O/'inputs/actual/out/target/product/p00a/.installable_files').read_text().split()
edge=None
for l in (T/'out/build-lineage_p00a.ninja').open():
 if l.startswith('build '+target+':'):edge=l.strip();break
assert edge, 'No install edge for selected UprobeStats loader'
source=edge.split(':',1)[1].split()[1];assert (T/source).is_file(),source
manifest={}
def copy(p,rel):
 dest=O/rel;dest.parent.mkdir(parents=True,exist_ok=True);a=hashlib.sha256(p.read_bytes()).hexdigest();shutil.copyfile(p,dest);assert a==hashlib.sha256(p.read_bytes()).hexdigest()==hashlib.sha256(dest.read_bytes()).hexdigest();manifest[str(rel)]={'source':str(p),'sha256':a,'bytes':dest.stat().st_size};return dest
loader=copy(T/source,Path('inputs/runtime-root-r2')/rel)
for src in ['packages/modules/UprobeStats/bpfloader/UprobeStatsBpfLoad.cpp','packages/modules/UprobeStats/bpfloader/Android.bp']:
 copy(T/src,Path('inputs/object-source')/src)
q=s.run(['aarch64-linux-gnu-readelf','-d',str(loader)],capture_output=True,text=True);needed=re.findall(r'Shared library: \[(.*?)\]',q.stdout)
missing=[n for n in needed if not (D/'system/lib64'/n).is_file()]
assert not missing,missing
(O/'evidence/uprobe-loader.json').write_text(json.dumps({'install_edge':edge,'needed':needed,'files':manifest},indent=2)+'\n')
print(json.dumps({'install_edge':edge,'needed':needed,'missing_libraries':missing}))
