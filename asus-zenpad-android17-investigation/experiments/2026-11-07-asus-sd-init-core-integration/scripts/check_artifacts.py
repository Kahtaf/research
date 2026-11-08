from pathlib import Path
import sys,subprocess,json,hashlib
R=Path(__file__).resolve().parents[1];sys.path.insert(0,str(R/'source'))
import bootformat as b
T=Path('/srv/android/asus-target-rescue/artifacts/tools-delivery')
rows=[]
def check(args,expected=True):
 p=subprocess.run(list(map(str,args)),capture_output=True,text=True,timeout=15)
 rows.append(dict(command=list(map(str,args)),returncode=p.returncode,stdout=p.stdout,stderr=p.stderr))
 assert (p.returncode==0)==expected,rows[-1]
 return p.stdout
policy=R/'artifacts/sepolicy'
def av(s,t,c,perms,ok=True):return check([R/'artifacts/policy_constraints',policy,('u:object_r:' if s=='rescue_sd_file' else 'u:r:')+s+':s0',('u:r:' if c in ('process','unix_stream_socket','fd','capability') else 'u:object_r:')+t+':s0',c,perms],ok)
for n in ('os-rescue','rescue-sd','rescue-sd-supervisor'):
 data=(R/'artifacts'/n).read_bytes();b.elf_static(data)
 check(['aarch64-linux-gnu-readelf','-h','-l',R/'artifacts'/n])
for s,t,c,p in [
 ('init','rescue_sd_supervisor_exec','file','open,read,execute,execute_no_trans'),
 ('init','shell','process','transition,siginh,rlimitinh'),
 ('shell','rescue_sd_exec','file','entrypoint,open,read,execute'),
 ('shell','init','process','sigchld'),('shell','init','fd','use'),
 ('init','init','process','setexec'),('init','init','capability','setuid,setgid,sys_admin,sys_boot'),
 ('init','rescue_sd_device','blk_file','open,read,write'),
 ('init','vfat','filesystem','relabelfrom'),
 ('init','rescue_sd_fs','filesystem','mount,relabelto'),
 ('init','rescue_sd_file','filesystem','relabelto'),
 ('rescue_sd_file','rescue_sd_fs','filesystem','associate'),
 ('shell','rescue_sd_file','dir','open,read,search,write,add_name'),
 ('shell','rescue_sd_file','file','open,read,write,create'),
 ('shell','rescue_sd_fs','filesystem','getattr'),
 ('shell','os_rescue','unix_stream_socket','connectto'),
 ('shell','os_rescue_socket','sock_file','write,getattr'),
 ('os_rescue','os_rescue_state','file','create,write'),
 ('os_rescue','rescue_userdata_device','blk_file','open,read,write,ioctl'),
 ('shell','rootfs','file','open,read,getattr'),
 ('shell','rootfs','filesystem','getattr'),
 ('shell','proc','file','open,read,getattr'),
 ('shell','shell','file','open,read,getattr'),
 ('init','init','file','open,write'),
 ('shell','sysfs','lnk_file','read,getattr')]:av(s,t,c,p)
for s in ('shell','adbd','os_rescue'):
 for t in ('rescue_recovery_device','rescue_disk_device'):
  av(s,t,'blk_file','write',False)
for s in ('shell','os_rescue'):av(s,'rescue_sd_device','blk_file','write',False)
# Actual compiled file-context lookup with stock Android libselinux/PCRE.
for path,mode,label in [('/sbin/rescue-sd','100755','rescue_sd_exec'),('/sbin/rescue-sd-supervisor','100700','rescue_sd_supervisor_exec'),('/sbin/os-rescue','100700','os_rescue_exec'),('/dev/rescue-state/ready','100400','os_rescue_state'),('/dev/socket/os_rescue','140600','os_rescue_socket'),('/dev/block/mmcblk1p1','60600','rescue_sd_device'),('/mnt','40755','rootfs'),('/mnt/rescue-sd','40755','rootfs'),('/rescue.sd.arm','100444','rootfs'),('/rescue.manifest','100444','rootfs')]:
 out=check([T/'context_lookup',R/'source/file_contexts',path,mode]);assert out.strip()=='u:object_r:'+label+':s0',out
(R/'evidence/artifact-checks.json').write_text(json.dumps(rows,indent=2)+'\n')
print('Actual static ELFs, constrained policy decisions and compiled labels pass')
