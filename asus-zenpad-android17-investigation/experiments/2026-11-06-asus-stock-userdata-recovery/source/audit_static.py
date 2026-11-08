"""Reproduce bounded exact-ELF disassembly and cross-file assertions."""
from pathlib import Path
import json,struct,hashlib
from elfaudit import ELF
S=Path(__file__).resolve().parents[1]
e=ELF(S/'inputs/recovery__sbin_recovery')
windows={'oem-wipe':(0x40d7ec,0x40d990),'erase-volume':(0x404088,0x4044bc),'format':(0x407cb8,0x408244),'file-size':(0x416618,0x41677c),'wipe-block':(0x41b1d0,0x41b370),'formatter-core':(0x413ba4,0x414300),'formatter-wrapper':(0x414824,0x414974),'make-device':(0x40c460,0x40c4a8),'device-methods':(0x401914,0x401a08),'menu-to-reset':(0x40d270,0x40d390),'wipe-menu-wrapper':(0x404b54,0x404b58),'volumes':(0x407660,0x407824),'mt-volume-additions':(0x40c5ac,0x40cc0c),'storage-layout-check':(0x43b460,0x43b638),'oem-bookkeeping':(0x40db7c,0x40e048),'emmc-bcb-write':(0x40e1a0,0x40e2e8),'finish-recovery':(0x403e9c,0x404088),'sideload-entry':(0x400980,0x400d50)}
for name,(a,b) in windows.items():(S/f'evidence/{name}.txt').write_text(e.listing(a,b))
def ptr(a):return struct.unpack('<Q',e.bytes(a,a+8))[0]
vt=ptr(0x562890)+16
hooks=[ptr(vt+k) for k in [0x48,0x50]]
assert hooks==[0x401a00]*2 and e.bytes(0x401a00,0x401a08).hex()=='e0030032c0035fd6'
menus=[e.string(ptr(0x563020+8*k)) for k in range(11)];assert menus[4]=='Wipe data/factory reset'
confirm=[e.string(ptr(0x55de00+8*k)) for k in range(11)];assert confirm[7]==' Yes -- delete all user data'
fs=(S/'inputs/recovery__etc_recovery.fstab').read_text();boot=(S/'inputs/boot__fstab.mt8163').read_text();assert fs==boot
entries=[l.split() for l in fs.splitlines() if l and not l.startswith('#')]
data=next(x for x in entries if x[1]=='/data');assert 'forceencrypt=/dev/block/platform/mtk-msdc.0/11230000.MSDC0/by-name/metadata' in data[4]
assert not any(x[1]=='/nvdata' for x in entries)
assert next(x for x in entries if x[1]=='/misc')[0].endswith('/para')
props=(S/'inputs/recovery__default.prop').read_text();assert '\nro.debuggable=0\n'in props and '\nro.adb.secure=1\n'in props
vold=ELF(S/'inputs/system__bin_vold');assert vold.string(0x85f94)=='0' and vold.string(0x85f96)=='1'
assert vold.string(0x8cf31)=='--wipe_data\n--reason=cryptfs_enable_internal\n'
r={'recovery_ELF_sha256':hashlib.sha256(e.data).hexdigest(),'device_vtable':hex(vt),'PreWipeData_PostWipeData':[hex(x)for x in hooks],'hooks':'mov w0,1; ret','menu':menus,'confirmation':confirm,'fstab_equal':True,'data_entry':data,'nvdata_present':False,'metadata_reset_size':33554432,'crypto_failure_property_default':'0','crypto_failure_reset_condition':'property equals 1; runtime value unproved','stock_UI_adbd_default':'disabled, ro.debuggable=0, ro.adb.secure=1','windows':{k:[hex(a),hex(b)]for k,(a,b)in windows.items()}}
(S/'evidence/static-checks.json').write_text(json.dumps(r,indent=2)+'\n');print(json.dumps({'static_assertions':'pass','disassembly_windows':len(windows)}))
