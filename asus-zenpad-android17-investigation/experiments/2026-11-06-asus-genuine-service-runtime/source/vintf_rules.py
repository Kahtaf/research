from pathlib import Path
import mmap,json
T=Path('/srv/android/lineage24');R=Path('/srv/android/asus-genuine-service-runtime');rows=[]
for f in (T/'out/soong').glob('build.lineage_p00a.*.ninja'):
 with f.open('rb') as fd,mmap.mmap(fd.fileno(),0,access=mmap.ACCESS_READ) as m:
  for mod in ['system_ext_manifest.xml','vendor_manifest.xml']:
   needle=('# Module:  '+mod+'\n').encode();start=m.find(needle)
   if start<0:continue
   end=m.find(b'# Module:',start+len(needle));end=len(m) if end<0 else end
   block=m[start:end].decode();rows.append(dict(module=mod,ninja=str(f),block=block))
(R/'evidence/vintf-module-rules.json').write_text(json.dumps(rows,indent=2))
for row in rows:print(row['block'][:16000])
