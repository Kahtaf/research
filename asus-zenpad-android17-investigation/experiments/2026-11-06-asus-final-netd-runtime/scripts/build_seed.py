from pathlib import Path
import os,resource,json,hashlib,subprocess as s,shlex
os.sched_setaffinity(0,{min(os.sched_getaffinity(0))});resource.setrlimit(resource.RLIMIT_AS,(1024**3,1024**3))
O=Path('/srv/android/asus-final-netd-runtime-20261106');N=Path('/srv/android/asus-network-runtime');os.environ['TMPDIR']=str(O/'tmp');sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
props={};sources={}
for p in (O/'props').rglob('*.prop'):
 for line in p.read_text().splitlines():
  if '=' in line and not line.startswith('#'):
   k,v=line.split('=',1);props[k]=v;sources[k]=dict(path=str(p),sha256=sha(p))
keys=['ro.build.version.sdk','ro.build.version.sdk_full','ro.build.version.codename','ro.build.type','ro.bpf.allow_legacy_kernel']
selected={k:dict(value=props[k],**sources[k]) for k in keys}
selected['ro.board.first_api_level']=dict(value=None,source='ABSENT in captured SYSTEM/vendor build.prop; preserve genuine loader default, do not seed 23')
(O/'evidence/property-seeds.json').write_text(json.dumps(selected,indent=2));print('SEEDS',json.dumps(selected))
text='#include <sys/system_properties.h>\n#include <stdio.h>\n#include <string.h>\nextern "C" int __system_property_area_init();\nextern "C" int __system_property_add(const char*,unsigned,const char*,unsigned);\nint main(){int rc=__system_property_area_init();printf("PROPERTY_AREA_INIT %d\\n",rc);if(__system_property_area_serial()==(unsigned)-1)return 1;const char* p[][2]={'+','.join('{'+json.dumps(k)+','+json.dumps(props[k])+'}' for k in keys)+'};for(auto&v:p){rc=__system_property_add(v[0],strlen(v[0]),v[1],strlen(v[1]));printf("PROPERTY_ADD %s=%s rc=%d\\n",v[0],v[1],rc);if(rc)return 1;char b[PROP_VALUE_MAX];int n=__system_property_get(v[0],b);if(n!=(int)strlen(v[1])||strcmp(b,v[1]))return 2;}return 0;}\n'
(O/'scripts/seed_properties.cpp').write_text(text)
cmd=json.loads((N/'evidence/seed_properties-compile-r11.log').read_text().splitlines()[0]);cmd=[str(O/'scripts/seed_properties.cpp') if x==str(N/'source/seed_properties.cpp') else str(O/'seed_properties') if x==str(N/'artifacts/seed_properties') else x for x in cmd];cmd+=['-MD','-MF',str(O/'seed_properties.d')]
r=s.run(cmd,capture_output=True,text=True,cwd=O,timeout=60);(O/'evidence/seed-compile.json').write_text(json.dumps(dict(argv=cmd,exit=r.returncode,stdout=r.stdout,stderr=r.stderr),indent=2));print('COMPILE',r.returncode,r.stderr);assert r.returncode==0
paths=shlex.split((O/'seed_properties.d').read_text().replace('\\\n',' ').split(':',1)[1]);pins={p:sha(Path(p)) for p in paths};pins[cmd[0]]=sha(Path(cmd[0]));pins[str(O/'seed_properties')]=sha(O/'seed_properties');(O/'evidence/seed-compile-inputs.json').write_text(json.dumps(pins,indent=2))
# Capture the actual source-apex symlink receipt and platform init metadata.
raw='/srv/android/asus-root-enabled-incremental-r1/host-r2/validation/system-partition.raw';r=s.run(['/usr/sbin/debugfs','-R','stat /system/etc/source_apex_version',raw],capture_output=True,text=True);(O/'evidence/source-apex-stat.txt').write_text(r.stdout+r.stderr);assert 'Fast link dest: "373399999"' in r.stdout
