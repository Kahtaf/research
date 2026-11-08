from pathlib import Path
import json,hashlib,datetime,subprocess
R=Path('/srv/android/asus-firstboot-parity-continuation');P=Path('/srv/android/asus-firstboot-runtime');T=Path('/srv/android/lineage24'); O=R/'evidence/services-current.json'
records=json.loads((P/'evidence/service-dependencies-final.json').read_text())['records']
for row in records:
 for e in row['edges']:
  tokens=e['edge'].split();e['output']=tokens[1].rstrip(':');e['output_exists']=(T/e['output']).is_file();e['missing_previous']=e['missing'];e['missing']=[x for x in tokens[3:] if x.startswith(('out/','prebuilts/')) and not (T/x).exists()]
installed=['system/bin/apexd','system/bin/keystore2','system/bin/hwservicemanager','system/bin/servicemanager','vendor/bin/hw/android.hardware.keymaster@4.0-service','system/bin/linkerconfig','system/apex/com.android.adbd.apex','system/build.prop','system_ext/build.prop','product/build.prop','vendor/build.prop']
files=[]
for n in installed:
 p=T/'out/target/product/p00a'/n;row={'path':str(p),'exists':p.is_file()}
 if p.is_file():row.update(bytes=p.stat().st_size,sha256=hashlib.sha256(p.read_bytes()).hexdigest())
 files.append(row)
O.write_text(json.dumps({'utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'records':records,'installed':files},indent=2))
for r in records:print(r['module'],r['variant'],[(e['output_exists'],len(e['missing'])) for e in r['edges']])
print(json.dumps(files,indent=2))
