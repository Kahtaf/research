"""Laptop-only verifier; no network, device, image writes, or full SYSTEM/data reads.
Reconstructs padded candidate bytes only in memory. Public original recovery is
read from the existing immutable restorer delivery, not copied into this spike.
"""
from pathlib import Path
import hashlib,json,struct,zlib,re,sys
R=Path(__file__).resolve().parents[1];W=R.parent;A=R/'artifacts';C=A/'candidate'
sha=lambda x:hashlib.sha256(x).hexdigest()
def up(n,a):return (n+a-1)//a*a
def archive(data):
 p=0;out={}
 while True:
  assert data[p:p+6]==b'070701';v=[int(data[p+6+8*i:p+14+8*i],16) for i in range(13)]
  name=data[p+110:p+110+v[11]];assert name[-1:]==b'\0';name=name[:-1].decode();start=up(p+110+v[11],4);end=start+v[6]
  assert end<=len(data) and not any(data[p+110+v[11]:start]) and not any(data[end:up(end,4)])
  p=up(end,4)
  if name=='TRAILER!!!':assert not any(data[p:]);return out
  assert name not in out and not name.startswith('/') and '..' not in name.split('/')
  out[name]=(v[1],v[2],v[3],data[start:end])
def image_parts(data,canonical=True):
 assert data[:8]==b'ANDROID!';ks,ka,rs,ra,ss,sa,tags,page=struct.unpack_from('<8I',data,8)
 assert page==2048 and ss==0;ro=page+up(ks,page);k=data[page:page+ks];r=data[ro:ro+rs]
 assert data[576:608]==hashlib.sha1(k+struct.pack('<I',ks)+r+struct.pack('<II',rs,0)).digest()+bytes(12)
 for x,n in [(k,b'KERNEL'),(r,b'RECOVERY')]:assert x[:4]==bytes.fromhex('88168858') and struct.unpack_from('<I',x,4)[0]==len(x)-512 and x[8:40].split(b'\0')[0]==n
 if canonical:assert not any(data[page+ks:ro]) and not any(data[ro+rs:])
 return k,r
pins=json.loads((R/'inputs/original-local-pins.json').read_text())
for rel,pin in pins.items():assert sha((W/rel).read_bytes())==pin,rel
original= W/'2026-11-06-asus-ram-original-recovery-restorer'
img=(C/'UNAPPROVED-STOCK-ONLY.img').read_bytes();full=img+bytes(16740352-len(img));k,rd=image_parts(img)
c=json.loads((C/'session-contract.UNAPPROVED.json').read_text())
assert c['manifest_records']==2 and c['mode']=='STOCK-ONLY/UNAPPROVED'
assert all(c[n] is False for n in ['armed','execute_approved','timing_qualified','physical_GO','physical_validation'])
assert sha(img)==c['image_sha256'] and sha(full)==c['p10_full_sha256']
z=zlib.decompressobj(31);core=archive(z.decompress(rd[512:]));offset=up(len(rd)-512-len(z.unused_data),4);extra=archive(rd[512+offset:])
assert len(rd)-512<=4194304 and 4194304-(len(rd)-512)==c['reservation_headroom']
assert set(extra)=={'sbin/p10-restore'} and extra['sbin/p10-restore']==(0o100700,0,0,(A/'p10-restore').read_bytes())
assert rd[512:512+offset]==(A/'core.cpio.gz').read_bytes() and rd[512+offset:]==(C/'helper.cpio').read_bytes()
m=core['rescue.manifest'][3]
assert m==(A/'original-stock.manifest').read_bytes() and len(m)==115288 and struct.unpack_from('<I',m,12)[0]==2
assert sha(m)=='605cdec038dafe3dddabfe92b8bd6cd189734f740230dfc362d02a43421e4e47'
commission=W/'2026-11-06-asus-stock-rescue-commissioning-artifact/artifacts/stock-pair-candidate/UNTESTED-STOCK-ONLY-commissioning.img'
_,cr=image_parts(commission.read_bytes());assert archive(zlib.decompress(cr[512:],31))['rescue.manifest'][3]==m
payload=(original/'artifacts/original-recovery.payload').read_bytes();assert len(payload)==16740352 and sha(payload)==c['payload_sha256']
sk,sr=image_parts(payload,canonical=False);stock=archive(zlib.decompress(sr[512:],31));assert k==sk
for n in ['init','sbin/adbd','property_contexts','seapp_contexts','service_contexts']:assert core[n]==stock[n]
for n,a in [('sepolicy','restore-sepolicy'),('file_contexts.bin','file_contexts.bin'),('sbin/os-rescue','os-rescue'),('sbin/rescue-proxy','rescue-proxy'),('system/bin/sh','rescue-proxy')]:assert core[n][3]==(A/a).read_bytes()
h=bytearray(img[:2048]);h[16:20]=bytes(4);h[576:608]=bytes(32);wrapper=bytearray(rd[:512]);wrapper[4:8]=bytes(4)
text=(R/'source/core_binding.h').read_text()
for name,data in [('core_header_sha',h),('core_wrapper_sha',wrapper),('core_kernel_sha',k),('core_gzip_sha',rd[512:512+offset])]:
 found=re.search(name+r'\[32\]=\{([^}]+)\}',text);assert found
 assert bytes(int(x,16) for x in found[1].split(','))==hashlib.sha256(data).digest()
local_artifacts=0
for rel,item in json.loads((R/'ARTIFACTS.json').read_text()).items():
 p=R/rel
 if p.exists():assert p.stat().st_size==item['bytes'] and sha(p.read_bytes())==item['sha256'];local_artifacts+=1
sourcepins=json.loads((R/'SOURCE_PINS.json').read_text())
for rel,pin in sourcepins.items():assert sha((R/rel).read_bytes())==pin,rel
sys.path.insert(0,str(R/'source'));import host
assert sha((R/'source/host.py').read_bytes())=='2d6acd11f5b46585bec820188463e4ecb863ec19a6f106a83320f14c24c479d9'
assert host.ARMED is False and host.TIMING_QUALIFIED is False
assert host.PRIOR_SHA==sha(full) and host.HELPER_SHA==sha(extra['sbin/p10-restore'][3])
try:host.restore(None,None);raise AssertionError('public host accepted')
except RuntimeError as e:assert 'Unarmed' in str(e)
for local,rel in [('parent-contract-acceptance.json','2026-11-06-asus-stock-userdata-recovery/evidence/parent-contract-acceptance.json'),('parent-preservation-acceptance.json','2026-11-06-asus-factory-state-preservation/evidence/parent-preservation-acceptance.json')]:assert (R/'inputs'/local).read_bytes()==(W/rel).read_bytes()
result=dict(passed=True,manifest_records=2,image_sha256=sha(img),full_p10_reconstructed_in_memory_sha256=sha(full),stock_manifest_matches_prior_commissioning=True,stock_kernel_init_authadbd_equal=True,source_pin_count=len(sourcepins),local_artifact_pin_count=local_artifacts,old_input_count=len(pins),old_inputs_unchanged=True,old_zero_record_image_sha256=pins['2026-11-06-asus-ram-original-recovery-restorer/artifacts/candidate/UNARMED.img'],old_full_p10_sha256=pins['2026-11-06-asus-ram-original-recovery-restorer/artifacts/candidate/UNARMED.p10.raw'],public_host_refused=True,timing_qualified=False,full_padded_p10_or_SYSTEM_data_written_locally=False,device_operations=0)
(R/'evidence/compact-delivery-verification.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result,indent=2))
