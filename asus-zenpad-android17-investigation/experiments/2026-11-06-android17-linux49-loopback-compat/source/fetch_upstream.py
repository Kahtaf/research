#!/usr/bin/env python3
from pathlib import Path
import urllib.request, json, hashlib
R=Path(__file__).resolve().parents[1]
ref='v5.10'
paths=['net/core/filter.c','net/core/bpf_sk_storage.c','include/net/bpf_sk_storage.h','kernel/bpf/verifier.c','include/linux/bpf.h','include/linux/bpf_verifier.h','include/uapi/linux/bpf.h','kernel/bpf/bpf_local_storage.c','include/linux/bpf_local_storage.h','net/core/sock.c','net/ipv4/af_inet.c','net/ipv6/af_inet6.c','kernel/bpf/cgroup.c','include/linux/bpf-cgroup.h','tools/testing/selftests/bpf/verifier/ref_tracking.c']
manifest=[]
for rel in paths:
 url=f'https://raw.githubusercontent.com/torvalds/linux/{ref}/{rel}'
 b=urllib.request.urlopen(url,timeout=30).read(); p=R/'inputs/upstream'/ref/rel;p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(b)
 manifest.append(dict(url=url,path=str(p.relative_to(R)),bytes=len(b),sha256=hashlib.sha256(b).hexdigest()))
(R/'evidence/upstream-selection.json').write_text(json.dumps(manifest,indent=2)+'\n')
print('captured',len(manifest),'files',sum(x['bytes'] for x in manifest),'bytes')
