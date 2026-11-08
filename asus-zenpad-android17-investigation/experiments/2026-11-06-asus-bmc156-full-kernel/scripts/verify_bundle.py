from pathlib import Path
import hashlib,json,gzip,zlib,struct,difflib
R=Path(__file__).resolve().parents[1]
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
checks=0
def check(condition,message):
 global checks
 assert condition,message
 checks+=1
m=json.loads((R/'MANIFEST.json').read_text())
for rel,v in m['files'].items():
 p=R/rel;check(p.is_file() and p.resolve().is_relative_to(R) and not p.is_symlink(),rel)
 check(p.stat().st_size==v['bytes'] and sha(p)==v['sha256'],rel)
check(m['total_bytes']<12*1024**2,'compact exported payload')
v=json.loads((R/'evidence/full-verification.json').read_text());s=json.loads((R/'evidence/build-status.json').read_text())
check(s['exit']==0 and s['status']=='complete','real build status')
check(s['max_jobs']==1 and len(s['affinity'])==1,'serial one CPU')
check(s['commands'][-1]['command'][-1]=='Image.gz-dtb' and s['commands'][-1]['exit']==0,'full target exit')
check(v['full_kernel_compiled'] and not v['physical_tested'] and not v['product_integrated'],'qualification scope')
image=(R/'artifacts/Image.gz-dtb').read_bytes();z=zlib.decompressobj(31);raw=z.decompress(image)+z.flush();dt=z.unused_data
check(z.eof and raw[56:60]==b'ARM\x64','complete compressed ARM64 Image')
check(dt[:4]==bytes.fromhex('d00dfeed') and struct.unpack_from('>I',dt,4)[0]==len(dt),'one complete appended FDT')
check(dt==(R/'artifacts/asus-p00a.dtb').read_bytes(),'DT artifact equality')
check(hashlib.sha256(raw).hexdigest()==v['artifacts']['arch/arm64/boot/Image']['sha256'],'decompressed Image pin')
check(hashlib.sha256(dt).hexdigest()=='a099d0538b270e23ec0d034b507eef9248252a3c459a11aa70edb6520bfd2b77','physical r5 DT pin')
check(b'asus,allow-battery-charging' not in dt,'charging opt-in absent')
check(sha(R/'artifacts/resolved.config')=='10b212cabd28aad012582e86c64695ccd450650b4e09ec8da30c21e094f377c2','exact accelerometer config')
start=raw.index(b'IKCFG_ST')+8;end=raw.index(b'IKCFG_ED',start)
check(gzip.decompress(raw[start:end])==(R/'artifacts/resolved.config').read_bytes(),'embedded config exact')
base=json.loads(gzip.decompress((R/'evidence/r5-source-manifest.json.gz').read_bytes()));changes=json.loads((R/'patches/pre-post-hashes.json').read_text())
check(len(base)==62224 and len(changes)==9,'full r5 baseline + nine paths')
post=dict(base)
for rel,c in changes.items():
 check(base.get(rel)==c['before'],'exact preimage '+rel)
 check(sha(R/'source'/rel)==c['after'],'exact postimage '+rel);post[rel]=c['after']
check(len(post)==62228,'complete postimage file set')
check(hashlib.sha256(json.dumps(post,sort_keys=True).encode()).hexdigest()==v['source_manifests']['post']['canonical_json_sha256'],'full postimage manifest reconstructed exactly')
check(sha(R/'patches/kernel-from-physical-r5.patch')=='1f40942ee014bda87c4e4c382b881e27c98b2034b227a06020a7e96126399cec','original patch unchanged')
check(len(v['config_delta'])==4,'four config changes')
check(v['dt_byte_identical'] and not v['layout']['static_overlaps'],'DT and static layout verification')
for name in ['282_runtime_sources','58_runtime_options','16_network_options','290_firstboot_source_files','134_firstboot_options','18_r5_runtime_radio_charging_network_symbols','all_original_r5_source_files_unchanged','complete_owned_source_manifest_unchanged']:
 check(name in v['checks'],name)
log=gzip.decompress((R/'evidence/Image.gz-dtb.log.gz').read_bytes()).decode(errors='replace')
for token in ['bmc156_acc/bmc156_acc.o','LD      vmlinux','Image.gz-dtb']:
 check(token in log,'real full build log '+token)
check('fuzz' not in gzip.decompress((R/'evidence/patch-apply.log.gz').read_bytes()).decode().lower(),'patch without fuzz')
print('PASS',checks,'local bundle/hash/ARM64/config/source-preservation checks; no physical or full-product claim')
