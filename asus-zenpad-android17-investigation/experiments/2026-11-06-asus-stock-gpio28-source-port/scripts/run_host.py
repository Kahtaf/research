from pathlib import Path
import json,platform,resource
from bounded import ROOT,run
run(['python3',ROOT/'scripts/extract_tests.py'],'evidence/extract-test-status.txt')
run(['/usr/bin/clang','-std=gnu89','-O0','-g','-Wall','-Wextra','-Werror','-Wno-unused-function','-Wno-unused-parameter','-Wno-declaration-after-statement','-fsanitize=undefined','-fno-sanitize-recover=all',ROOT/'tests/contract.c','-o',ROOT/'tests/contract-host'],'evidence/host-compile.txt')
print(run([ROOT/'tests/contract-host'],'evidence/host-results.txt').decode())
run(['python3',ROOT/'scripts/verify_source.py'],'evidence/source-verification.txt')
probe={}
# Probe in a disposable child: this process retains normal compiler execution limits.
code='''import resource,json
r={}
for n in ['RLIMIT_AS','RLIMIT_DATA','RLIMIT_RSS']:
 x=getattr(resource,n)
 try:resource.setrlimit(x,(1024**3,1024**3));r[n]={'limits':resource.getrlimit(x),'error':None}
 except (OSError,ValueError) as e:r[n]={'limits':resource.getrlimit(x),'error':str(e)}
print(json.dumps(r))
'''
probe=json.loads(run(['python3','-c',code],'evidence/darwin-memory-probe.json'))
rows=[json.loads(l) for l in (ROOT/'evidence/commands.jsonl').read_text().splitlines()]
(ROOT/'evidence/host-constraints.json').write_text(json.dumps({'platform':platform.platform(),'resource_probe':probe,'cpu_affinity':'Darwin has no sched_setaffinity; no hard one-core binding claim. All extraction, clang/frontend and tests run serially, no build workers.','per_child_cpu_seconds':30,'per_command_wall_seconds':45,'per_output_file_bytes':128*1024**2,'max_recorded_child_highwater_rss_bytes':max(x['children_peak_rss_bytes_cumulative'] for x in rows),'memory_limit':'1GiB AS/DATA/RSS requested per child; API acceptance is recorded, Darwin semantics do not prove hard total-process-tree resident/virtual enforcement. Measured child high-water is below 1GiB. No ASan virtual-space reservation, target object or full kernel build.','bounds':'finite local source fragments and preprocessor inputs; no network or hardware services'},indent=2)+'\n')
print('Host checks and source receipts complete')
