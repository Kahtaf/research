"""One bounded add-needed-only run over the frozen public importer; no build tools."""
from pathlib import Path
import base64
import hashlib
import importlib.util
import json
import subprocess
import sys

sys.dont_write_bytecode = True
root = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('transport', root.parent / '2026-11-06-asus-product-input-build-kit/scripts/remote.py')
transport = importlib.util.module_from_spec(spec)
spec.loader.exec_module(transport)
payload = r'''
from pathlib import Path
import base64,hashlib,json,os,resource,subprocess,time
started=time.monotonic()
os.sched_setaffinity(0,{min(os.sched_getaffinity(0))})
resource.setrlimit(resource.RLIMIT_AS,(1024**3,1024**3))
resource.setrlimit(resource.RLIMIT_CPU,(40,40))
resource.setrlimit(resource.RLIMIT_FSIZE,(8*1024**2,8*1024**2))
r=Path('/srv/android/asus-camera-property-map-repair-20261107-static')
r.mkdir(exist_ok=False)
source=Path('/srv/android/asus-camera-arm32-route/public/vendor_lib_libcam_utils.so')
tool=Path('/usr/bin/patchelf')
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
assert sha(source)=='be8cb386e5f5ea7045b24017870d85b67774518f6e9ae9efd3ed1c00f5dcdcec'
assert sha(tool)=='35fc95654387035338a74bb8cf62fde3712ec83dd8ca30a768deb714d07f063a'
output=r/'importer-needed-only.so'
argv=[str(tool),'--output',str(output),'--add-needed','libasus_camera_legacy_property_map.so',str(source)]
p=subprocess.run(argv,capture_output=True,text=True,timeout=20)
assert p.returncode==0,p.stderr
assert sha(source)=='be8cb386e5f5ea7045b24017870d85b67774518f6e9ae9efd3ed1c00f5dcdcec'
size=sum(p.stat().st_size for p in r.rglob('*') if p.is_file())
assert size<=32*1024**2
receipt={'argv':argv,'returncode':p.returncode,'stdout':p.stdout,'stderr':p.stderr,'original_sha256':sha(source),'needed_only_sha256':sha(output),'patchelf_sha256':sha(tool),'scratch_bytes':size,'cpu_affinity':list(os.sched_getaffinity(0)),'address_space_limit':resource.getrlimit(resource.RLIMIT_AS),'cpu_limit_seconds':resource.getrlimit(resource.RLIMIT_CPU),'elapsed_seconds':time.monotonic()-started,'outer_ssh_timeout_seconds':110,'subprocess_timeout_seconds':20,'runtime_executed':False}
(r/'receipt.json').write_text(json.dumps(receipt,indent=2)+'\n')
print(json.dumps({'receipt':receipt,'artifact_base64':base64.b64encode(output.read_bytes()).decode()}))
'''
p = subprocess.run(transport.SSH + ['python3 -B -'], input=payload, text=True, capture_output=True, timeout=110)
if p.returncode:
    raise RuntimeError(p.stderr or p.stdout)
result = json.loads(p.stdout)
data = base64.b64decode(result['artifact_base64'], validate=True)
assert hashlib.sha256(data).hexdigest() == result['receipt']['needed_only_sha256']
(root / 'artifacts/importer-needed-only.so').write_bytes(data)
(root / 'evidence/add-needed.json').write_text(json.dumps(result['receipt'], indent=2) + '\n')
print(json.dumps(result['receipt'], indent=2))
