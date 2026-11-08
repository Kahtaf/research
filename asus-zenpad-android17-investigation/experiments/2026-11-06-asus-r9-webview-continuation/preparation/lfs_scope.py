import remote,json
from pathlib import Path
s=r'''
from pathlib import Path
import json,sys,hashlib
A=Path('/srv/android/lineage24');P=A/'out/target/product/p00a';R=Path('/srv/android/asus-reviewed-build-kit/r9');sys.path.insert(0,'/srv/android/asus-reviewed-build-kit/r8/scripts')
from verify_product_r3 import graph_files
from integrate import sha
install=set((P/'.installable_files').read_text().split());selected_apks={str(P.relative_to(A))+'/'+x for x in install if x.endswith('.apk')}
# Follow only selected APK graph ancestry. Store dependency tokens, never full source contents.
frags=list(graph_files(A));wanted=set(selected_apks);edges={};seen=set();passes=0
while wanted-seen:
 passes+=1
 assert passes<=20,'Bounded APK ancestry requires more than 20 layers'
 batch=wanted-seen;seen|=batch
 for rel in frags:
  pending=''
  with (A/rel).open() as f:
   for raw in f:
    line=pending+raw
    if line.endswith('$\n'):pending=line[:-2];continue
    pending=''
    if not line.startswith('build '):continue
    head,sep,tail=line[6:].partition(': ')
    if not sep:continue
    outputs=set(head.split())-{'|'}
    hits=outputs&batch
    if not hits:continue
    deps=tail.split()[1:];deps=[x for x in deps if x not in ['|','||'] and '$' not in x]
    # Restrict ancestry to APK-producing paths; config/tool edges are out of scope.
    deps=[x for x in deps if x.endswith('.apk')]
    for t in hits:edges[t]=deps
    wanted.update(deps)
leaves=sorted(x for x in wanted if not x.startswith('out/'))
checks=[]
for rel in leaves:
 p=A/rel
 if not p.is_file():checks.append(dict(path=rel,missing=True));continue
 with p.open('rb') as f:b=f.read(256)
 attrs=[]
 for parent in [p.parent,*p.parents]:
  if parent==A.parent:break
  attr=parent/'.gitattributes'
  if attr.is_file():attrs.append(dict(path=str(attr.relative_to(A)),sha256=sha(attr),text=attr.read_text()[:4096]))
 checks.append(dict(path=rel,bytes=p.stat().st_size,lfs_pointer=b.decode() if b.startswith(b'version https://git-lfs.github.com/spec/v1\n') else None,gitattributes=attrs))
r=dict(scope='APK-only dependency ancestry of actual current product .installable_files; explicit four WebView ABI pointers audited separately. Not all source binaries or unbuilt modules.',installable_sha256=sha(P/'.installable_files'),selected_installed_apks=sorted(selected_apks),graph_fragments=frags,passes=passes,edges=edges,selected_source_apks=checks,additional_needed_materializations=[x for x in checks if x.get('lfs_pointer') and x['path']!='external/chromium-webview/prebuilt/arm64/webview.apk'])
with (R/'evidence/selected-lfs-audit.json').open('x') as f:json.dump(r,f,indent=2);f.write('\n')
print(json.dumps(r,indent=2))
'''
r=remote.run(s);Path('2026-11-06-asus-r9-webview-continuation/evidence/selected-lfs-audit.json').write_text(r);d=json.loads(r);print(json.dumps({k:v for k,v in d.items() if k not in ['edges','selected_installed_apks']},indent=2))
