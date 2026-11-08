#!/usr/bin/env python3
import hashlib, json, urllib.request
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'sources/ports'; OUT.mkdir(exist_ok=True)
records=[]
def get(url):
    with urllib.request.urlopen(urllib.request.Request(url,headers={'User-Agent':'asus-feasibility-audit'}),timeout=45) as r: return r.read()
for label,repo in [('tab-s5e','anton-scholten/lineageos-galaxy-tab-s5e'),('dandelion','qcom-toolbox/EVOLUTION-X-DANDELION-17')]:
    commit=json.loads(get('https://api.github.com/repos/'+repo+'/commits/HEAD'))['sha']
    tree=json.loads(get('https://api.github.com/repos/'+repo+'/git/trees/'+commit+'?recursive=1'))
    (OUT/(label+'-tree.json')).write_text(json.dumps(tree,indent=2))
    paths=[x['path'] for x in tree['tree'] if x['type']=='blob' and (x['path']=='README.md' or x['path'].startswith(('local_manifests/','manifests/','patches/')) or x['path'] in ['build.sh','UPSTREAM.md'])]
    for p in paths:
        if p.endswith(('.png','.jpg','.zip')): continue
        url='https://raw.githubusercontent.com/'+repo+'/'+commit+'/'+p
        data=get(url); dest=OUT/label/p; dest.parent.mkdir(exist_ok=True,parents=True);dest.write_bytes(data)
        records.append(dict(repo=repo,sha=commit,path=p,url=url,sha256=hashlib.sha256(data).hexdigest(),bytes=len(data)))
    print(label,commit,len(paths))
(OUT/'provenance.json').write_text(json.dumps(records,indent=2))
