from pathlib import Path
import json,os,subprocess as s
R=Path('/srv/android/asus-r9-linkerconfig-ownership-fix-20261106');os.environ['TMPDIR']=str(R/'tmp');d={}
for root in ['/srv/android/asus-firstboot-runtime/evidence','/srv/android/asus-firstboot-runtime/source','/srv/android/asus-genuine-service-runtime/evidence','/srv/android/asus-full-system-observer-preparation-20261106/immutable','/srv/android/asus-full-system-observer-preparation-20261106/immutable/lib64']:
 p=Path(root);d[root]=[x.name for x in p.iterdir()] if p.is_dir() else None
for n in ['libgtest-dev','libfmt-dev','libprotobuf-dev','libtinyxml2-dev']:
 p=s.run(['dpkg-query','-W','-f=${Status}\n',n],capture_output=True,text=True);d[n]=p.stdout.strip()
p=Path('/srv/android/asus-device-product/logs/graphics-build-r6.log');rows=p.read_text(errors='replace').splitlines();matches=[]
for i,line in enumerate(rows):
 if any(x in line for x in ['linkerconfig_contents_fulltest','19 tests','Running main','[ RUN      ]']):matches.append((i,line))
d['old_host_tests']=matches;d['retained_ninja_log_names']=[str(x) for x in Path('/srv/android/asus-reviewed-build-kit/r9-exec-r1').glob('**/*ninja*')][:30]
(R/'evidence/closure-discovery.json').write_text(json.dumps(d,indent=2));print(json.dumps(d,indent=2))
