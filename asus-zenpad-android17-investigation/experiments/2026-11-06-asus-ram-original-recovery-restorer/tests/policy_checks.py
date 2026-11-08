from pathlib import Path
import subprocess,json,sys,collections
R=Path(__file__).resolve().parents[1];A=R/'artifacts';T=Path('/srv/android/asus-target-rescue/artifacts/tools-delivery')
checks=[]
def run(cmd,expect=0,want=None):
 p=subprocess.run(list(map(str,cmd)),capture_output=True,text=True)
 ok=p.returncode==expect and (want is None or p.stdout.strip()==want)
 checks.append(dict(command=list(map(str,cmd)),returncode=p.returncode,stdout=p.stdout,stderr=p.stderr,passed=ok))
 assert ok,checks[-1]
def sub(t):return 'u:r:'+t+':s0'
def obj(t):return 'u:object_r:'+t+':s0'
def check(src,tgt,cl,perm,allowed):run([T/'policy_constraints',A/'restore-sepolicy',sub(src),tgt,cl,perm],0 if allowed else 1)
for node in ['rescue_boot_device','rescue_system_device','rescue_recovery_device','rescue_disk_device']:
 check('p10_restore',obj(node),'blk_file','open,read,getattr,ioctl',True)
 check('p10_restore',obj(node),'blk_file','write',node=='rescue_recovery_device')
for domain in ['os_rescue','shell','adbd']:
 check(domain,obj('rescue_recovery_device'),'blk_file','write',False)
for node in ['rescue_userdata_device','block_device','metadata_block_device','userdata_block_device','preloader_block_device','para_block_device','nvm_device','nvram_device']:
 for permission in ['read','write']:check('p10_restore',obj(node),'blk_file',permission,False)
for cl,permission in [('tcp_socket','create'),('udp_socket','create'),('capability','sys_boot'),('capability','sys_admin'),('capability','dac_override')]:check('p10_restore',sub('p10_restore'),cl,permission,False)
check('p10_restore',sub('kernel'),'security','setenforce',False)
check('p10_restore',obj('rootfs'),'filesystem','mount',False)
check('p10_restore',obj('shell_exec'),'file','execute',False)
check('p10_restore',obj('p10_restore_exec'),'file','write',False)
check('os_rescue',obj('p10_restore_exec'),'file','write',False)
check('shell',obj('p10_restore_exec'),'file','execute',False)
check('p10_restore',sub('os_rescue'),'fd','use',True)
check('p10_restore',sub('os_rescue'),'unix_stream_socket','accept,read,write,getopt,setopt,shutdown',True)
check('p10_restore',obj('p10_restore_exec'),'file','entrypoint,open,read,execute,getattr',True)
check('os_rescue',sub('p10_restore'),'process','transition,siginh,rlimitinh',True)
run([T/'policy_query',A/'restore-sepolicy',sub('os_rescue'),obj('p10_restore_exec'),'process','--transition'],want=sub('p10_restore'))
lookups=0
for part,alias,name in [(9,'boot','rescue_boot_device'),(10,'recovery','rescue_recovery_device'),(25,'system','rescue_system_device'),(26,'userdata','rescue_userdata_device')]:
 direct='/dev/block/mmcblk0p'+str(part);link='/dev/block/platform/mtk-msdc.0/11230000.MSDC0/by-name/'+alias
 for path in [direct,link]:
  for mode,want in [('60600',name),('120777','block_device'),('100600','block_device')]:
   run([T/'context_lookup',A/'file_contexts.bin',path,mode],want=obj(want));lookups+=1
 run([T/'context_lookup',A/'file_contexts.bin',direct,'60600',link],want=obj(name));lookups+=1
run([T/'context_lookup',A/'file_contexts.bin','/sbin/p10-restore','100700'],want=obj('p10_restore_exec'));lookups+=1
sys.path.insert(0,str(R/'source'));from file_contexts import extract
actual=collections.Counter(extract((A/'file_contexts.bin').read_bytes()))
expected=collections.Counter((f[0],f[1] if len(f)==3 else '',f[-1]) for f in [l.split() for l in (A/'file_contexts').read_text().splitlines()])
assert actual==expected
(R/'evidence/policy-checks.json').write_text(json.dumps(dict(passed=True,checks=checks,compiled_context_lookups=lookups,compiled_rows=len(list(actual.elements()))),indent=2)+'\n')
print('POLICY_CONTEXT_PASS',len(checks),'checks;',lookups,'lookups')
