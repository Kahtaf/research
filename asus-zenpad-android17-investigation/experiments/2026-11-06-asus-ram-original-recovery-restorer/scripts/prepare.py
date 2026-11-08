"""Read-only public inputs; prepare immutable core and isolated build inputs."""
from pathlib import Path
import sys,json,hashlib,struct
R=Path(__file__).resolve().parents[1];W=R.parent;S=R/'source';A=R/'artifacts'
sys.path.insert(0,str(S));import bootformat as b
sha=lambda x:hashlib.sha256(x).hexdigest()
def const(name,data):return 'static const unsigned char '+name+'[32]={'+','.join('0x'+data.hex()[i:i+2] for i in range(0,64,2))+'};\n'
old=W/'2026-11-06-asus-stock-rescue-commissioning-artifact/artifacts/stock-pair-candidate/UNTESTED-STOCK-ONLY-commissioning.img'
x=old.read_bytes();assert sha(x)=='154853e37436d17c44d873e177f25efd605ecda4e69e8d2148dd840b60bee6c7'
h,k,r,t=b.parse_image(x);assert not t;e=b.parse_cpio(b.ungzip(r[512:])[0])
manifest=e['rescue.manifest'][3];assert len(manifest)==115288 and struct.unpack_from('<I',manifest,12)[0]==2
(S/'stock_binding.h').write_text(const('stock_manifest_sha',hashlib.sha256(manifest).digest()))
(A/'original-stock.manifest').write_bytes(manifest)
(A/'base-header').write_bytes(h);(A/'base-kernel').write_bytes(k);(A/'base-wrapper').write_bytes(r[:512])
for name in ['init','sbin/adbd','property_contexts','seapp_contexts','service_contexts','adb_keys','default.prop','ueventd.rc']:
 out=A/'core-inputs'/name;out.parent.mkdir(parents=True,exist_ok=True);out.write_bytes(e[name][3])
(A/'core-input-metadata.json').write_text(json.dumps({n:list(e[n][:3]) for n in e},indent=2)+'\n')
init=e['init.rc'][3].replace(b'restorecon /sbin/os-rescue ',b'restorecon /sbin/p10-restore /sbin/os-rescue ')
(A/'core-inputs/init.rc').write_bytes(init)
(A/'unarmed.manifest').write_bytes(manifest[:12]+bytes(4)+manifest[16:112])
(A/'base-policy').write_bytes(e['sepolicy'][3])
from file_contexts import extract
rows=extract(e['file_contexts.bin'][3]);assert sum(kind=='-b' and 'rescue_' in ctx for _,kind,ctx in rows)==9
text=''.join(' '.join(filter(None,row))+'\n' for row in rows)
text+='/sbin/p10-restore -- u:object_r:p10_restore_exec:s0\n'
(A/'file_contexts').write_text(text)
payload=[]
for name in ['initial','verify']:
 p=W/'2026-11-05-asus-boot-access-audit/artifacts/device-backup'/name/'recovery.bin'
 assert p.is_file() and not p.is_symlink();data=p.read_bytes();assert len(data)==b.PARTITION_SIZE and sha(data)==b.RECOVERY_SHA
 payload.append(data)
assert payload[0]==payload[1];(A/'original-recovery.payload').write_bytes(payload[0])
(R/'evidence/input-pins.json').write_text(json.dumps(dict(base_image_sha256=sha(x),stock_manifest_sha256=sha(manifest),payload_sha256=sha(payload[0]),payload_bytes=len(payload[0]),copies_equal=True,private_inputs=False),indent=2)+'\n')
