"""One offline OEM-layout check, not a retention/boot test or hardware model."""
from pathlib import Path
import hashlib,json,struct,zlib
R=Path(__file__).resolve().parents[1];W=R.parent
p=W/'2026-11-05-asus-boot-access-audit/artifacts/device-backup/initial/recovery.bin'
b=p.read_bytes(); assert hashlib.sha256(b).hexdigest()=='902b2f06a01cca574b4aa374e67c4e7f8f0ed53f6e6a55017b6d96351f0f1f20'
k=zlib.decompress(b[2560:],31);base=0xffffffc000080000
# Exact instructions retained from the shipped reader, not reference C.
pins={
 0xffffffc0006951d0:'012840b9', # sz_buffer +0x28
 0xffffffc0006951fc:'022c40b9', # off_linux +0x2c
 0xffffffc000695208:'023040b9', # off_console +0x30
 0xffffffc000697228:'21001091', # off_linux + 0x400
 0xffffffc0006972a0:'633e40b9', # sz_console +0x3c
 0xffffffc0006972b0:'603a40b9', # log_size +0x38
 0xffffffc0006972bc:'623640b9', # log_start +0x34
 0xffffffc0006972cc:'0200024b', # first write size = log_size-log_start
 0xffffffc000f41400:'0088a8d2', # physical base 0x44400000
 0xffffffc000f41428:'0201a0d2', # total size 0x80000
}
for addr,hexbytes in pins.items(): assert k[addr-base:addr-base+4]==bytes.fromhex(hexbytes)
assert k[0xffffffc000e38668-base:][:10]==b'last_kmsg\0'
size=0x80000;linux=0x200;console=linux+0x400;capacity=size-console
marker=b'ASUS-e9-retained-v1 01 paging_init returned; trace ready\n'
# A representative valid OTA fallback header. NOT a captured device header.
# log_start=0 makes the shipped two seq_write calls emit the append-only text.
checked=[]
for payload in (marker, b'x'*capacity):
 values=[0x43474244,0,0,0,0,0,0,0,0,0,size,linux,console,0,len(payload),capacity]
 raw=struct.pack('<16I',*values)+bytes(console-64)+payload+bytes(capacity-len(payload))
 h=struct.unpack_from('<16I',raw)
 assert len(raw)==h[10]==size and h[12]==h[11]+0x400
 assert h[15]==h[10]-h[12] and h[14]<=h[15] and h[13]<=h[14]
 observed=raw[h[12]+h[13]:h[12]+h[14]]+raw[h[12]:h[12]+h[13]]
 assert observed==payload
 checked.append({'text_bytes':len(payload),'reader_bytes':len(observed),'equal':True})
result={'status':'PASS','scope':'exact binary field instructions plus two offline reader-length boundaries; no hardware execution',
 'instruction_pins':{hex(a):v for a,v in pins.items()},'header_bytes':64,'RR_aligned_bytes':1024,'reservation_base':'0x44400000','reservation_bytes':size,
 'representative_fallback_console_offset':console,'representative_capacity':capacity,'cases':checked}
(R/'evidence/layout-check.json').write_text(json.dumps(result,indent=2)+'\n')
print(json.dumps(result,indent=2))
