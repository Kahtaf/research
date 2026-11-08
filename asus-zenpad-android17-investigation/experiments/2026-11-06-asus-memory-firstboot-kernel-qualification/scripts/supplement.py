"""Read frozen physical manifest and narrow Kconfig/source definitions only."""
from pathlib import Path
import importlib.util
import json
import sys

sys.dont_write_bytecode = True

R = Path(__file__).resolve().parents[2]
S = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('authorized_remote', R/'2026-11-06-asus-product-input-build-kit/scripts/remote.py')
remote = importlib.util.module_from_spec(spec)
spec.loader.exec_module(remote)
code = r'''
from pathlib import Path
import gzip,hashlib,json,os,re,resource
os.sched_setaffinity(0,{min(os.sched_getaffinity(0))})
resource.setrlimit(resource.RLIMIT_AS,(1024**3,1024**3))
resource.setrlimit(resource.RLIMIT_CPU,(120,120))
O=Path('/srv/android/asus-memory-firstboot-kernel-qualification-20261106')
assert not (O/'supplement.json').exists()
V=Path('/srv/android/asus-sdk37-lmkd-functional/kernel-memory-r1/source')
B=Path('/srv/android/asus-bmc156-full-kernel-r1/kernel')
m=Path('/srv/android/asus-bmc156-full-kernel-r1/evidence/post-source-manifest.json.gz')
d=json.loads(gzip.decompress(m.read_bytes()))
inspection=json.loads((O/'inspection.json').read_text())
paths=sorted({r['path'] for rows in inspection['sources'].values() for r in rows}|{'drivers/irqchip/irq-gic-v3.c'})
out={'limits':{'affinity':sorted(os.sched_getaffinity(0)),'address_space_bytes':resource.getrlimit(resource.RLIMIT_AS)[0]},'physical_manifest':{'path':str(m),'compressed_sha256':hashlib.sha256(m.read_bytes()).hexdigest(),'canonical_json_sha256':hashlib.sha256(json.dumps(d,sort_keys=True,separators=(',',':')).encode()).hexdigest(),'files':len(d)},'selected_physical_manifest_pins':{p:d[p] for p in paths},'definitions':[],'historical_memory_build_status':json.loads((V.parent/'resume-r1/status.json').read_text())}
targets={'CMA_DEBUGFS','DEBUG_PREEMPT','PREEMPTIRQ_EVENTS','PREEMPT_TRACER','ZRAM_MEMORY_TRACKING','SCHED_DEBUG','MTK_SCHED_RQAVG_US','CMA','MTK_SSMR'}
for root,label in [(V,'virtual'),(B,'physical')]:
 for rel in ['lib/Kconfig.debug','kernel/trace/Kconfig','mm/Kconfig','mm/Kconfig.debug','drivers/block/zram/Kconfig','kernel/Kconfig.hz','init/Kconfig','arch/arm64/Kconfig','arch/arm64/Kconfig.debug','kernel/sched/Kconfig']:
  p=root/rel
  if not p.is_file():continue
  text=p.read_text(); lines=text.splitlines(True)
  for i,line in enumerate(lines):
   match=re.match(r'(?:menu)?config (\w+)\s*$',line)
   if match and match[1] in targets:
    end=next((j for j in range(i+1,len(lines)) if re.match(r'(?:menu)?config |(?:end)?menu\b|endchoice\b',lines[j])),min(i+90,len(lines)))
    out['definitions'].append({'tree':label,'path':rel,'file_sha256':hashlib.sha256(p.read_bytes()).hexdigest(),'line':i+1,'symbol':match[1],'text':''.join(lines[i:end])})
 for rel in ['kernel/sched/core.c','kernel/sched/fair.c','kernel/sched/sched.h','mm/page_alloc.c','drivers/block/zram/zram_drv.c','kernel/trace/trace_irqsoff.c']:
  p=root/rel
  if not p.is_file():continue
  lines=p.read_text().splitlines()
  for i,line in enumerate(lines):
   if any('CONFIG_'+t in line for t in ['MTK_SCHED_RQAVG_US','SCHED_DEBUG','ZRAM_MEMORY_TRACKING']):
    out['definitions'].append({'tree':label,'path':rel,'file_sha256':hashlib.sha256(p.read_bytes()).hexdigest(),'line':i+1,'text':'\n'.join(lines[max(0,i-2):i+12])})
raw=json.dumps(out,indent=2)+'\n';(O/'supplement.json').write_text(raw);print(raw)
'''
data = json.loads(remote.run(code))
(S/'evidence/remote-supplement.json').write_text(json.dumps(data, indent=2)+'\n')
print(json.dumps({'physical_manifest':data['physical_manifest'],'definitions':[(d['tree'],d.get('symbol'),d['path'],d['line']) for d in data['definitions']]},indent=2))
