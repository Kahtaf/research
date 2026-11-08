from pathlib import Path
import subprocess,hashlib,json
r=Path('/srv/android/asus-camera-property-map-review-20261106')
patchelf=Path('/usr/bin/patchelf');assert hashlib.sha256(patchelf.read_bytes()).hexdigest()=='35fc95654387035338a74bb8cf62fde3712ec83dd8ca30a768deb714d07f063a'
a=[str(patchelf),'--output',str(r/'reproduced-WITNESS.so'),'--rename-dynamic-symbols',str(r/'src/import-renames.txt'),'--add-needed','libasus_camera_legacy_property_map.so',str(r/'importer-original.so')]
p=subprocess.run(a,capture_output=True,text=True,timeout=20);assert p.returncode==0,p.stderr
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
result={'argv':a,'rc':p.returncode,'stderr':p.stderr,'original_sha256':sha(r/'importer-original.so'),'reproduced_witness_sha256':sha(r/'reproduced-WITNESS.so'),'patchelf_sha256':sha(patchelf),'scratch_bytes':sum(p.stat().st_size for p in r.rglob('*') if p.is_file())}
assert result['original_sha256']=='be8cb386e5f5ea7045b24017870d85b67774518f6e9ae9efd3ed1c00f5dcdcec'
assert result['reproduced_witness_sha256']=='625bfeb69cdc3118661588264e030d2ec07be96e9f3cf967a66f79eba0e743fa'
assert result['scratch_bytes']<=32*1024**2
print(json.dumps(result,indent=2))
