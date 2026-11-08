"""One bounded observation of the existing r6 handle; never launch or retry."""
from pathlib import Path
import datetime
import importlib.util
import json

ROOT = Path(__file__).resolve().parents[1]
remote_path = ROOT.parent / '2026-11-06-asus-product-input-build-kit/scripts/remote.py'
spec = importlib.util.spec_from_file_location('r6_observation_remote', remote_path)
remote = importlib.util.module_from_spec(spec)
spec.loader.exec_module(remote)

CODE = r'''
from pathlib import Path
import datetime,json
out={'observed_utc':datetime.datetime.now(datetime.timezone.utc).isoformat()}
base=Path('/srv/android/asus-reviewed-build-kit/r3/attempt')
for name in ['started','launch','FAILED','complete']:
 p=base/(name+'.json')
 if p.exists():out[name]=json.loads(p.read_text())
p=base/'integration.json'
if p.exists():
 d=json.loads(p.read_text())
 out['integration']={k:d[k] for k in ['kernel_sha256','source_patch_sha256','staged_receipt_sha256','physical_boot_verified','full_service_chain_accepted','flash_ready'] if k in d}
prefix=Path('/srv/android/asus-device-product/logs/full-build-r6')
for suffix in ['started','pid','exit-code','finished']:
 p=Path(str(prefix)+'.'+suffix)
 if p.exists():out[suffix]=p.read_text().strip()
for pid in [1546715]+([int(out['pid'])] if 'pid' in out else []):
 p=Path('/proc')/str(pid)
 out.setdefault('processes',{})[str(pid)]={'exists':p.exists(),'cmdline':(p/'cmdline').read_bytes().replace(bytes([0]),b' ').decode(errors='replace') if p.exists() else None,'stat':(p/'stat').read_text() if p.exists() else None}
for key,p in [('build_log',Path(str(prefix)+'.log')),('supervisor_log',Path('/srv/android/asus-r6-product-build/supervisor.log'))]:
 if p.exists():
  with p.open('rb') as f:
   f.seek(max(0,p.stat().st_size-6000))
   out[key]={'bytes':p.stat().st_size,'tail':f.read().decode(errors='replace')}
print(json.dumps(out))
'''

result = json.loads(remote.run(CODE))
stamp = datetime.datetime.now(datetime.timezone.utc).strftime('%Y%m%dT%H%M%S.%fZ')
destination = ROOT / 'evidence' / ('observation-' + stamp + '.json')
destination.write_text(json.dumps(result, indent=2) + '\n')
compact = {k: v for k, v in result.items() if k not in ['started', 'build_log', 'supervisor_log']}
compact['evidence'] = str(destination)
for key in ['build_log', 'supervisor_log']:
 if key in result:
  compact[key] = {'bytes':result[key]['bytes'],'tail':result[key]['tail'][-2600:]}
print(json.dumps(compact, indent=2))
