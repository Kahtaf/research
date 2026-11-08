"""Verify original preservation; pin local evidence without touching inputs."""
from bounded import R,run
from pathlib import Path
import json,hashlib,os,sys,platform
ROOT=R.parent;C=ROOT/'2026-11-06-asus-final5role-data-policy-correction'
def pin(p):
 h=hashlib.sha256();size=0
 with p.open('rb') as f:
  for b in iter(lambda:f.read(1048576),b''):h.update(b);size+=len(b)
 return dict(bytes=size,sha256=h.hexdigest())
originals=json.loads((R/'evidence/originals-before.json').read_text());after={n:pin(ROOT/n) for n in originals};assert after==originals
correction=json.loads((R/'evidence/correction-before.json').read_text());cafter={str(p.relative_to(C)):pin(p) for p in C.rglob('*') if p.is_file()};assert cafter==correction
(R/'evidence/originals-after.json').write_text(json.dumps(after,indent=2)+'\n')
(R/'evidence/preservation.json').write_text(json.dumps(dict(passed=True,originals=154,all_originals_equal_pinned_before_and_after=True,correction_files=len(cafter),entire_correction_file_set_and_contents_unchanged=True),indent=2)+'\n')
commands={}
for args in [['/usr/bin/clang','--version'],['/usr/bin/sw_vers'],['/usr/bin/uname','-a'],['/usr/bin/xcrun','--show-sdk-version'],['/usr/bin/xcrun','--show-sdk-path']]:
 q=run(args,timeout=10);commands[' '.join(args)]=q.stdout
logs=[json.loads(line) for line in (R/'evidence/commands.jsonl').read_text().splitlines()]
resources=dict(platform=platform.platform(),serial_host_commands=True,make_jobs=1,affinity_supported=hasattr(os,'sched_setaffinity'),hard_affinity_claimed=False,hard_memory_quota_claimed=False,cpu_limit_seconds_per_leaf_process=60,query_suite_cpu_and_wall_seconds_per_query=10,peak_observed_child_rss_bytes=max(x['observed_children_maxrss_bytes'] for x in logs),memory_limit_probe_receipt='resource-limit-probes.json',initial_reviewer_lock_timeout_retained=True,commands_logged=len(logs))
assert resources['peak_observed_child_rss_bytes']<1024**3
(R/'evidence/resources.json').write_text(json.dumps(resources,indent=2)+'\n')
paths=[Path(sys.executable),Path('/usr/bin/clang'),Path('/usr/bin/ar'),Path('/usr/bin/make')]
paths += [p for p in (R/'tools/host').iterdir() if p.is_file() and not p.suffix=='.o']
(R/'evidence/toolchain.json').write_text(json.dumps(dict(python=sys.version,commands=commands,tools={str(p):pin(p) for p in paths},host_runtime_sdk_not_comprehensively_pinned=True),indent=2)+'\n')
inputs={str(p.relative_to(R)):pin(p) for d in ['inputs','baseline','patches'] for p in (R/d).rglob('*') if p.is_file()}
(R/'INPUT_PINS.json').write_text(json.dumps(inputs,indent=2)+'\n')
outputs={str(p.relative_to(R)):pin(p) for d in ['scripts','source','tests','evidence','artifacts'] for p in (R/d).rglob('*') if p.is_file()}
outputs.update({n:pin(R/n) for n in ['REPORT.md','README.md','INPUT_PINS.json','policy-review.html'] if (R/n).exists()})
(R/'OUTPUT_PINS.json').write_text(json.dumps(outputs,indent=2)+'\n')
print(json.dumps(dict(preserved_originals=len(after),preserved_correction_files=len(cafter),resources=resources)))
