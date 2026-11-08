from pathlib import Path
import sys,subprocess,json,struct
R=Path(__file__).resolve().parents[1];sys.path.insert(0,str(R/'source'))
import bootformat as b
T=Path('/srv/android/asus-target-rescue/artifacts/tools-delivery');rows=[]
def check(cmd,ok=True):
 p=subprocess.run(list(map(str,cmd)),capture_output=True,text=True,timeout=15);rows.append(dict(command=list(map(str,cmd)),returncode=p.returncode,stdout=p.stdout,stderr=p.stderr));(R/'evidence/artifact-checks.json').write_text(json.dumps(rows,indent=2)+'\n')
 assert (p.returncode==0)==ok,rows[-1];return p.stdout
def av(s,t,c,perms,ok=True):
 obj=c not in ('process','fd','unix_stream_socket','capability')
 return check([R/'artifacts/policy_constraints',R/'artifacts/sepolicy','u:r:'+s+':s0',('u:object_r:' if obj else 'u:r:')+t+':s0',c,perms],ok)
for n in ['os-rescue','rescue-sd','rescue-sd-supervisor','p10-restore']:
 data=(R/'artifacts'/n).read_bytes();b.elf_static(data);assert struct.unpack_from('<H',data,16)[0]==2;check(['aarch64-linux-gnu-readelf','-h','-l',R/'artifacts'/n])
for s,t,c,p in [('init','init','capability','dac_override,sys_admin,sys_boot'),('init','stock_restore_exec','file','open,read,execute'),('p10_restore','stock_restore_exec','file','entrypoint,open,read,execute'),('init','p10_restore','process','transition,siginh,rlimitinh'),('p10_restore','init','fd','use'),('p10_restore','init','unix_stream_socket','getattr,getopt'),('p10_restore','rescue_sd_file','file','open,read,getattr'),('p10_restore','rescue_sd_fs','filesystem','getattr'),('init','rescue_sd_file','file','open,read,create,write'),('init','rescue_sd_fs','filesystem','unmount'),('init','os_rescue_control_socket','sock_file','write,getattr,create'),('init','os_rescue','unix_stream_socket','connectto'),('init','os_rescue','fd','use'),('os_rescue','init','unix_stream_socket','read,write'),('p10_restore','rescue_recovery_device','blk_file','open,read,write,ioctl'),('shell','rescue_sd_file','file','open,read,write,create')]:av(s,t,c,p)
for s in ['shell','adbd','os_rescue']:
 for t in ['rescue_recovery_device','rescue_disk_device']:av(s,t,'blk_file','write',False)
for t in ['rescue_boot_device','rescue_system_device','rescue_userdata_device','rescue_disk_device']:av('p10_restore',t,'blk_file','write',False)
av('os_rescue','stock_restore_exec','file','execute',False);av('shell','stock_restore_exec','file','execute',False);av('shell','os_rescue_control_socket','sock_file','write',False)
av('p10_restore','rescue_sd_file','file','write',False)
for path,mode,label in [('/sbin/p10-restore','100700','stock_restore_exec'),('/dev/socket/os_rescue_control','140600','os_rescue_control_socket'),('/rescue.original.manifest','100444','rootfs'),('/rescue.current.binding','100444','rootfs'),('/sbin/rescue-sd','100755','rescue_sd_exec'),('/sbin/rescue-sd-supervisor','100700','rescue_sd_supervisor_exec'),('/dev/socket/os_rescue','140600','os_rescue_socket')]:
 assert check([T/'context_lookup',R/'source/file_contexts',path,mode]).strip()=='u:object_r:'+label+':s0'
print('actual static ELF, constrained entry/source/lock/denial policy and compiled labels pass')
