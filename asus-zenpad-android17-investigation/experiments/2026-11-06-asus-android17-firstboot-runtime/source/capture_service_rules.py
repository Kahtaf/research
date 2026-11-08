from pathlib import Path
import re,json,hashlib
T=Path('/srv/android/lineage24');R=Path('/srv/android/asus-firstboot-runtime');D=R/'inputs/service-rules-r2';D.mkdir();wanted={'apexd','keystore2','android.hardware.keymaster@4.0-service','hwservicemanager','servicemanager'}
modules=[]
for f in (T/'out/soong').glob('build.lineage_p00a.*.ninja'):
 lines=[];name=''
 def save():
  if name not in wanted or not lines:return
  txt=''.join(lines);var=next((l.split(':',1)[1].strip() for l in lines if l.startswith('# Variant:')),'')
  if 'arm64' not in var:return
  defined=next((l.split(':',1)[1].strip() for l in lines if l.startswith('# Defined:')),'')
  if defined.startswith('toolchain/'):return
  out=D/(name+'-'+var+'.ninja');assert not out.exists(),(str(out),defined);out.write_text(txt);modules.append(dict(module=name,variant=var,defined=defined,ninja=str(f),path=str(out),sha256=hashlib.sha256(txt.encode()).hexdigest()))
 for line in f.open():
  if line.startswith('# Module:'):save();name=line.split(':',1)[1].strip();lines=[line] if name in wanted else []
  elif name in wanted:lines.append(line)
 save()
records=[]
for m in modules:
 logical=Path(m['path']).read_text().replace('$\n','');edges=[]
 for line in logical.splitlines():
  if line.startswith('build ') and any(x in line for x in ['g.cc.ld ', 'g.rust.rustc ', 'g.rust.rustLink ']):
   toks=line.split();deps=[x for x in toks[3:] if x.startswith(('out/','prebuilts/'))];edges.append(dict(edge=line,dependencies=len(deps),missing=[x for x in deps if not (T/x).exists()]))
 records.append(dict(**m,edges=edges))
(D/'inventory.json').write_text(json.dumps(records,indent=2));print(json.dumps([dict(module=m['module'],variant=m['variant'],edges=len(m['edges']),missing_counts=[len(e['missing']) for e in m['edges']]) for m in records],indent=2))
