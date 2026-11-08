from pathlib import Path
import os,resource,json,hashlib,subprocess as s,stat
os.sched_setaffinity(0,{min(os.sched_getaffinity(0))});resource.setrlimit(resource.RLIMIT_AS,(1024**3,1024**3))
O=Path('/srv/android/asus-final-netd-runtime-20261106');O.mkdir();(O/'evidence').mkdir();(O/'scripts').mkdir();(O/'tmp').mkdir();os.environ['TMPDIR']=str(O/'tmp')
F=Path('/srv/android/asus-final-bpf-runtime-20261106');N=Path('/srv/android/asus-network-runtime');P=Path('/srv/android/asus-sdk37-platform-bpf-startup-20261106');sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
c=json.loads((F/'evidence/capture.json').read_text());raw=Path(c['raw_before']['path']);st=raw.stat();assert (st.st_size,stat.S_IMODE(st.st_mode),st.st_ino,st.st_mtime_ns)==(3753902080,0o444,c['raw_before']['inode'],c['raw_before']['mtime_ns'])
for name in ['capture.json','final-audit.json','final-host-binding.json']:(O/'evidence'/name).write_bytes((F/'evidence'/name).read_bytes())
for row in c['objects']:assert sha(F/'capture/root'/row['install_path'])==row['current_sha256']
for p,row in c['loaders'].items():assert sha(F/'capture/root'/p)==row['sha256']
commands=[]
for path in ['/system/build.prop','/system/etc/prop.default','/system/vendor/build.prop','/system/product/build.prop','/system/system_ext/build.prop']:
 dest=O/'props'/path.lstrip('/');dest.parent.mkdir(parents=True,exist_ok=True);cmd=['/usr/sbin/debugfs','-R','dump '+path+' '+str(dest),str(raw)];r=s.run(cmd,capture_output=True,text=True);commands.append(dict(argv=cmd,exit=r.returncode,stdout=r.stdout,stderr=r.stderr))
 if dest.exists():print('PROPFILE',path,sha(dest));print('\n'.join(x for x in dest.read_text().splitlines() if x.startswith(('ro.build.','ro.board.first','ro.bpf.','ro.product.first','ro.cw','ro.oem'))))
for p in (F/'capture/com.android.tethering-selected-apex').rglob('build.prop'):
 dest=O/'props/apex/com.android.tethering'/p.relative_to(F/'capture/com.android.tethering-selected-apex');dest.parent.mkdir(parents=True,exist_ok=True);dest.write_bytes(p.read_bytes());print('APEX_PROP',p,sha(p),p.read_text())
(O/'evidence/property-capture-commands.json').write_text(json.dumps(commands,indent=2))
for rel in ['bpf/headers/include/bpf/BpfUtils.h','bpf/headers/include/bpf/KernelUtils.h','bpf/loader/NetBpfLoad.cpp']:
 p=N/'inputs/Connectivity'/rel;t=p.read_text();print('SOURCE',p,sha(p));print(t[0:7000] if p.name!='NetBpfLoad.cpp' else '\n'.join(t.splitlines()[1510:1650]));dest=O/'evidence'/p.name;dest.write_text(t)
print('SEEDCOMPILE',s.run(['find',str(N/'evidence'),'-name','seed_properties*'],capture_output=True,text=True).stdout)
print('COMPILERS',s.run(['find',str(N/'inputs'),'-maxdepth','2','-type','d'],capture_output=True,text=True).stdout)
(O/'evidence/frozen-receipts-sha256.json').write_text(json.dumps({str(F/'evidence'/x):sha(F/'evidence'/x) for x in ['capture.json','final-audit.json','final-host-binding.json']},indent=2))
