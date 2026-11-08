"""Read-only libsepol queries of the exact saved stock binary policy."""
from pathlib import Path
import hashlib,json,subprocess
S=Path(__file__).resolve().parents[1];W=S.parent
P=W/'2026-11-06-asus-stock-programmatic-control/artifacts/stock-boot.sepolicy'
Q=W/'2026-11-06-asus-stock-programmatic-control/artifacts/build-v1/policy_probe'
B=P.read_bytes();assert hashlib.sha256(B).hexdigest()=='873141c3874066341dcb4e2c7be4eb3f664686635ee3f84d2c4100f557ae740f'
(S/'inputs/stock-boot.sepolicy').write_bytes(B)
(S/'source/policy_probe.c').write_bytes((W/'2026-11-06-asus-stock-programmatic-control/source/policy_probe.c').read_bytes())
queries=[('shell','ctl_default_prop','property_service','set'),('system_server','ctl_default_prop','property_service','set'),('shell','recovery_service','service_manager','find'),('system_server','recovery_service','service_manager','add'),('shell','servicemanager','binder','call'),('shell','system_server','binder','call'),('shell','system_server','binder','transfer'),('system_server','shell','binder','transfer'),('system_server','property_socket','sock_file','write'),('system_server','init','unix_stream_socket','connectto'),('system_server','uncrypt_socket','sock_file','write'),('system_server','uncrypt','unix_stream_socket','connectto'),('system_server','system_server','unix_stream_socket','create'),('system_server','system_server','unix_stream_socket','connect'),('system_server','system_server','unix_stream_socket','read'),('system_server','system_server','unix_stream_socket','write'),('system_server','system_server','unix_stream_socket','getopt'),('init','uncrypt','process','transition'),('uncrypt','uncrypt_exec','file','entrypoint'),('uncrypt','misc_block_device','blk_file','write'),('uncrypt','misc_block_device','blk_file','open'),('uncrypt','misc_block_device','blk_file','read'),('shell','binder_device','chr_file','open'),('shell','binder_device','chr_file','ioctl'),('shell','binder_device','chr_file','read'),('shell','binder_device','chr_file','write')]
for label in ['block_device','para_block_device']:
 for perm in ['open','write','getattr']:
  queries.append(('uncrypt',label,'blk_file',perm))
process_types={'shell','system_server','init','uncrypt','servicemanager'};out=[]
for src,dst,cl,perm in queries:
 source=f'u:r:{src}:s0';target=f'u:{"r" if dst in process_types else "object_r"}:{dst}:s0'
 p=subprocess.run([str(Q),str(P),source,target,cl,perm],capture_output=True,text=True,timeout=5)
 row=dict(source=source,target=target,object_class=cl,permission=perm,exit_code=p.returncode)
 if p.returncode:row.update(stdout=p.stdout,stderr=p.stderr)
 else:row.update(json.loads(p.stdout))
 out.append(row)
(S/'evidence/policy-queries.json').write_text(json.dumps(dict(policy_sha256=hashlib.sha256(B).hexdigest(),probe_binary=str(Q),probe_sha256=hashlib.sha256(Q.read_bytes()).hexdigest(),probe_source_sha256=hashlib.sha256((S/'source/policy_probe.c').read_bytes()).hexdigest(),queries=out,device_policy_changed=False),indent=2)+'\n')
for r in out:print(r['source'],r['target'],r['object_class'],r['permission'],r.get('allowed',r['exit_code']))
