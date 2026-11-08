from pathlib import Path
import os,hashlib,json,re,shutil,subprocess as s
os.sched_setaffinity(0,{min(os.sched_getaffinity(0))})
T=Path('/srv/android/lineage24');O=Path('/srv/android/asus-sdk37-platform-bpf-startup-20261106');P='out/target/product/p00a/'
def sha(p):
 with p.open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
selected=sorted(x for x in (O/'inputs/actual/out/target/product/p00a/.installable_files').read_text().split() if '/etc/bpf/' in x)
edges={};blocks={};graphpins={};image_deps=[];rsp_selected=[]
graphs=[T/'out/build-lineage_p00a.ninja']
for p in graphs:
 h=hashlib.sha256();current=None;pending=''
 for raw in p.open('rb'):
  h.update(raw);l=pending+raw.decode()
  if l.endswith('$\n'):pending=l[:-2];continue
  pending='';key=l.split(':',1)[0]
  if l.startswith('build '):
   current=None
   if 'bpf' in key.lower() or 'filterPowerSupplyEvents' in key:
    target=key[6:];current=target;blocks[target]={'graph':str(p.relative_to(T)),'text':l};deps=l.split(':',1)[1].split();edges[target]=deps[1:]
   if l.startswith('build '+P+'obj/PACKAGING/system_intermediates/system.img:'):image_deps=[x for x in l.split() if '/etc/bpf/' in x]
  elif current and l.startswith(' '):blocks[current]['text']+=l
  else:current=None
  if 'rspfile_content = ' in l and 'system_intermediates/file_list.txt' in l:rsp_selected+=re.findall(r'echo "([^"]*etc/bpf/[^"]*)"',l)
 graphpins[str(p.relative_to(T))]={'sha256':h.hexdigest(),'size':p.stat().st_size}
(O/'evidence/graph-pins-v2.json').write_text(json.dumps(graphpins,indent=2)+'\n')
rows=[];captured={};needed=set()
def save(p,rel):
 d=O/rel;d.parent.mkdir(parents=True,exist_ok=True);a=sha(p);shutil.copyfile(p,d);assert a==sha(p)==sha(d);return a
for rel in selected:
 root=P+rel;seen=set();queue=[root];candidates=[]
 while queue:
  node=queue.pop(0)
  if node in seen:continue
  seen.add(node)
  if node in blocks:needed.add(node)
  if node.endswith(('.bpf','.o')):
   candidates.append(node)
   queue.extend(x for x in edges.get(node,[]) if x.endswith(('.bpf','.o')))
 avail=[x for x in candidates if (T/x).is_file()];row={'install_path':rel,'selected_by':'.installable_files','system_image_dependency':root in image_deps,'system_image_file_list':rel.removeprefix('system/') in rsp_selected,'graph_output_chain':candidates,'available_outputs':{x:{'sha256':sha(T/x),'bytes':(T/x).stat().st_size} for x in avail}}
 if avail:
  source=T/avail[0];row['captured_source']=str(source);row['sha256']=save(source,'inputs/selected-root-v2/'+rel)
  md=O/'evidence/object-metadata-v2'/ (rel.replace('/','__')+'.txt');md.parent.mkdir(exist_ok=True)
  q=s.run([str(T/'prebuilts/clang/host/linux-x86/clang-r584948b/bin/llvm-readelf'),'--all','--hex-dump=.maps','--hex-dump=maps','--hex-dump=progs',str(source)],capture_output=True,text=True);md.write_text(q.stdout+q.stderr);row['metadata']=str(md.relative_to(O))
 else:row['missing']=True
 rows.append(row)
# Freeze only source/build declarations reached through the BPF objects, not broad source trees.
sources={}
all_nodes=set(needed)
for row in rows:all_nodes.update(row['graph_output_chain'])
for target in all_nodes:
 for dep in edges.get(target,[]):
  if dep.endswith(('.c','.h','.bp')) and (T/dep).is_file():sources[dep]=save(T/dep,'inputs/object-source/'+dep)
 # Module source directory is encoded before /<name>.bpf/android_ in Soong targets.
 m=re.search(r'out/soong/\.intermediates/(.*?)/[^/]+\.(?:bpf|o)/android_',target)
 if m:
  d=Path(m.group(1));bp=T/d/'Android.bp'
  if bp.is_file():
   sources[str(d/'Android.bp')]=save(bp,Path('inputs/object-source')/d/'Android.bp')
   for src in re.findall(r'"([^"]+\.c)"',bp.read_text()):
    q=T/d/src
    if q.is_file():sources[str(d/src)]=save(q,Path('inputs/object-source')/d/src)
(O/'evidence/selection-v2.json').write_text(json.dumps({'objects':rows,'system_image_bpf_dependencies':image_deps,'system_image_file_list_bpf':rsp_selected,'source_hashes':sources,'boundary':'Install graph and .installable_files; APEX UprobeStats is separately owned by its service, not Rust platform FILE_ARR.'},indent=2)+'\n')
(O/'evidence/selected-graph-edges-v2.json').write_text(json.dumps({k:blocks[k] for k in sorted(needed)},indent=2)+'\n')
print(json.dumps([{'path':r['install_path'],'available':bool(r['available_outputs']),'source':r.get('captured_source'),'image_selected':r['system_image_dependency']} for r in rows],indent=2))
