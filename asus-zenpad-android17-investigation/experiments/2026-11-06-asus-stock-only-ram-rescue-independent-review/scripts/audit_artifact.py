"""Independent, read-only parser; only review evidence is written."""
from pathlib import Path
import hashlib, json, struct, zlib, re, sys
R=Path(__file__).resolve().parents[1]; W=R.parent
N=R/'snapshot'; O=W/'2026-11-06-asus-ram-original-recovery-restorer'
sha=lambda b:hashlib.sha256(b).hexdigest()
def align(x,a):return (x+a-1)//a*a
def image(b,canonical=True):
    assert b[:8]==b'ANDROID!'
    ks,ka,rs,ra,ss,sa,tags,page=struct.unpack_from('<8I',b,8)
    assert page==2048 and ss==0
    ro=page+align(ks,page); end=ro+align(rs,page)
    assert end<=len(b)
    k=b[page:page+ks]; r=b[ro:ro+rs]
    assert b[576:608]==hashlib.sha1(k+struct.pack('<I',ks)+r+struct.pack('<II',rs,0)).digest()+bytes(12)
    for item,name in [(k,b'KERNEL'),(r,b'RECOVERY')]:
        assert item[:4]==bytes.fromhex('88168858') and struct.unpack_from('<I',item,4)[0]==len(item)-512
        assert item[8:40].split(b'\0')[0]==name
    if canonical:assert not any(b[page+ks:ro]) and not any(b[ro+rs:])
    return k,r,dict(kernel_address=ka,ramdisk_address=ra,second_address=sa,tags_address=tags,page=page,end=end)
def cpio(b,canonical=True):
    p=0; entries={}; index=0
    while True:
        assert b[p:p+6]==b'070701'
        f=[int(b[p+6+8*i:p+14+8*i],16) for i in range(13)]
        ino,mode,uid,gid,nlink,mtime,size,maj,minor,rmaj,rminor,ns,crc=f
        assert 1<=ns<=4096
        name=b[p+110:p+110+ns]; assert len(name)==ns and name[-1:]==b'\0'
        name=name[:-1].decode(); start=align(p+110+ns,4); end=start+size
        assert end<=len(b)
        if canonical:
            index+=1
            assert ino==index and nlink==(2 if mode&0o170000==0o040000 else 1) and mtime==maj==minor==rmaj==rminor==crc==0
            assert not any(b[p+110+ns:start]) and not any(b[end:align(end,4)])
        p=align(end,4)
        if name=='TRAILER!!!':
            assert size==0
            if canonical:assert mode==uid==gid==0 and align(p,512)==len(b)
            assert not any(b[p:]); return entries
        assert name not in entries and not name.startswith('/') and '..' not in name.split('/')
        entries[name]=(mode,uid,gid,b[start:end])
def members(rd):
    z=zlib.decompressobj(31); raw=z.decompress(rd[512:],64*1024*1024)
    assert z.eof and not z.unconsumed_tail
    used=len(rd)-512-len(z.unused_data); split=align(used,4)
    assert not any(rd[512+used:512+split])
    return cpio(raw),rd[512:512+split],rd[512+split:]
img=(N/'artifacts/candidate/UNAPPROVED-STOCK-ONLY.img').read_bytes()
assert len(img)==10412032 and sha(img)=='5a61d3d65a7ba6b29745a965d9911ab4483c951a0327339839a0541bcb9ab30f'
full=img+bytes(16740352-len(img))
assert sha(full)=='3f99c785cca60bf56c2505711e2d26b72623daf28180515d44c5ba2abf03a44a'
k,rd,layout=image(img); core,gz,cap=members(rd); helper=cpio(cap)
assert len(img)==layout['end'] and len(rd)-512<=4194304
assert helper=={'sbin/p10-restore':(0o100700,0,0,(N/'artifacts/p10-restore').read_bytes())}
assert sha(helper['sbin/p10-restore'][3])=='c5df268a9f0bdc31e01140a5378d404f9cb7b091b8ec50e5c2be992434089859'
assert gz==(N/'artifacts/core.cpio.gz').read_bytes() and cap==(N/'artifacts/candidate/helper.cpio').read_bytes()
ok,ord,oldlayout=image((O/'artifacts/candidate/UNARMED.img').read_bytes())
oldcore,oldgz,oldcap=members(ord)
changed=sorted(n for n in core.keys()|oldcore.keys() if core.get(n)!=oldcore.get(n))
assert changed==['rescue.manifest'] and k==ok and layout|{'end':0}==oldlayout|{'end':0}
m=core['rescue.manifest'][3]
assert sha(m)=='605cdec038dafe3dddabfe92b8bd6cd189734f740230dfc362d02a43421e4e47'
assert m==(O/'artifacts/original-stock.manifest').read_bytes()==(N/'artifacts/original-stock.manifest').read_bytes()
commission=W/'2026-11-06-asus-stock-rescue-commissioning-artifact/artifacts/stock-pair-candidate/UNTESTED-STOCK-ONLY-commissioning.img'
_,commission_rd,_=image(commission.read_bytes())
assert cpio(zlib.decompress(commission_rd[512:],31))['rescue.manifest'][3]==m
assert m[:16]==b'ASUSR002\x02\0\0\0\x02\0\0\0'; off=112; rows=[]
for i,part,size,digest in [(0,25,3753902080,'4597a7b5a9f30f9e851f1ae71b54a2db1845465e36a1a55b70ae26e171d5cd49'),(1,9,16740352,'7bb68511b1ade34d24c3e932da7260e6753fa87270bd8249a7218755a5df3316')]:
    role,p,n=struct.unpack_from('<IIQ',m,off); count=struct.unpack_from('<I',m,off+48)[0]
    assert (role,p,n)==(i,part,size) and m[off+16:off+48].hex()==digest and count==(size+1048575)//1048576
    rows.append(dict(role=role,partition=p,bytes=n,sha256=digest,chunks=count));off+=52+32*count
assert off==len(m)==115288
payload=(O/'artifacts/original-recovery.payload').read_bytes()
assert len(payload)==16740352 and sha(payload)=='902b2f06a01cca574b4aa374e67c4e7f8f0ed53f6e6a55017b6d96351f0f1f20'
sk,srd,_=image(payload,False); stock=cpio(zlib.decompress(srd[512:],31),False)
assert k==sk
for n in ['init','sbin/adbd','property_contexts','seapp_contexts','service_contexts']:assert core[n]==stock[n]
for name,artifact in [('sepolicy','restore-sepolicy'),('file_contexts.bin','file_contexts.bin'),('sbin/os-rescue','os-rescue'),('sbin/rescue-proxy','rescue-proxy'),('system/bin/sh','rescue-proxy')]:
    assert core[name][3]==(N/'artifacts'/artifact).read_bytes()==(O/'artifacts'/artifact).read_bytes()
h=bytearray(img[:2048]);h[16:20]=bytes(4);h[576:608]=bytes(32)
w=bytearray(rd[:512]);w[4:8]=bytes(4);txt=(N/'source/core_binding.h').read_text()
for name,data in [('core_header_sha',h),('core_wrapper_sha',w),('core_kernel_sha',k),('core_gzip_sha',gz)]:
    assert bytes(int(x,16) for x in re.search(name+r'\[32\]=\{([^}]+)\}',txt)[1].split(','))==hashlib.sha256(data).digest()
assert int(re.search(r'CORE_GZIP_BYTES (\d+)U',txt)[1])==len(gz)
assert int(re.search(r'CORE_KERNEL_BYTES (\d+)U',txt)[1])==len(k)
source_delta={p.name:dict(before=sha((O/'source'/p.name).read_bytes()),after=sha(p.read_bytes())) for p in (N/'source').iterdir() if p.is_file()}
assert sorted(n for n,v in source_delta.items() if v['before']!=v['after'])==['core_binding.h','generated_host_binding.py','host.py']
assert (N/'source/host.py').read_bytes()==(W/'2026-11-06-asus-ram-restorer-host-contract-fix/source/host.py').read_bytes()
sys.path.insert(0,str(N/'source'));import host
assert host.PRIOR_SHA==sha(full) and host.HELPER_SHA==sha(helper['sbin/p10-restore'][3]) and not host.ARMED and not host.TIMING_QUALIFIED
contract=json.loads((N/'artifacts/candidate/session-contract.UNAPPROVED.json').read_text())
handoff=json.loads((N/'HANDOFF.json').read_text())
assert handoff['report_sha256']==sha((N/'REPORT.md').read_bytes())
assert handoff['manifest_records']==contract['manifest_records']==2
for obj in [handoff,contract]:
    assert all(obj[n] is False for n in ['armed','timing_qualified','execute_approved','physical_GO'])
assert contract['image_sha256']==sha(img) and contract['p10_full_sha256']==sha(full)
for pinfile in ['SOURCE_PINS.json','DELIVERY_PINS.json']:
    for rel,pin in json.loads((N/pinfile).read_text()).items():
        if isinstance(pin,dict):pin=pin['sha256']
        assert sha((N/rel).read_bytes())==pin,(pinfile,rel)
for rel,item in json.loads((N/'ARTIFACTS.json').read_text()).items():
    p=N/rel
    if p.is_file():assert len(p.read_bytes())==item['bytes'] and sha(p.read_bytes())==item['sha256']
pins=json.loads((N/'inputs/original-local-pins.json').read_text())
for rel,pin in pins.items():assert sha((W/rel).read_bytes())==pin,rel
for local,spike in [('parent-preservation-acceptance.json','2026-11-06-asus-factory-state-preservation'),('parent-contract-acceptance.json','2026-11-06-asus-stock-userdata-recovery')]:
    assert (N/'inputs'/local).read_bytes()==(W/spike/'evidence'/local).read_bytes()
for name in ['p10-restore','os-rescue']:
    b=(N/'artifacts'/name).read_bytes();assert b[:6]==b'\x7fELF\x02\x01' and struct.unpack_from('<H',b,18)[0]==183
    start=struct.unpack_from('<Q',b,32)[0];size,count=struct.unpack_from('<HH',b,54)
    assert all(struct.unpack_from('<I',b,start+i*size)[0] not in (2,3) for i in range(count))
result=dict(passed=True,independent_parser=True,external_image_sha256=sha(img),external_full_p10_sha256=sha(full),helper_sha256=host.HELPER_SHA,manifest_sha256=sha(m),original_roles=rows,source_delta=source_delta,core_changed_entries=changed,stock_kernel_init_adbd_equal=True,canonical_helper_archive=True,immutable_core_binding=True,source_and_delivery_inventory_valid=True,old_inputs_unchanged=len(pins),layout=layout,ramdisk_bytes=len(rd)-512,reservation_headroom=4194304-len(rd)+512,p10_headroom=16740352-len(img),full_p10_only_in_memory=True,physical_proof=False)
(R/'evidence/artifact-audit.json').write_text(json.dumps(result,indent=2)+'\n')
print(json.dumps({k:v for k,v in result.items() if k!='source_delta'},indent=2))
