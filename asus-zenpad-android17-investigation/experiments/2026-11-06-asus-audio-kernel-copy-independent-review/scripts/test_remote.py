import os,pathlib,subprocess,resource,json,time
p=pathlib.Path('/srv/android/asus-audio-kernel-copy-review-20261106-r1');os.chdir(p)
os.sched_setaffinity(0,{min(os.sched_getaffinity(0))})
cmd=['gcc','-std=gnu11','-g','-O1','-Wall','-Wextra','-Wno-unused-function','-Wno-unused-variable','-Wno-unused-parameter','-Wno-sign-compare','-Wno-pointer-sign','-fsanitize=address,undefined','-fno-omit-frame-pointer','-pthread','tests/generated.c','-o','out/callback-tests']
def limit():resource.setrlimit(resource.RLIMIT_AS,(1024**3,1024**3))
records=[]
r=subprocess.run(cmd,stdout=subprocess.PIPE,stderr=subprocess.STDOUT,preexec_fn=limit)
(p/'evidence/host-compile.log').write_bytes(r.stdout);records.append({'command':cmd,'exit':r.returncode,'compiler_address_space_limit_bytes':1024**3})
if not r.returncode:
 env=dict(os.environ,ASAN_OPTIONS='detect_leaks=1:halt_on_error=1',UBSAN_OPTIONS='halt_on_error=1:print_stacktrace=1')
 cmd=['/usr/bin/time','-v','out/callback-tests'];r=subprocess.run(cmd,env=env,stdout=subprocess.PIPE,stderr=subprocess.STDOUT)
 (p/'evidence/host-tests.log').write_bytes(r.stdout);records.append({'command':cmd,'exit':r.returncode,'ASAN_OPTIONS':env['ASAN_OPTIONS'],'UBSAN_OPTIONS':env['UBSAN_OPTIONS']})
group=pathlib.Path('/sys/fs/cgroup'+pathlib.Path('/proc/self/cgroup').read_text().strip().split('::')[1])
records.append({'affinity':list(os.sched_getaffinity(0)),'cgroup':str(group),'memory.max':(group/'memory.max').read_text(),'memory.peak':(group/'memory.peak').read_text(),'cpu.max':(group/'cpu.max').read_text()})
(p/'evidence/host-tests.json').write_text(json.dumps(records,indent=2));print(json.dumps(records,indent=2));raise SystemExit(r.returncode)
