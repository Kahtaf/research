from pathlib import Path
import os,resource,subprocess as s,json,hashlib
os.sched_setaffinity(0,{min(os.sched_getaffinity(0))});resource.setrlimit(resource.RLIMIT_AS,(1024**3,1024**3))
O=Path('/srv/android/asus-final-netd-runtime-20261106');os.environ['TMPDIR']=str(O/'tmp');sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
src=(O/'scripts/fixture_init.c').read_text();run=(O/'scripts/run_unit.py').read_text();add='const char*dirs[]={"netd_shared","netd_readonly","net_shared","tethering","loader","clatd","dscpPolicy","offload"};for(unsigned i=0;i<sizeof(dirs)/sizeof(dirs[0]);i++){char path[128];snprintf(path,sizeof(path),"/sys/fs/bpf/%s",dirs[i]);mkdir(path,0755);}'
sources={4:src,3:src.replace(add,'').replace('"/apex/com.android.tethering/etc/bpf/mainline/netd.o",0','"/apex/com.android.tethering/etc/bpf/mainline/netd.o","/apex/com.android.tethering/etc/bpf/mainline/netd@funcs.o",0')}
results=[]
for version,text in sources.items():
 source=O/'scripts'/f'fixture_init_r{version}.c';source.write_text(text);(O/'scripts/fixture_init.c').write_text(text);out=O/f'fixture-init-r{version}-repro';cmd=['aarch64-linux-gnu-gcc','-static','-O2','-Wall','-Wextra',str(O/'scripts/fixture_init.c'),'-o',str(out)];p=s.run(cmd,capture_output=True,text=True,timeout=60);assert p.returncode==0,p.stderr
 R=O/f'run-r{version}-'+Path('actual') if False else O/('run-r3-actual' if version==3 else 'run-r4-metadata-crud')
 expected=json.loads((R/'inputs.json').read_text())['init'];results.append(dict(version=version,argv=cmd,source_sha256=sha(source),binary_sha256=sha(out),expected=expected,match=sha(out)==expected,compiler_sha256=sha(Path('/usr/bin/aarch64-linux-gnu-gcc'))))
 # GCC may encode the source basename; report reproducibility exactly, without altering run inputs.
(O/'scripts/fixture_init.c').write_text(src)
assert all(r['match'] for r in results),results
(O/'evidence/init-source-reproduction.json').write_text(json.dumps(results,indent=2));print(json.dumps(results,indent=2))
(O/'scripts/run_unit_r3.py').write_text(run.replace("['metadata-crud']","['metadata-crud','actual']").replace("run-r4-","run-r3-"))
