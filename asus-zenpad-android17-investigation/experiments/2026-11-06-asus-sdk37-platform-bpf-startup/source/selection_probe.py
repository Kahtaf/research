from pathlib import Path
import json
T=Path('/srv/android/lineage24')
for d in ['out/target/product/p00a/obj/PACKAGING','out/target/product/p00a','out/soong']:
 print('LIST',d,[p.name for p in (T/d).iterdir() if any(x in p.name for x in ['system','file','module','install','package'])])
p=T/'out/build-lineage_p00a.ninja';want=[]
for line in p.open():
 if line.startswith('build ') and (line.startswith('build systemimage:') or line.startswith('build out/target/product/p00a/system.img:') or ('file_list' in line.split(':')[0] and 'system' in line.split(':')[0])): print('EDGE',line[:3000]);want.extend(line.split(':',1)[1].split()[1:])
for p in (T/'out/target/product/p00a').glob('**/file_list*'):
 if p.is_file() and p.stat().st_size < 3000000:
  matches=[x for x in p.read_text().splitlines() if '/etc/bpf/' in x]
  if matches:print('FILELIST',p,matches)
print('DEPS EXIST')
R=Path('/srv/android/asus-network-runtime');cmd=json.loads((R/'platform-build-legacy/command.json').read_text())['argv'];total=0
for i,a in enumerate(cmd):
 if a=='-L':
  d=T/cmd[i+1];fs=[p for p in d.iterdir() if p.is_file() and (p.name.endswith(('.so','.rlib','.a','.rmeta')))];size=sum(p.stat().st_size for p in fs);total+=size;print(d,len(fs),size)
print('TOTAL',total)
