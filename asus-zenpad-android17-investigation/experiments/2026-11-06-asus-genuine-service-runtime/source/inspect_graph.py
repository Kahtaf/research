from pathlib import Path
import json,subprocess,datetime
T=Path('/srv/android/lineage24');R=Path('/srv/android/asus-genuine-service-runtime')
needles=['system/apex/com.android.runtime','com.android.runtime.apex:','com.android.runtime.capex:','/system/bin/boringssl_self_test','system-build.prop/android_common/build.prop:','system_ext-build.prop/android_common/build.prop:','product-build.prop/android_common/build.prop:','apexkeys_intermediates/apexkeys.txt:']
rows=[]
for f in list((T/'out/soong').glob('build.lineage_p00a.*.ninja'))+list((T/'out').glob('build-lineage_p00a*.ninja')):
 module='';acc=''
 for l in f.open():
  if l.startswith('# Module:'):module=l.strip()
  if acc:acc+=l
  elif l.startswith('build '):acc=l
  else:continue
  if l.rstrip().endswith('$'):continue
  edge=acc.replace('$\n','');acc=''
  outputs=edge.split(': ',1)[0]
  if any(n in outputs for n in needles):
   toks=edge.split();inputs=[x for x in toks[3:] if x not in ['|','||']]
   rows.append(dict(ninja=str(f),module=module,edge=edge,missing=[x for x in inputs if not (T/x.replace('$: ',': ')).exists()]))
(R/'evidence/official-target-edges.json').write_text(json.dumps(dict(utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),edges=rows),indent=2))
print(json.dumps(rows,indent=2)[:24000])
