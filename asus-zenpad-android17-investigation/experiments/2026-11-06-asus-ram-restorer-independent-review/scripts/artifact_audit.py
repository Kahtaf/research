from pathlib import Path
import hashlib,json,struct,zlib,re
R=Path(__file__).resolve().parents[1];S=R/'snapshot';A=S/'artifacts'
sha=lambda b:hashlib.sha256(b).hexdigest()
def up(n,a):return (n+a-1)//a*a
def archive(buf):
 result={};p=0
 while True:
  assert buf[p:p+6]==b'070701';f=[int(buf[p+6+i*8:p+14+i*8],16) for i in range(13)]
  name=buf[p+110:p+110+f[11]];assert name[-1:]==b'\0';name=name[:-1].decode();d=up(p+110+f[11],4);end=d+f[6];assert end<=len(buf)
  assert not any(buf[p+110+f[11]:d]) and not any(buf[end:up(end,4)])
  if name=='TRAILER!!!':assert not any(buf[up(end,4):]);return result
  assert name not in result;result[name]=dict(mode=f[1],uid=f[2],gid=f[3],data=buf[d:end]);p=up(end,4)
img=(A/'candidate/UNARMED.img').read_bytes();raw=(A/'candidate/UNARMED.p10.raw').read_bytes();payload=(A/'original-recovery.payload').read_bytes()
assert len(img)==10317824 and sha(img)=='94e6747bc5998d7e5cf58a33280d362bb0dd97c14941c7fae6625117cc53ef91'
assert len(raw)==16740352 and sha(raw)=='e3df64342477816bc9aa2c8bb44cb61adf7a0f910d2d016c339c3250ff8457e3' and raw==img+bytes(len(raw)-len(img))
assert len(payload)==16740352 and sha(payload)=='902b2f06a01cca574b4aa374e67c4e7f8f0ed53f6e6a55017b6d96351f0f1f20'
ks=struct.unpack_from('<I',img,8)[0];rs=struct.unpack_from('<I',img,16)[0];ro=2048+up(ks,2048);k=img[2048:2048+ks];rd=img[ro:ro+rs]
assert img[576:596]==hashlib.sha1(k+struct.pack('<I',ks)+rd+struct.pack('<II',rs,0)).digest()
z=zlib.decompressobj(31);core=archive(z.decompress(rd[512:]));used=len(rd)-512-len(z.unused_data);offset=up(used,4);helper=archive(rd[512+offset:]);assert list(helper)==['sbin/p10-restore']
assert helper['sbin/p10-restore']['data']==(A/'p10-restore').read_bytes();assert helper['sbin/p10-restore']['mode']==0o100700
assert core['rescue.manifest']['data']==(A/'unarmed.manifest').read_bytes();assert struct.unpack_from('<I',core['rescue.manifest']['data'],12)[0]==0
assert sha((A/'original-stock.manifest').read_bytes())=='605cdec038dafe3dddabfe92b8bd6cd189734f740230dfc362d02a43421e4e47'
for entry,file in [('sepolicy','restore-sepolicy'),('file_contexts.bin','file_contexts.bin'),('sbin/os-rescue','os-rescue'),('system/bin/sh','rescue-proxy'),('sbin/rescue-proxy','rescue-proxy')]:assert core[entry]['data']==(A/file).read_bytes()
# Independently compare original stock kernel, init, adbd without inspecting private inputs.
sks=struct.unpack_from('<I',payload,8)[0];srs=struct.unpack_from('<I',payload,16)[0];sro=2048+up(sks,2048)
assert k==payload[2048:2048+sks];o=archive(zlib.decompress(payload[sro+512:sro+srs],31))
for entry in ['init','sbin/adbd']:assert core[entry]==o[entry]
# Check generated hashes against the actual normalized immutable components.
h=bytearray(img[:2048]);h[16:20]=bytes(4);h[576:608]=bytes(32);w=bytearray(rd[:512]);w[4:8]=bytes(4)
text=(S/'source/core_binding.h').read_text()
for key,data in [('core_header_sha',h),('core_wrapper_sha',w),('core_kernel_sha',k),('core_gzip_sha',rd[512:512+offset])]:
 m=re.search(key+r'\[32\]=\{([^}]+)\}',text);assert m;pin=bytes(int(x,16) for x in m[1].split(','));assert pin==hashlib.sha256(data).digest()
manifest=core['rescue.manifest']['data'];payload_map=up(16740352,4096)
result=dict(passed=True,image_sha256=sha(img),image_bytes=len(img),full_p10_sha256=sha(raw),payload_sha256=sha(payload),helper_sha256=sha(helper['sbin/p10-restore']['data']),policy_sha256=sha(core['sepolicy']['data']),contexts_sha256=sha(core['file_contexts.bin']['data']),kernel_sha256=sha(k),manifest_sha256=sha(manifest),manifest_records=0,ramdisk_bytes=rs-512,reservation_headroom=0x400000-(rs-512),core_archive_names=sorted(core),helper_archive_names=sorted(helper),helper_payload_prior_scratch_allocations=2*payload_map+1048576,successful_core_p10_read_bytes=20*16740352,pre_hello_system_boot_read_bytes=2*(3753902080+16740352),minimum_pre_hello_read_plus_hash_bytes_per_second_for_15s=2*(3753902080+16740352)/15,physical_validation=False)
(R/'evidence/independent-artifact-audit.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps({k:v for k,v in result.items() if not k.endswith('_names')},indent=2))
