#!/usr/bin/env python3
"""Selective remote read only. Outputs confined to this spike; never invokes old fixture scripts."""
from pathlib import Path
import subprocess, json, base64, hashlib, sys
HERE=Path(__file__).resolve().parents[1]
wrapper=HERE.parent/'2026-11-06-asus-android17-network-runtime/source/remote.py'
# Parse its SSH literal without executing the module's stdin-driven main.
import ast
mod=ast.parse(wrapper.read_text()); ssh=next(ast.literal_eval(n.value) for n in mod.body if isinstance(n,ast.Assign) and any(isinstance(t,ast.Name) and t.id=='SSH' for t in n.targets))
paths='''inputs/Connectivity/bpf/progs/netd.c
inputs/Connectivity/bpf/progs/netd.h
inputs/Connectivity/bpf/progs/include/bpf_helpers.h
inputs/Connectivity/bpf/loader/NetBpfLoad.cpp
inputs/Connectivity/bpf/netd/BpfHandler.cpp
inputs/Connectivity/service/src/com/android/server/BpfNetMaps.java
handoff-r1/connectivity-source/bpf/progs/netd.c
handoff-r1/manifest.json
handoff-r1/network.config
evidence/connectivity-head.txt
run-r18/inputs.json
run-r18/result.json
run-r18/qemu-command.json
run-r18/serial.log
source/cross_profile_probe.cpp
artifacts/bpf-original/netd.build.json
kernel/include/linux/bpf.h
kernel/include/linux/bpf_verifier.h
kernel/include/linux/filter.h
kernel/include/uapi/linux/bpf.h
kernel/include/net/sock.h
kernel/include/net/inet_sock.h
kernel/include/net/net_namespace.h
kernel/include/linux/bpf-cgroup.h
kernel/kernel/bpf/verifier.c
kernel/kernel/bpf/syscall.c
kernel/kernel/bpf/helpers.c
kernel/kernel/bpf/hashtab.c
kernel/kernel/bpf/arraymap.c
kernel/kernel/bpf/core.c
kernel/kernel/bpf/Makefile
kernel/kernel/bpf/cgroup.c
kernel/net/core/filter.c
kernel/net/core/sock.c
kernel/net/core/sock_diag.c
kernel/net/socket.c
kernel/net/ipv4/inet_hashtables.c
kernel/net/ipv4/udp.c
kernel/net/ipv4/tcp_ipv4.c
kernel/net/ipv4/af_inet.c
kernel/net/ipv6/inet6_hashtables.c
kernel/net/ipv6/udp.c
kernel/net/ipv6/tcp_ipv6.c
kernel/net/ipv6/af_inet6.c
kernel/include/net/inet_hashtables.h
kernel/include/net/inet6_hashtables.h
kernel/include/net/udp.h
kernel/include/net/tcp.h
kernel/include/linux/rcupdate.h
kernel/include/linux/rculist_nulls.h'''.splitlines()
if len(sys.argv)>1: paths=sys.argv[1:]
script='''import pathlib,json,base64,hashlib
root=pathlib.Path('/srv/android/asus-network-runtime')
paths=PATHS
out=[]
for rel in paths:
 p=root/rel
 if not p.is_file():out.append(dict(path=rel,missing=True));continue
 b=p.read_bytes()
 assert len(b)<2000000
 out.append(dict(path=rel,bytes=len(b),sha256=hashlib.sha256(b).hexdigest(),data=base64.b64encode(b).decode()))
print(json.dumps(out))
'''.replace('PATHS',repr(paths))
p=subprocess.run(ssh+['bash -s'],input="ulimit -t 60\nulimit -v 1048576\nexec python3 - <<'PYREMOTE'\n"+script+"\nPYREMOTE\n",text=True,capture_output=True,timeout=90,check=True)
items=json.loads(p.stdout)
for x in items:
 if 'data' in x:
  b=base64.b64decode(x.pop('data')); d=HERE/'inputs/frozen'/x['path'];d.parent.mkdir(parents=True,exist_ok=True);d.write_bytes(b)
(HERE/('evidence/frozen-extra.json' if len(sys.argv)>1 else 'evidence/frozen-selection.json')).write_text(json.dumps(dict(root='/srv/android/asus-network-runtime',wrapper_sha256=hashlib.sha256(wrapper.read_bytes()).hexdigest(),files=items),indent=2)+'\n')
print(json.dumps(dict(files=len(items),bytes=sum(x.get('bytes',0) for x in items),missing=[x['path'] for x in items if x.get('missing')]),indent=2))
