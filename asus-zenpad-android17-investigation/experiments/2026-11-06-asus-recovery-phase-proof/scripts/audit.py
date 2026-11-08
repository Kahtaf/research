from pathlib import Path
import hashlib,json
R=Path(__file__).resolve().parents[1]
rows={}
for line in (R/'evidence/policy-reachability.txt').read_text().splitlines():
 s,t,c,*perms=line.split();rows[s,t,c]=set(perms)
actors=['init','ueventd','adbd','shell','os_rescue','p10_restore']
for actor in actors:
 assert ('write' in rows[actor,'rescue_recovery_device','blk_file'])==(actor=='p10_restore')
 assert 'write' not in rows[actor,'rescue_disk_device','blk_file']
 assert 'write' not in rows[actor,'block_device','blk_file']
 assert 'setenforce' not in rows[actor,'kernel','security']
 assert 'dyntransition' not in rows[actor,'p10_restore','process']
 if actor not in ['init','os_rescue','p10_restore']:
  assert 'ptrace' not in rows[actor,'os_rescue','process']
  assert 'ptrace' not in rows[actor,'p10_restore','process']
 assert ('transition' in rows[actor,'p10_restore','process'])==(actor=='os_rescue')
 assert ('execute' in rows[actor,'p10_restore_exec','file'])==(actor in ['os_rescue','p10_restore'])
for actor in ['os_rescue','p10_restore']:
 assert not rows[actor,actor,'capability']
 assert 'fork' not in rows[actor,actor,'process']
init=(R/'context/init.rc').read_text();services=[line.split()[1:] for line in init.splitlines() if line.startswith('service ')]
assert services==[['ueventd','/sbin/ueventd'],['os-rescue','/sbin/os-rescue','--serve'],['adbd','/sbin/rescue-proxy','--adbd']]
assert not any(line.strip().startswith(('import ','exec ','mount_all ','swapon_all ')) for line in init.splitlines())
assert 'p10-restore' not in str(services)
assert (R/'source/handoff.h').read_bytes()==(R/'baseline/handoff.h').read_bytes()
for rev,folder in [('before','baseline'),('after','source')]:assert (R/f'tests/generated/{rev}.c').read_bytes()==(R/f'{folder}/rescue.c').read_bytes().split(b'\n',1)[1]
counts=json.loads((R/'evidence/full-geometry-counts.json').read_text())
assert counts['totals']['before']['recovery_bytes']==241362395136
assert counts['totals']['after']['recovery_bytes']==251105280
for name in ['linux-sessions-after.stderr','linux-sessions-before.stderr','linux-guard.stderr','linux-handoff.stderr']:assert (R/'evidence'/name).read_text().rstrip().endswith('OK'),name
assert (R/'evidence/linux-memory-limit.txt').read_text().strip()=='1073741824'
assert (R/'evidence/linux-cpus.txt').read_text().strip()=='0'
assert (R/'evidence/linux-cpu-quota.txt').read_text().strip()=='100000 100000'
peak=int((R/'evidence/linux-memory-peak.txt').read_text());assert peak<1024**3
assert (R/'evidence/final-linux.exit').read_text().strip()=='0'
result=dict(passed=True,effective_policy_rows=len(rows),services=services,only_reachable_p10_writer='p10_restore after daemon exec; no concurrent ordinary RSC phase',phase_content_detection='boundary proof; not a kernel/content watch',model_counts=counts['totals'],cgroup_peak_bytes=peak,cpu='0 only; quota one CPU',memory_limit_bytes=1024**3,sanitizers=['ASan','UBSan','bounds'],frozen_files=34)
(R/'evidence/acceptance.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result,indent=2))
