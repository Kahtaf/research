import remote,json
from pathlib import Path
s=r'''
from pathlib import Path
import json,hashlib,datetime,os
A=Path('/srv/android/lineage24');P=A/'out/target/product/p00a';R=Path('/srv/android/asus-reviewed-build-kit/r9');F=Path('/srv/android/asus-reviewed-build-kit/r9-fixtures')
(F/'product-v2-audit.pid').write_text(str(os.getpid())+'\n')
def sha(p):
 h=hashlib.sha256()
 with p.open('rb') as f:
  for b in iter(lambda:f.read(1048576),b''):h.update(b)
 return h.hexdigest()
def retained(t):return t.endswith(('.apk','.img')) or t.startswith('out/target/product/p00a/obj/PACKAGING/') or t.startswith('out/target/product/p00a/installed-files') or t in {'systemimage','bootimage'}
prior=json.loads((F/'product-apk-graph-index.json').read_text());graphs={};edges={}
for rel,expected in prior['graph_sha256'].items():
 h=hashlib.sha256();header=None;outputs=None;deps=[];rule_seen=False
 with (A/rel).open('rb') as f:
  for raw in f:
   h.update(raw);continued=raw.endswith(b'$\n');line=raw[:-2] if continued else raw
   if raw.startswith(b'build '):header=[line[6:]];outputs=None;deps=[];rule_seen=False
   elif header is not None:header.append(line)
   elif outputs is None:continue
   if header is not None:
    data=b''.join(header);assert len(data)<1048576,'Build header exceeded bound'
    head,sep,tail=data.partition(b': ')
    if not sep:
     assert continued,'Malformed Ninja build header';continue
    outputs=[t.decode() for t in head.split() if retained(t.decode())]
    header=None
    if not outputs:outputs=None;continue
    fields=tail.split()
   else:fields=line.split()
   for b in fields:
    if not rule_seen:rule_seen=True;continue
    if b in [b'|',b'||']:continue
    t=b.decode()
    if '$' not in t and retained(t):deps.append(t)
   if not continued:
    for t in outputs:edges[t]=deps
    outputs=None
 assert header is None and outputs is None
 assert h.hexdigest()==expected,'Graph changed while preparing audit: '+rel
 graphs[rel]=h.hexdigest()
 (F/'product-v2-audit-progress.json').write_text(json.dumps(dict(graphs_completed=len(graphs),last_graph=rel,retained_edges=len(edges))))
with (F/'product-apk-graph-index-v2.json').open('x') as f:json.dump(dict(graph_sha256=graphs,edges=edges),f)
selected={'systemimage','bootimage','out/target/product/p00a/system.img','out/target/product/p00a/boot.img'};queue=list(selected);closure=set()
while queue:
 t=queue.pop()
 if t in closure:continue
 closure.add(t);queue.extend(edges.get(t,[]))
assert len(closure)<10000,'Product APK scope exceeds bound'
assert 'external/chromium-webview/prebuilt/arm64/webview.apk' in closure,'Actual image graph did not reach selected WebView input'
checks=[]
for rel in sorted(t for t in closure if not t.startswith('out/') and t.endswith('.apk')):
 p=A/rel
 if not p.is_file():checks.append(dict(path=rel,missing=True));continue
 with p.open('rb') as f:b=f.read(256)
 attrs=[]
 for parent in [p.parent,*p.parents]:
  if parent==A.parent:break
  attr=parent/'.gitattributes'
  if attr.is_file():attrs.append(dict(path=str(attr.relative_to(A)),sha256=sha(attr),text=attr.read_text()[:4096]))
 checks.append(dict(path=rel,bytes=p.stat().st_size,lfs_pointer=b.decode() if b.startswith(b'version https://git-lfs.github.com/spec/v1\n') else None,gitattributes=attrs))
r=dict(utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),scope='APK/packaging ancestry of genuine bootimage/systemimage graph roots, not potential .installable_files inventory. Full graph byte hashes match the frozen own index. Four WebView ABI pointers audited separately; not all source binaries.',graph_sha256=graphs,retained_edges_indexed=len(edges),selected_closure_count=len(closure),selected_image_apks=sorted(t for t in closure if t.startswith('out/target/product/p00a/system/') and t.endswith('.apk')),selected_edges={t:edges[t] for t in closure if t in edges},selected_source_apks=checks,additional_needed_materializations=[x for x in checks if x.get('lfs_pointer') and x['path']!='external/chromium-webview/prebuilt/arm64/webview.apk'])
with (R/'evidence/selected-lfs-product-audit.json').open('x') as f:json.dump(r,f,indent=2);f.write('\n')
print(json.dumps(r,indent=2))
'''
r=remote.run(s);Path('2026-11-06-asus-r9-webview-continuation/evidence/selected-lfs-product-audit.json').write_text(r);d=json.loads(r);print(json.dumps({k:v for k,v in d.items() if k not in ['selected_edges','selected_image_apks']},indent=2))
