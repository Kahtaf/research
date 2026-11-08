from pathlib import Path
import json,hashlib,difflib,gzip
p=Path(__file__).resolve().parents[1]
base=p.parent/'2026-11-06-asus-bmc156-full-kernel'
def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()
manifest=json.load(gzip.open(base/'evidence/r5-source-manifest.json.gz'))
for k,v in json.loads((base/'patches/pre-post-hashes.json').read_text()).items():manifest[k]=v['after']
canonical=hashlib.sha256(json.dumps(manifest,sort_keys=True).encode()).hexdigest()
assert canonical == 'c636d9abad7de61e242268372a3b6e3e0cc0ff23f1926274db21f17a6dd81124'
assert manifest == json.load(gzip.open(p/'evidence/physical-bmc-source-manifest.json.gz'))
# Record the exact serialization as well as the parent's canonical receipt.
pre=dict(manifest);delta={};patch=[]
for file in sorted((p/'source/current').rglob('*')):
 if not file.is_file():continue
 rel=str(file.relative_to(p/'source/current'));orig=p/'source/original'/rel
 before=sha(orig) if orig.exists() else None
 assert pre.get(rel)==before,(rel,pre.get(rel),before)
 after=sha(file);delta[rel]={'before':before,'after':after,'after_bytes':file.stat().st_size}
 patch.extend(difflib.unified_diff(orig.read_text().splitlines(True) if orig.exists() else [],file.read_text().splitlines(True),fromfile='a/'+rel if orig.exists() else '/dev/null',tofile='b/'+rel))
 manifest[rel]=after
(p/'patches/audio-copy.patch').write_text(''.join(patch));(p/'patches/pre-post.json').write_text(json.dumps(delta,indent=2)+'\n')
for name,data in [('physical-bmc156-before',pre),('future-audio-after',manifest)]:
 with gzip.GzipFile(filename=str(p/'patches'/(name+'.json.gz')),mode='wb',mtime=0) as f:f.write(json.dumps(data,sort_keys=True,separators=(',',':')).encode())
inputs={str(f.relative_to(p)):sha(f) for f in (p/'source/original').rglob('*') if f.is_file()}
for path,actual in inputs.items():
 rel=path.removeprefix('source/original/');assert pre[rel]==actual,(rel,actual,pre[rel])
(p/'evidence/source-pins.json').write_text(json.dumps({'fixture':'/srv/android/asus-bmc156-full-kernel-r1/kernel','files':inputs,'all_original_copies_match_physical_bmc_manifest':True},indent=2)+'\n')
runtime=json.loads((base/'evidence/r5-runtime-source-preservation.json').read_text())['files']
r5delta=json.loads((base/'evidence/r5-source-receipt.json').read_text())['changes']
paths=set(runtime)|set(r5delta)|set(json.loads((base/'patches/pre-post-hashes.json').read_text()))
expected={x:pre[x] for x in sorted(paths)}
(p/'evidence/preservation-expected.json').write_text(json.dumps(expected,indent=2)+'\n')
print(json.dumps({'changed_paths':len(delta),'patch_sha256':sha(p/'patches/audio-copy.patch'),'original_files_verified':len(inputs),'base_manifest_files':len(pre),'base_manifest_canonical_sha256':canonical,'preservation_paths':len(expected)},indent=2))
