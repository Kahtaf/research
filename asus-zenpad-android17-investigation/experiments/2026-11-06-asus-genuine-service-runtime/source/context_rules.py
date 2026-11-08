from pathlib import Path
import json
T=Path('/srv/android/lineage24');R=Path('/srv/android/asus-genuine-service-runtime');rows=[]
wanted={p+'_'+t+'_contexts' for p in ['plat','system_ext','product','vendor'] for t in ['service','hwservice']}|{'vndservice_contexts'}
for idx in [8,9]:
 f=T/f'out/soong/build.lineage_p00a.{idx}.ninja';module='';block=[]
 for l in f.open():
  if l.startswith('# Module:'):module=l.split(':',1)[1].strip()
  if module in wanted:
   if l.startswith('build ') or l.startswith('    command =') or l.startswith('    input') or l.startswith('    output'):rows.append(dict(module=module,ninja=str(f),line=l.rstrip()))
(R/'evidence/context-rules.json').write_text(json.dumps(rows,indent=2))
for x in rows:
 if 'command =' in x['line']:print(x['module'],x['line'][:15000])
