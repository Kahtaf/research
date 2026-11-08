import os,resource,signal,pathlib,json,hashlib,base64,subprocess
os.sched_setaffinity(0,{min(os.sched_getaffinity(0))});resource.setrlimit(resource.RLIMIT_AS,(1024**3,1024**3));resource.setrlimit(resource.RLIMIT_CPU,(60,60));signal.alarm(90)
P=pathlib.Path;R=P('/srv/android/asus-sdk37-host-metadata-resolvers-20261106');I=R/'inputs-r4'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
build=json.loads((R/'build.json').read_text());assert all(r['before']==r['copied']==r['after']==sha(P(r['copy'])) for r in build['copies'])
exports={}
for n in ['resolve_fs_config','resolve_contexts']:
 p=R/'bin-r4'/n;exports[n]=dict(bytes=p.stat().st_size,sha256=sha(p),base64=base64.b64encode(p.read_bytes()).decode())
sources={}
for p in (I/'source').rglob('*'):
 if p.is_file():sources[str(p.relative_to(I/'source'))]=dict(sha256=sha(p),text=p.read_text())
# Narrow generated-header/ABI evidence: the exported fs_config C signature and binary record layout
# are sufficient; these callers need no unavailable AOSP generated header.
metadata={}
for p in [I/'lib64/libcutils.so',I/'lib64/libselinux.so',I/'lib64/libpcre2.so',I/'bin/sefcontext_compile',I/'compiler/gcc']:
 metadata[p.name]=dict(sha256=sha(p),notes=subprocess.check_output(['/usr/bin/readelf','-n',str(p)],text=True),comment=subprocess.run(['/usr/bin/readelf','-p','.comment',str(p)],capture_output=True,text=True).stdout)
# Freeze current source-side capability ABI header, only this explicit public source file.
p=P('/srv/android/lineage24/bionic/libc/kernel/uapi/linux/capability.h');q=I/'source/bionic/libc/kernel/uapi/linux/capability.h'
if p.exists():
 b=p.read_bytes();before=hashlib.sha256(b).hexdigest();q.parent.mkdir(parents=True,exist_ok=True);q.write_bytes(b);after=sha(p);assert before==sha(q)==after
 sources['bionic/libc/kernel/uapi/linux/capability.h']=dict(sha256=before,text=b.decode())
 metadata['sdk37_capability_header_copy']=dict(source=str(p),copy=str(q),before=before,copied=sha(q),after=after)
logs={str(p.relative_to(R)):p.read_text(errors='replace')for top in ['build-r1','build-r2','build-r3','build-r4','qa-logs'] for p in (R/top).glob('*')if p.is_file()and p.suffix in ['.log','.stdout','.stderr','.json','.d']}
# Pin host compiler's diagnostic executables and interpreter without rebuilding anything.
probes={}
for args in [['--version'],['-dumpmachine']]:
 probes[' '.join(args)]=subprocess.check_output([str(I/'compiler/gcc'),*args],text=True)
unique={(p.stat().st_dev,p.stat().st_ino):p.stat().st_size for p in R.rglob('*')if p.is_file()}
result=dict(capture_passed=True,resolver_elfs=exports,source_snapshots=sources,elf_metadata=metadata,compiler_probes=probes,
            qualified_tools=json.loads((R/'qualified-tools.json').read_text()),qualified_tools_sha256=sha(R/'qualified-tools.json'),
            logs=logs,total_unique_file_bytes=sum(unique.values()),storage_cap_bytes=256*1024**2,
            copy_receipts_sha256=sha(R/'copy-receipts.json'),actual_product_outputs_accessed=False)
assert result['total_unique_file_bytes']<result['storage_cap_bytes'];(R/'capture.json').write_text(json.dumps(result,indent=2));print(json.dumps(result,indent=2))
