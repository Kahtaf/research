from pathlib import Path
import sys,gzip,json,hashlib
R=Path(__file__).resolve().parents[1];sys.path.insert(0,str(R/'source'))
import bootformat as b

def common():
 e={n:(0o40755,0,0,b'') for n in ['dev','proc','sys','sbin','tmp','mnt','mnt/rescue-sd','system','data']}
 for n in ['init','property_contexts','service_contexts','seapp_contexts']:
  e[n]=(0o100750 if n=='init' else 0o100644,0,0,(R/'inputs'/n).read_bytes())
 for n,mode in [('os-rescue',0o100700),('rescue-sd',0o100755),('rescue-sd-supervisor',0o100700)]:e['sbin/'+n]=(mode,0,0,(R/'artifacts'/n).read_bytes())
 for n in ['sepolicy','file_contexts.bin']:e[n]=(0o100644,0,0,(R/'artifacts'/n).read_bytes())
 for dest,src in [('init.rc','init.common.rc'),('default.prop','default.prop'),('ueventd.rc','ueventd.rc')]:e[dest]=(0o100644,0,0,(R/'source'/src).read_bytes())
 e['sbin/ueventd']=(0o120777,0,0,b'../init')
 return e
if __name__=='__main__':
 e=common();cp=b.make_cpio(e);assert b.parse_cpio(cp)==e
 gz=bytearray(gzip.compress(cp,compresslevel=9,mtime=0));gz[9]=255
 (R/'artifacts/common-rootfs.cpio.gz').write_bytes(gz)
 assert b'start rescue-sd-offline' not in e['init.rc'][3]
 assert not any(n in e for n in ['system/bin/sh','sbin/adbd','sbin/p10-restore','rescue.manifest','rescue.sd.arm'])
 (R/'evidence/common-entries.json').write_text(json.dumps({n:dict(mode=oct(m),uid=u,gid=g,bytes=len(d),sha256=b.sha(d)) for n,(m,u,g,d) in e.items()},indent=2)+'\n')
 print('Built nonoperational common rootfs; no manifest/arm or automatic client start')
