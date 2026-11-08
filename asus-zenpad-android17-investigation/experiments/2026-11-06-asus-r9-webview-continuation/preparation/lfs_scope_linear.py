import remote,json
from pathlib import Path
s=r'''
from pathlib import Path
import json,hashlib,datetime
A=Path('/srv/android/lineage24');P=A/'out/target/product/p00a';R=Path('/srv/android/asus-reviewed-build-kit/r9');F=Path('/srv/android/asus-reviewed-build-kit/r9-fixtures')
# Self-identify only this newly authorized worker reader, for parent coordination.
import os
(F/'linear-audit.pid').write_text(str(os.getpid())+'\n')
def sha(p):
 h=hashlib.sha256()
 with p.open('rb') as f:
  for b in iter(lambda:f.read(1048576),b''):h.update(b)
 return h.hexdigest()
install=set((P/'.installable_files').read_text().split());selected={str(P.relative_to(A))+'/'+x for x in install if x.endswith('.apk')}
pending=['out/combined-lineage_p00a.ninja'];seen=set();graphs={};edges={}
while pending:
 rel=pending.pop()
 if rel in seen:continue
 assert rel.startswith('out/') and '..' not in Path(rel).parts and '$' not in rel
 seen.add(rel);h=hashlib.sha256();parts=None
 def record(data):
  head,sep,tail=data[6:].partition(b': ')
  if not sep:return
  outputs=[x.decode() for x in head.split() if x!=b'|']
  if not any(x.endswith('.apk') for x in outputs):return
  deps=[x.decode() for x in tail.split()[1:] if x.endswith(b'.apk') and b'$' not in x]
  for t in outputs:
   if t.endswith('.apk'):edges[t]=deps
 with (A/rel).open('rb') as f:
  for raw in f:
   h.update(raw)
   if raw.startswith((b'subninja ',b'include ')):
    pending.append(raw.split(None,1)[1].strip().decode())
   if parts is not None:
    parts.append(raw[:-2] if raw.endswith(b'$\n') else raw)
    assert sum(map(len,parts))<16*1024*1024,'APK edge exceeded bounded scope'
    if not raw.endswith(b'$\n'):record(b''.join(parts));parts=None
    continue
   if not raw.startswith(b'build '):continue
   head,sep,tail=raw[6:].partition(b': ')
   if not sep or not any(x.endswith(b'.apk') for x in head.split()):continue
   if raw.endswith(b'$\n'):parts=[raw[:-2]]
   else:record(raw)
 assert parts is None
 graphs[rel]=h.hexdigest()
 (F/'linear-audit-progress.json').write_text(json.dumps(dict(graphs_completed=len(graphs),last_graph=rel,apk_edges=len(edges))))
queue=list(selected);closure=set()
while queue:
 t=queue.pop()
 if t in closure:continue
 closure.add(t);queue.extend(edges.get(t,[]))
assert len(closure)<10000,'APK ancestry exceeded bounded scope'
checks=[]
for rel in sorted(t for t in closure if not t.startswith('out/')):
 p=A/rel
 if not p.is_file():checks.append(dict(path=rel,missing=True));continue
 with p.open('rb') as f:b=f.read(256)
 attrs=[]
 for parent in [p.parent,*p.parents]:
  if parent==A.parent:break
  attr=parent/'.gitattributes'
  if attr.is_file():attrs.append(dict(path=str(attr.relative_to(A)),sha256=sha(attr),text=attr.read_text()[:4096]))
 checks.append(dict(path=rel,bytes=p.stat().st_size,lfs_pointer=b.decode() if b.startswith(b'version https://git-lfs.github.com/spec/v1\n') else None,gitattributes=attrs))
r=dict(utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),scope='Single-pass graph index of APK-only ancestry for actual product .installable_files; explicit four WebView ABI pointers audited separately. Not all source binaries.',installable_sha256=sha(P/'.installable_files'),selected_installed_apks=sorted(selected),graph_sha256=graphs,total_apk_edges_indexed=len(edges),selected_edges={t:edges[t] for t in closure if t in edges},selected_source_apks=checks,additional_needed_materializations=[x for x in checks if x.get('lfs_pointer') and x['path']!='external/chromium-webview/prebuilt/arm64/webview.apk'])
with (R/'evidence/selected-lfs-linear-audit.json').open('x') as f:json.dump(r,f,indent=2);f.write('\n')
print(json.dumps(r,indent=2))
'''
r=remote.run(s);Path('2026-11-06-asus-r9-webview-continuation/evidence/selected-lfs-linear-audit.json').write_text(r);d=json.loads(r);print(json.dumps({k:v for k,v in d.items() if k not in ['selected_edges','selected_installed_apks']},indent=2))
