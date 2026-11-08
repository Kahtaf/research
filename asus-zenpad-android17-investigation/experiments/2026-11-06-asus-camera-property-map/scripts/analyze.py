from pathlib import Path
import json,re,hashlib
r=Path(__file__).resolve().parents[1]
d=json.loads((r/'evidence/providers-capture.json').read_text())
def sym(s):
 out=[]
 for line in s.splitlines():
  m=re.match(r'\s*\d+:\s+(\w+)\s+(\d+)\s+(\w+)\s+(\w+)\s+(\w+)\s+(\w+)\s+(\S+)',line)
  if m:out.append(dict(zip(['address','size','type','binding','visibility','index','name'],m.groups())))
 return out
def needed(s):return re.findall(r'Shared library: \[(.*?)\]',s)
closure={};abi={}
for arch,libs in d['providers'].items():
 e=(r/'artifacts'/arch/'elf.txt').read_text();symbols=sym(e)
 exports=[s for s in symbols if s['index']!='UND' and s['binding'] in ['GLOBAL','WEAK']]
 assert len(exports)==9 and all('11AsusPropMap' in s['name'] for s in exports)
 required=[s for s in symbols if s['index']=='UND' and s['binding']=='GLOBAL']
 direct=needed(e); providers={}
 for s in required:
  n=s['name'].split('@')[0];matches=[]
  for lib in direct:
   for x in sym(libs[lib]['elf']):
    if x['index']!='UND' and x['name'].split('@')[0]==n:matches.append({'provider':lib,'export':x['name'],'sha256':libs[lib]['sha256']})
  assert matches,(arch,n)
  providers[s['name']]=matches
 graph={};missing=[];queue=direct[:]
 while queue:
  lib=queue.pop(0)
  if lib in graph:continue
  if lib not in libs:graph[lib]={'captured':False};missing.append(lib);continue
  graph[lib]={'captured':True,'sha256':libs[lib]['sha256'],'bytes':libs[lib]['bytes'],'needed':needed(libs[lib]['elf'])};queue+=graph[lib]['needed']
 closure[arch]={'direct_needed':direct,'adapter_strong_import_resolution':providers,'transitive_needed_graph':graph,'missing_frozen_frontier':sorted(set(missing)),'loadable':False,'reason':'missing provider/loader artifacts; Android target runtime and linker namespace not exercised'}
 abi[arch]={'exports':exports,'strong_imports':required,'modern_libutils_sha256':libs['libutils.so']['sha256']}
(r/'evidence/provider-closure.json').write_text(json.dumps(closure,indent=2)+'\n');(r/'evidence/adapter-symbols.json').write_text(json.dumps(abi,indent=2)+'\n')
# Check all nine imports against both original real-ELF inventories.
methods={}
for arch,file in [('arm','2026-11-06-asus-camera-arm32-route/evidence/extended-closure.json'),('arm64','2026-11-06-asus-camera-source-abi-route/evidence/dependency-audit.json')]:
 x=json.loads((r.parent/file).read_text())['vendor_libraries']['libcam_utils.so'];names=[n for n in x['undefined'] if 'PropertyMap' in n];assert len(names)==9
 assert {s['name'].replace('11AsusPropMap','11PropertyMap') for s in abi[arch]['exports']}==set(names)
 methods[arch]={'oem_path':x['path'],'oem_sha256':x['sha256'],'bytes':x['bytes'],'required':names}
(r/'evidence/oem-methods.json').write_text(json.dumps(methods,indent=2)+'\n')
# The production method bodies must be the donor, with exactly the documented edits.
s=(r/'donor/libutils/PropertyMap.cpp').read_text();expected=s[s.index('PropertyMap::PropertyMap()'):s.index('void PropertyMap::addAll')].replace('PropertyMap','AsusPropMap').replace('.string()', '.c_str()')
p=(r/'src/legacy_property_map.cpp').read_text();assert expected in p
print('PASS exact donor method extraction; nine real OEM imports/exports match in both widths; all direct strong imports have genuine frozen providers')
for arch,c in closure.items():print(arch,'runtime frontier missing:',c['missing_frozen_frontier'])
