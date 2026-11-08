from pathlib import Path
import json,gzip,tarfile,hashlib
p=Path(__file__).resolve().parents[1];i=p/'inputs'
sha=lambda b:hashlib.sha256(b).hexdigest()
b=json.loads(gzip.decompress((i/'patches/physical-bmc156-before.json.gz').read_bytes()));a=json.loads(gzip.decompress((i/'patches/future-audio-after.json.gz').read_bytes()));s=json.loads(gzip.decompress((i/'evidence/physical-bmc-source-manifest.json.gz').read_bytes()))
assert b==s
changes={k:{'before':b.get(k),'after':a.get(k)} for k in sorted(b.keys()|a.keys()) if b.get(k)!=a.get(k)}
expected=json.loads((i/'patches/pre-post.json').read_text());assert changes=={k:{'before':v['before'],'after':v['after']} for k,v in expected.items()}
pins=json.loads((i/'evidence/remote/evidence/compiler-inputs.json').read_text())
with tarfile.open(i/'evidence/remote/evidence/compiler-inputs.tar.gz') as t:
 members={m.name:m for m in t.getmembers() if m.isfile()};assert len(members)==len(pins)==504
 for f,v in pins.items():
  data=t.extractfile(members[f.lstrip('/')]).read();assert len(data)==v['bytes'];assert sha(data)==v['sha256']
source=json.loads((i/'evidence/source-pins.json').read_text())['files']
for f,v in source.items():
 assert sha((i/f).read_bytes())==v
 if f.startswith('source/original/'):assert b[f.removeprefix('source/original/')]==v
(p/'evidence/integrity-audit.json').write_text(json.dumps({'before_entries':len(b),'after_entries':len(a),'base_equals_saved_physical_manifest':True,'exact_changes':changes,'all_504_archive_inputs_match_pins':True,'source_pins_verified':len(source),'original_sources_match_physical_manifest':True,'physical_parent_canonical_sha256':sha(json.dumps(b,sort_keys=True).encode()),'patch_sha256':sha((i/'patches/audio-copy.patch').read_bytes())},indent=2)+'\n')
print('PASS exact 3 manifest changes, 504 archive source/header inputs and',len(source),'source pins')
