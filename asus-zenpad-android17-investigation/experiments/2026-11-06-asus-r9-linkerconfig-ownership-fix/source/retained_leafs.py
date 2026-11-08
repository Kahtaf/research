from pathlib import Path
import json,os,tarfile
R=Path('/srv/android/asus-r9-linkerconfig-ownership-fix-20261106');os.environ['TMPDIR']=str(R/'tmp');d={}
for p in [Path('/srv/android/asus-firstboot-runtime/evidence/service-ninja-r1'),Path('/srv/android/asus-firstboot-runtime/inputs/service-rules-r2'),Path('/srv/android/asus-official-runtime-capture'),Path('/srv/android/asus-device-product/legacy-core-checkpoint')]:
 d[str(p)]=[x.name for x in p.iterdir()] if p.is_dir() else None
for p in Path('/srv/android/asus-firstboot-runtime/evidence/service-ninja-r1').glob('*'):
 if p.is_file() and 'linker' in p.name:d[str(p)]=p.read_text()[:12000]
for n in ['graphics-result-r7.tar.gz','legacy-core-checkpoint.tar.gz','checkpoint.tar.gz']:
 p=Path('/srv/android/asus-device-product')/n
 with tarfile.open(p) as tf:d[n]=[m.name for m in tf.getmembers() if any(x in m.name for x in ['linkerconfig','ninja','commands','libprotobuf','linker_config.pb'])][:100]
(R/'evidence/retained-leaf-search.json').write_text(json.dumps(d,indent=2));print(json.dumps(d,indent=2))
