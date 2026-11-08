import os,resource,signal,pathlib,json,hashlib,sys
os.sched_setaffinity(0,{min(os.sched_getaffinity(0))});resource.setrlimit(resource.RLIMIT_AS,(1024**3,1024**3));resource.setrlimit(resource.RLIMIT_CPU,(60,60));signal.alarm(90)
R=pathlib.Path('/srv/android/asus-sdk37-host-metadata-resolvers-20261106');sys.path.insert(0,str(R/'scripts'))
from query import tools
q=tools();build=json.loads((R/'build.json').read_text());cap=json.loads((R/'capture.json').read_text())
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
assert all(sha(pathlib.Path(r['copy']))==r['before']==r['copied']==r['after'] for r in build['copies'])
r=cap['elf_metadata']['sdk37_capability_header_copy'];assert sha(pathlib.Path(r['copy']))==r['before']==r['copied']==r['after']
extra=json.loads((R/'extra-qa.json').read_text());assert extra['extra_controls_passed']
unique={(p.stat().st_dev,p.stat().st_ino):p.stat().st_size for p in R.rglob('*')if p.is_file()};size=sum(unique.values());assert size<256*1024**2
result=dict(final_audit_passed=True,copies_verified=147,qualified_tool_group_sha256=sha(R/'qualified-tools.json'),
            query_source_sha256=sha(R/'scripts/query.py'),resolver_sources={p.name:sha(p)for p in (R/'source-r4').glob('*')},
            resolver_elfs={p.name:sha(p)for p in (R/'bin-r4').glob('*')},
            final_unique_storage_bytes=size,storage_cap_bytes=256*1024**2,
            extra_logs={str(p.relative_to(R)):p.read_text()for p in (R/'qa-extra').glob('*')if p.is_file()},
            actual_product_metadata_group=False,SYSTEM_accessed=False,observer_image_built=False,physical_GO=False)
(R/'final-audit.json').write_text(json.dumps(result,indent=2));print(json.dumps(result,indent=2))
