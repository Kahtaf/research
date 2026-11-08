exec(open('2026-11-06-asus-r8-continuation-kit/preparation/inspect_remote.py').read().split('script=r')[0])
script=r'''
from pathlib import Path
import os,hashlib,json,shlex,subprocess,resource,datetime
A=Path('/srv/android/lineage24');F=Path('/srv/android/asus-reviewed-build-kit/r8-fixtures/wpa-r2');F.mkdir(parents=True)
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def write(p,d):p.write_text(json.dumps(d,indent=2,sort_keys=True)+'\n')
source='device/asus/p00a/connectivity/src/driver_cmd_p00a.c';original=(A/source).read_text();before=sha(A/source)
old='#include "includes.h"\n#include "common.h"\n#include "driver_nl80211.h"\n#include "linux_ioctl.h"\n'
new='/* Upstream disabled-feature inline stubs have unused parameters. Keep the\n * exception at this include boundary; adapter code retains -Wextra -Werror. */\n#pragma clang diagnostic push\n#pragma clang diagnostic ignored "-Wunused-parameter"\n'+old+'#pragma clang diagnostic pop\n'
assert original.count(old)==1
post=original.replace(old,new)
(F/'original.c').write_text(original);(F/'candidate.c').write_text(post)
(F/'strict-negative.c').write_text(post+'\nint r8_strict_warning_probe(int unused_parameter) { return 0; }\n')
failed=A/'out/siso_failed_commands.sh';line=next(l for l in failed.read_text().splitlines() if l.startswith('PWD='));argv=shlex.split(line);assert argv.pop(0)=='PWD=/proc/self/cwd'
assert argv[-1]==source and '-Wextra' in argv and '-Werror' in argv and 'aarch64-linux-android37' in argv
output=argv[argv.index('-o')+1];dep=argv[argv.index('-MF')+1]
write(F/'original-command.json',dict(command=line,argv=argv,source=source,output=output,depfile=dep,failed_commands_sha256=sha(failed)))
(F/'tmp').mkdir();env=os.environ.copy();env.update(PWD='/proc/self/cwd',TMPDIR=str(F/'tmp'))
def limit():
 os.sched_setaffinity(0,{min(os.sched_getaffinity(0))});resource.setrlimit(resource.RLIMIT_AS,(1024**3,1024**3));resource.setrlimit(resource.RLIMIT_CPU,(90,90))
records=[]
for name in ['original','candidate','strict-negative']:
 args=list(argv);args[-1]=str(F/(name+'.c'));args[args.index('-o')+1]=str(F/(name+'.o'));args[args.index('-MF')+1]=str(F/(name+'.d'))
 with (F/(name+'.log')).open('xb') as log:r=subprocess.run(args,cwd=A,env=env,stdout=log,stderr=subprocess.STDOUT,preexec_fn=limit,timeout=120)
 text=(F/(name+'.log')).read_text();records.append(dict(case=name,argv=args,exit=r.returncode,diagnostics_sha256=sha(F/(name+'.log')),errors=text.count('error:'),log=text))
assert records[0]['exit']!=0 and records[0]['errors']==17 and 'wpa_common.h' in records[0]['log']
assert records[1]['exit']==0 and (F/'candidate.o').is_file()
assert records[2]['exit']!=0 and 'unused_parameter' in records[2]['log'] and 'wpa_common.h:' not in records[2]['log']
deptext=(F/'candidate.d').read_text().replace('\\\n',' ');dependencies=shlex.split(deptext.split(':',1)[1]);pins={str(p):sha(Path(p) if Path(p).is_absolute() else A/p) for p in dependencies}
assert before==sha(A/source)
result=dict(utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),source=source,preimage=before,postimage=sha(F/'candidate.c'),object=dict(path=str(F/'candidate.o'),sha256=sha(F/'candidate.o'),bytes=(F/'candidate.o').stat().st_size,magic=(F/'candidate.o').read_bytes()[:4].hex(),lto=True),compiler_sha256=sha(A/argv[0]),records=records,dependency_sha256=pins,active_source_unchanged=True,one_cpu=True,address_space_bytes=1024**3,native_product_execution=False)
write(F/'result.json',result);print(json.dumps(result,indent=2))
'''
r=m.run(script);Path('2026-11-06-asus-r8-continuation-kit/evidence/wpa-reproduction.json').write_text(r);d=json.loads(r)
print(json.dumps({k:v for k,v in d.items() if k not in ['records','dependency_sha256']},indent=2));print([(r['case'],r['exit'],r['errors']) for r in d['records']])
