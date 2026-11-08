#!/usr/bin/env python3
import base64,json,urllib.request,hashlib
from pathlib import Path
root=Path(__file__).resolve().parents[1]; out=root/'sources/reference'; results=[]
def get(url):
 with urllib.request.urlopen(urllib.request.Request(url,headers={'User-Agent':'asus-audit'}),timeout=45) as r:return r.read()
def github(repo,ref,select,label):
 sha=json.loads(get(f'https://api.github.com/repos/{repo}/commits/{ref}'))['sha']
 tree=json.loads(get(f'https://api.github.com/repos/{repo}/git/trees/{sha}?recursive=1'))
 matches=[x['path'] for x in tree['tree'] if x['type']=='blob' and select(x['path'])]
 for p in matches:
  url=f'https://raw.githubusercontent.com/{repo}/{sha}/{p}'; data=get(url); name=label+'-'+p.replace('/','__');(out/name).write_bytes(data)
  results.append(dict(repo=repo,sha=sha,path=p,file=name,url=url,sha256=hashlib.sha256(data).hexdigest()))
 print(label,sha,'truncated',tree.get('truncated'),matches)
 return sha
mainline='20951722df6ae1f6fecbfcea0a7d585118a06f3f'
# Targeted directory listing avoids drawing absence conclusions from a truncated full tree.
data=get(f'https://api.github.com/repos/bengris32/linux-mtk/contents/arch/arm64/boot/dts/mediatek?ref={mainline}')
(out/'mainline-mediatek-directory.json').write_bytes(data)
names=[x['name'] for x in json.loads(data) if '8163' in x['name'] or 'asus' in x['name'].lower()]
print('mainline boards',names)
github('LineageOS/android_packages_modules_Connectivity','lineage-24.0',lambda p:p.endswith(('.cpp','.h')) and ('Loader' in p or 'loader' in p),'connectivity24')
github('anton-scholten/android_kernel_samsung_sdm670','lineage-24.0',lambda p:p in ['Makefile','fs/erofs/super.c','include/uapi/linux/bpf.h'],'s5e-kernel24')
(out/'additional-provenance.json').write_text(json.dumps(results,indent=2))
