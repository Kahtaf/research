from pathlib import Path
import re,hashlib,json,datetime,xml.etree.ElementTree as ET
roots={'active_r5':'/srv/android/lineage24/device/asus/p00a','continuation':'/srv/android/asus-build-continuation/product-device','combined_r5':'/srv/android/asus-build-continuation/integration-r5/product-device'}
out={'utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'scope':'Direct device tree evidence; no Soong product evaluation, no final installed-image claim','trees':{}}
for name,root in roots.items():
 p=Path(root);d={'root':root,'exists':p.exists(),'files':{},'hal_names':[],'make_lines':[],'policy_lines':[]}
 if p.exists():
  for f in sorted(p.rglob('*')):
   if not f.is_file() or any(s in f.parts for s in ['prebuilt','.git']) or f.suffix not in ['.mk','.xml','.rc','.bp','.te'] and f.name not in ['file_contexts','genfs_contexts']:continue
   b=f.read_bytes();s=b.decode(errors='replace');rel=str(f.relative_to(p));d['files'][rel]=hashlib.sha256(b).hexdigest()
   if f.suffix=='.mk':d['make_lines'] += [rel+':'+str(i)+':'+l for i,l in enumerate(s.splitlines(),1) if l.strip() and not l.lstrip().startswith('#')]
   if f.suffix=='.xml':
    try:d['hal_names']+= [x.text for x in ET.fromstring(s).findall('.//hal/name')]
    except ET.ParseError:pass
   if f.suffix=='.te' or f.name in ['file_contexts','genfs_contexts']:d['policy_lines'] += [rel+':'+str(i)+':'+l for i,l in enumerate(s.splitlines(),1) if l.strip() and not l.lstrip().startswith('#')]
 d['hal_names']=sorted(set(d['hal_names']));out['trees'][name]=d
print(json.dumps(out,indent=2))
