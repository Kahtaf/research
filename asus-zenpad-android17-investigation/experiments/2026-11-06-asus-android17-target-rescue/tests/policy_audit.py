from pathlib import Path
import subprocess,json,sys
R=Path(__file__).resolve().parents[1];tools=Path(sys.argv[1]);candidate=Path(sys.argv[2]);out=Path(sys.argv[3]);userdata=len(sys.argv)>4 and sys.argv[4]=='--userdata'
policy=candidate/'rescue-sepolicy';cases=[]
def check(src,dst,cl,perms,expected=True):
 cmd=[str(tools/'policy_constraints'),str(policy),src,dst,cl,perms];p=subprocess.run(cmd,capture_output=True,text=True);ok=p.returncode==(0 if expected else 1)
 cases.append(dict(command=cmd,returncode=p.returncode,expected_allowed=expected,passed=ok,stdout=p.stdout,stderr=p.stderr))
 if not ok:print('FAILED',cmd,p.stdout,p.stderr)
def sub(n):return 'u:r:'+n+':s0'
def obj(n):return 'u:object_r:'+n+':s0'
for src,dst,cl,perms in [
 ('init','os_rescue','process','transition,siginh,rlimitinh'),('os_rescue','init','fd','use'),
 ('init','os_rescue','unix_stream_socket','create,bind,getattr,setattr'),('os_rescue','os_rescue','unix_stream_socket','create,bind,listen,accept,read,write,getopt,setopt,shutdown'),
 ('shell','os_rescue','unix_stream_socket','connectto'),('os_rescue','shell','fd','use'),
 ('shell','adbd','unix_stream_socket','read,write,ioctl,getopt'),('shell','adbd','fd','use'),
 ('os_rescue','os_rescue','dir','search,open,read,getattr'),('os_rescue','os_rescue','file','open,read,getattr')]:
 check(sub(src),sub(dst),cl,perms)
for node in ['rescue_boot_device','rescue_system_device','rescue_recovery_device','rescue_disk_device']:
 check(sub('os_rescue'),obj(node),'blk_file','open,read,getattr,ioctl')
 check(sub('os_rescue'),obj(node),'blk_file','write',node in ['rescue_boot_device','rescue_system_device'])
 check(sub('ueventd'),obj(node),'blk_file','create,getattr,setattr')
 check(obj(node),obj('tmpfs'),'filesystem','associate')
check(sub('os_rescue'),obj('rescue_userdata_device'),'blk_file','open,read,write,getattr,ioctl',userdata)
for node in ['block_device','recovery_block_device','userdata_block_device','metadata_block_device','preloader_block_device','nvm_device','nvram_device','para_block_device','mmcblk0_block_device']:
 check(sub('os_rescue'),obj(node),'blk_file','write',False)
for cl,perms in [('tcp_socket','create'),('udp_socket','create'),('capability','sys_boot'),('capability','sys_admin'),('capability','dac_override')]:
 check(sub('os_rescue'),sub('os_rescue'),cl,perms,False)
check(sub('os_rescue'),sub('kernel'),'security','setenforce',False)
check(sub('os_rescue'),obj('shell_exec'),'file','execute',False)
check(sub('os_rescue'),obj('rootfs'),'filesystem','mount',False)
check(sub('os_rescue'),obj('os_rescue_exec'),'file','entrypoint,open,read,execute')
check(sub('init'),obj('os_rescue_exec'),'file','relabelto')
check(sub('init'),obj('shell_exec'),'file','relabelto')
check(sub('adbd'),obj('rootfs'),'file','execute_no_trans')
check(sub('os_rescue'),obj('os_rescue_state'),'file','create,open,read,write,getattr,rename,unlink')
check(sub('os_rescue'),obj('os_rescue_state'),'dir','search,open,read,write,add_name,remove_name')
check(sub('shell'),obj('os_rescue_socket'),'sock_file','write')
check(sub('shell'),obj('rescue_system_device'),'blk_file','write',False)
for target in ['device','block_device','socket_device','sysfs','proc','selinuxfs','tmpfs','rootfs']:
 check(sub('os_rescue'),obj(target),'dir','search,open,read,getattr')
for target in ['sysfs','proc','selinuxfs','rootfs']:
 check(sub('os_rescue'),obj(target),'file','open,read,getattr')
for src,dst,cl,want in [('init','os_rescue_exec','process','os_rescue'),('adbd','shell_exec','process','shell')]:
 p=subprocess.run([str(tools/'policy_query'),str(policy),sub(src),obj(dst),cl,'--transition'],capture_output=True,text=True);cases.append(dict(transition=[src,dst,cl],stdout=p.stdout,returncode=p.returncode,passed=p.returncode==0 and p.stdout.strip()==sub(want)))
lookups=[]
for path,mode,want in [
 ('/sbin/os-rescue','100700','os_rescue_exec'),('/system/bin/sh','100755','shell_exec'),('/sbin/adbd','100755','rootfs'),('/rescue.manifest','100444','rootfs'),
 ('/dev/socket/os_rescue','140600','os_rescue_socket'),('/dev/rescue-state/journal.new','100600','os_rescue_state'),
 ('/dev/block/mmcblk0p9','60600','rescue_boot_device'),('/dev/block/mmcblk0p10','60600','rescue_recovery_device'),('/dev/block/mmcblk0p25','60600','rescue_system_device'),('/dev/block/mmcblk0','60600','rescue_disk_device'),('/dev/block/mmcblk0p26','60600','rescue_userdata_device')]:
 cmd=[str(tools/'context_lookup'),str(candidate/'file_contexts.bin'),path,mode];p=subprocess.run(cmd,capture_output=True,text=True)
 lookups.append(dict(command=cmd,stdout=p.stdout,returncode=p.returncode,passed=p.returncode==0 and p.stdout.strip()==obj(want)))
for part,name,want in [(9,'boot','rescue_boot_device'),(10,'recovery','rescue_recovery_device'),(25,'system','rescue_system_device'),(26,'userdata','rescue_userdata_device')]:
 cmd=[str(tools/'context_lookup'),str(candidate/'file_contexts.bin'),'/dev/block/mmcblk0p'+str(part),'60600','/dev/block/platform/mtk-msdc.0/11230000.MSDC0/by-name/'+name]
 p=subprocess.run(cmd,capture_output=True,text=True);lookups.append(dict(command=cmd,stdout=p.stdout,returncode=p.returncode,passed=p.returncode==0 and p.stdout.strip()==obj(want)))
p=subprocess.run([str(tools/'policy_inspect'),str(candidate/'stock-sepolicy'),str(policy)]+(['--userdata'] if userdata else []),capture_output=True,text=True)
report=dict(passed=all(x['passed'] for x in cases+lookups) and p.returncode==0,constraints=cases,contexts=lookups,structural=dict(returncode=p.returncode,stdout=p.stdout,stderr=p.stderr))
out.write_text(json.dumps(report,indent=2)+'\n')
print(json.dumps(dict(passed=report['passed'],constraint_checks=len(cases),context_checks=len(lookups),structural_rc=p.returncode),indent=2))
sys.exit(0 if report['passed'] else 1)
