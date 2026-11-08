from pathlib import Path
import re,json,hashlib
P=Path(__file__).resolve().parent.parent;W=P.parent
V=W/'2026-11-06-asus-firstboot-parity-continuation/artifacts/frozen-r3/evidence/r7.config';B=P/'inputs/4-resolved.config'
def parse(p):
 d={}
 for l in p.read_text().splitlines():
  m=re.match(r'(CONFIG_\w+)=(.*)',l)
  if m:d[m[1]]=m[2]
  m=re.match(r'# (CONFIG_\w+) is not set',l)
  if m:d[m[1]]='n'
 return d
v=parse(V);b=parse(B);names=sorted({k for k in v.keys()|b.keys() if re.search(r'^CONFIG_(PSI|ZRAM|ZSMALLOC|ZPOOL|ZBUD|SWAP|MEMCG|CGROUP|CPUSETS|BLK_CGROUP|CMA|COMPACTION|MIGRATION|TRANSPARENT_HUGE|FRONTSWAP|CLEANCACHE|KSM|LZ4|CRYPTO_LZ4|VM_EVENT|PROC_PAGE|NUMA|HIGHMEM|ARM64_.*PAGES|64BIT|SMP$|HZ|PREEMPT|SLUB|SLAB|COMPACT_UNEVICTABLE|SECCOMP|SECURITY|DEFAULT_MMAP_MIN|MMU$|OOM)',k)})
a={'scope':'Selected memory/cgroup/security config; not whole kernel equivalence','virtual_config_sha256':hashlib.sha256(V.read_bytes()).hexdigest(),'physical_config_sha256':hashlib.sha256(B.read_bytes()).hexdigest(),'values':[{'name':k,'virtual_r7':v.get(k,'absent'),'physical_BMC':b.get(k,'absent')} for k in names]}
a['differences']=[x for x in a['values'] if x['virtual_r7']!=x['physical_BMC']];(P/'evidence/config-parity.json').write_text(json.dumps(a,indent=2));print(json.dumps(a['differences'],indent=2))
