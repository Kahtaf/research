from pathlib import Path
import hashlib,json,os,resource,struct,subprocess,sys
OWN=Path('/srv/android/asus-bpf-name-product-build-20261107');A=Path('/srv/android/lineage24');P=A/'out/target/product/p00a'
sys.path.insert(0,'/srv/android/asus-reviewed-build-kit/r9-exec-r1/scripts')
from verify_full_images import inspect_system
from verify_product_r3 import installed
assert os.fstat(int(os.environ['REVIEWED_BUILD_LOCK_FD'])).st_ino==15018964
assert resource.getrlimit(resource.RLIMIT_AS)==(resource.RLIM_INFINITY,resource.RLIM_INFINITY)
def sha(p):
 h=hashlib.sha256()
 with Path(p).open('rb') as f:
  for b in iter(lambda:f.read(1048576),b''):h.update(b)
 return h.hexdigest()
def write(name,obj):
 with (OWN/'evidence'/name).open('x') as f:json.dump(obj,f,indent=2);f.write('\n')
source=A/'system/bpf/loader/Loader.cpp'
assert sha(source)=='bb8288818619d492a79fe997c902dc9b64fa67f1f04bff4afb2b047b4511dccf'
lib=P/'system/lib64/libbpf_android.so';libsha=sha(lib)
assert libsha!=json.loads((OWN/'evidence/library-before.json').read_text())['sha256'],'Installed library did not change'
leaf=A/'out/soong/.intermediates/system/bpf/loader/libbpf_android'
# Exact filename and one module only; no broad ELF/source sweep.
matches=[dict(path=str(p),sha256=libsha,bytes=p.stat().st_size) for p in leaf.rglob('libbpf_android.so') if p.is_file() and sha(p)==libsha]
assert matches,'Installed library has no compiled native module match'
write('compiled-library.json',dict(installed_path=str(lib),sha256=libsha,bytes=lib.stat().st_size,compiled_matches=matches,qualified_candidate_sha256='682ed7fd0c69bcf0567d81c4d0d43314fce1c0205172f6a1dd9c263a97c7389e',matches_isolated_candidate=libsha=='682ed7fd0c69bcf0567d81c4d0d43314fce1c0205172f6a1dd9c263a97c7389e'))
limit=3753902080;unit=1048576;img=P/'system.img';raw=OWN/'system-partition.raw'
image=inspect_system(img,limit)
write('raw-reservation.json',dict(path=str(raw),source=image,materializations_total=1))
whole=hashlib.sha256();rows=[];pending=bytearray();written=0
with img.open('rb') as src,raw.open('xb') as dst:
 def emit(data):
  global pending,written
  dst.write(data);whole.update(data);pending.extend(data);written+=len(data)
  while len(pending)>=unit:
   block=bytes(pending[:unit]);del pending[:unit]
   rows.append((len(rows),len(rows)*unit,unit,hashlib.sha256(block).hexdigest()))
 def zeros(n,pattern=b'\0'):
  block=(pattern*(unit//len(pattern)))
  while n:
   take=min(n,unit);emit(block[:take]);n-=take
 if image['sparse']:
  header=src.read(28);_,major,minor,fh,ch,bs,blocks,chunks,checksum=struct.unpack('<I4H4I',header);src.seek(fh)
  for _ in range(chunks):
   hdr=src.read(ch);kind,res,count,total=struct.unpack_from('<2H2I',hdr);n=count*bs
   if kind==0xcac1:
    while n:
     data=src.read(min(n,unit));assert data;emit(data);n-=len(data)
   elif kind==0xcac2:zeros(n,src.read(4))
   elif kind==0xcac3:zeros(n)
   elif kind==0xcac4:src.read(4)
   else:raise ValueError('Unknown sparse chunk')
 else:
  for data in iter(lambda:src.read(unit),b''):emit(data)
 assert written==image['expanded_bytes'] and written<=limit
 zeros(limit-written)
 if pending:rows.append((len(rows),len(rows)*unit,len(pending),hashlib.sha256(pending).hexdigest()))
 dst.flush();os.fsync(dst.fileno())
raw.chmod(0o444)
assert raw.stat().st_size==limit and sum(row[2] for row in rows)==limit
chunkfile=OWN/'evidence/system-1MiB-chunks.tsv'
with chunkfile.open('x') as f:
 f.write('index\toffset\tbytes\tsha256\n')
 for row in rows:f.write('\t'.join(map(str,row))+'\n')
raw_receipt=dict(path=str(raw),bytes=limit,sha256=whole.hexdigest(),mode='0444',allocated_bytes=raw.stat().st_blocks*512,source_system=image,materializations_total=1,all_zero_ranges_written=True,whole_and_1MiB_hashes_computed_during_single_materialization=True,chunk_table=dict(path=str(chunkfile),bytes=chunkfile.stat().st_size,sha256=sha(chunkfile),chunk_bytes=unit,chunks=len(rows)))
write('raw-complete.json',raw_receipt)
b=A/'out/host/linux-x86/bin';debugfs=b/'debugfs'
lib_image=installed(P,'system/lib64/libbpf_android.so',raw,debugfs,libsha)
# Read only the actual property files; compare installed ext4 bytes through prior helper.
prop_paths=['system/build.prop','system/etc/prop.default','root/prop.default','system/system_ext/etc/build.prop','system/product/etc/build.prop','system/vendor/build.prop','system/vendor/default.prop']
props={k:[] for k in ['ro.secure','ro.debuggable','ro.adb.secure']};prop_rows=[]
for rel in prop_paths:
 p=P/rel
 if not p.is_file():continue
 for line in p.read_text().splitlines():
  k,sep,v=line.partition('=')
  if sep and k.strip() in props:props[k.strip()].append(dict(path=rel,value=v.strip()))
 if not rel.startswith('root/'):prop_rows.append(installed(P,rel,raw,debugfs,sha(p)))
assert all(values and all(x['value']=='1' for x in values) for values in props.values()),'Security property mismatch'
# Three established Google/Play core containers only, using prior public artifact receipts.
prior=json.loads(Path('/srv/android/asus-radio-trigger-build-r4/checks/r1/google-signed.json').read_text())
selected={'system/product/apex/com.google.android.gmssystem.prodvic.apex','system/product/priv-app/Phonesky/Phonesky.apk','system/system_ext/priv-app/GoogleServicesFramework/GoogleServicesFramework.apk'}
google=[]
for row in prior['checked']:
 if row['path'] in selected:
  assert sha(P/row['path'])==row['sha256'] and (P/row['path']).stat().st_size==row['size']
  google.append(installed(P,row['path'],raw,debugfs,row['sha256']))
assert len(google)==3
# Ext4 geometry from the sole raw image, no fsck or broad suite.
with raw.open('rb') as f:f.seek(1024);sb=f.read(1024)
assert sb[56:58]==b'\x53\xef'
blocks=struct.unpack_from('<I',sb,4)[0];blockbytes=1024<<struct.unpack_from('<I',sb,24)[0]
assert blocks*blockbytes<=limit
report=dict(system=raw_receipt,source_image=image,installed_libbpf_android=dict(path=str(lib),bytes=lib.stat().st_size,sha256=libsha,compiled_matches=matches,final_ext4=lib_image),security_properties=props,property_files=prop_rows,google_play_core_retained=google,ext4_geometry=dict(blocks=blocks,block_bytes=blockbytes,filesystem_bytes=blocks*blockbytes,partition_bytes=limit),validation_limits='Direct minimal authorized-delta artifact checks. Existing full host validator and broad ELF/policy/network/Google suites not rerun. Ordinary controlled incremental dependency trust accepted. No virtual or physical runtime verification.',preserved_boot=dict(path='/srv/android/asus-radio-trigger-build-r4/checks/r3/UNTESTED-combined-MTKBOOT.img',bytes=9242624,sha256='784d4dc565e7742ea607683d2a67d1fdb066764bddfa369895cbaaf6f048b435',binding='Prior identity retained; metadata verified by continuous-lock supervisor; not rebuilt or rehashed'))
write('artifacts.json',report)
print(json.dumps(report),flush=True)
