#!/usr/bin/env python3
"""Change only the matching ELF32 DT_NEEDED string, retaining all code bytes."""
import pathlib,struct,hashlib,json,shutil
r=pathlib.Path(__file__).resolve().parents[1]
src=r.parent/'2026-11-06-asus-android17-connectivity/staged/deferred-bluetooth/blobs/lib'
dst=r/'staged/device/asus/p00a/radio/bluetooth';dst.mkdir(exist_ok=True)
p=src/'libbluetooth_mtk.so';data=bytearray(p.read_bytes());assert data[:6]==b'\x7fELF\x01\x01'
# Parse section headers and the SHT_DYNAMIC-linked string table.
shoff=struct.unpack_from('<I',data,32)[0];entsize,num=struct.unpack_from('<HH',data,46)
sections=[struct.unpack_from('<10I',data,shoff+i*entsize) for i in range(num)]
changed=[]
for sec in sections:
 if sec[1]!=6:continue
 strings=sections[sec[6]]
 for off in range(sec[4],sec[4]+sec[5],8):
  tag,value=struct.unpack_from('<II',data,off)
  if tag!=1:continue
  start=strings[4]+value;end=data.index(0,start)
  if data[start:end]==b'libnvram.so':
   assert end-start==len(b'libbtcal.so');data[start:end]=b'libbtcal.so';changed.append([start,end])
assert len(changed)==1
for old,new in [(b'service.nvram_init',b'vendor.p00a.btcal'),
                (b'persist.mtk.wcn.combo.chipid',b'vendor.p00a.chipid')]:
 needle=old+b'\0';assert data.count(needle)==1
 start=data.index(needle);end=start+len(needle)
 assert any(sec[1]==1 and not sec[2]&4 and sec[4]<=start and end<=sec[4]+sec[5] for sec in sections)
 data[start:end]=new+bytes(len(needle)-len(new));changed.append([start,end])
(dst/p.name).write_bytes(data)
shutil.copyfile(src/'libbt-vendor.so',dst/'libbt-vendor.so')
(r/'evidence/bt-record-abi.json').write_text(json.dumps({
 'library_sha256':hashlib.sha256(p.read_bytes()).hexdigest(),
 'patched_sha256':hashlib.sha256(data).hexdigest(),'changed_byte_range':changed,
 'calls':{'read':'0x15d4..0x1618: LID=1, read=1, record_size=64, count=1; 12-byte descriptor',
 'write':'0x32dc..0x3386: LID=1, read=0; attempts 6-byte BDADDR write; provider returns EOPNOTSUPP'},
 'fallback':'0x1640..0x16a0: failed read branches to default record; provider fail-stops required-read failure',
 'scope':'Only libbluetooth_mtk DT_NEEDED and two property strings change; code and global libnvram untouched',
 'abi_cross_reference':'https://github.com/andr3jx/MTK6577/blob/master/mediatek/source/external/nvram/libnvram/libnvram.h',
 'basis':'Captured ASUS binary is authoritative for LID, size, ABI and call semantics. Header used only to identify field names; no implementation copied.'},indent=2)+'\n')
