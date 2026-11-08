"""Lossless text extraction from exact Android v4 compiled contexts (no PCRE reuse).
Stock rules retained; only exact rescue paths supersede their original entries."""
import struct
def extract(b):
 pos=0
 def take(n):
  nonlocal pos
  r=b[pos:pos+n];assert len(r)==n;pos+=n;return r
 def u():return struct.unpack('<I',take(4))[0]
 assert u()==0xf97cff8a and u()==4
 take(u())
 for _ in range(u()):take(u()+1)
 out=[]
 modes={0:'',0o100000:'--',0o040000:'-d',0o060000:'-b',0o020000:'-c',0o120000:'-l',0o010000:'-p',0o140000:'-s'}
 for _ in range(u()):
  context=take(u());regex=take(u());mode=u();u();u();u();take(u());take(u())
  assert context[-1:]==regex[-1:]==b'\0'
  out.append((regex[:-1].decode(),modes[mode],context[:-1].decode()))
 assert pos==len(b)
 return out
def derive(b):
 overrides={r'/rescue\.manifest':'rootfs','/sbin/os-rescue':'os_rescue_exec','/system/bin/sh':'shell_exec',
 '/dev/socket/os_rescue':'os_rescue_socket','/dev/rescue-state(/.*)?':'os_rescue_state',
 '/dev/block/mmcblk0p9':'rescue_boot_device','/dev/block/mmcblk0p25':'rescue_system_device',
 '/dev/block/mmcblk0p26':'rescue_userdata_device','/dev/block/mmcblk0p10':'rescue_recovery_device','/dev/block/mmcblk0':'rescue_disk_device'}
 for name,t in [('boot','rescue_boot_device'),('system','rescue_system_device'),('recovery','rescue_recovery_device'),('userdata','rescue_userdata_device')]:
  overrides[r'/dev/block/platform/mtk-msdc\.0/11230000\.MSDC0/by-name/'+name]=t
 rows=[r for r in extract(b) if r[0] not in overrides]
 rows.extend((n,'','u:object_r:'+t+':s0') for n,t in overrides.items())
 return ''.join(' '.join(x for x in r if x)+'\n' for r in rows).encode()
