from pathlib import Path
import subprocess,json,sys,collections,os,hashlib,resource,time
R=Path(__file__).resolve().parents[1];A=Path(os.environ.get('POLICY_CONTEXT_DIR',R/'inputs'));T=Path(os.environ.get('POLICY_TOOLS',R/'tools/host'))
POLICY=Path(os.environ.get('POLICY_BINARY',R/'artifacts/UNQUALIFIED-future5role-policy'))
started=time.monotonic()
def limits():
 resource.setrlimit(resource.RLIMIT_CPU,(10,10))
 resource.setrlimit(resource.RLIMIT_CORE,(0,0))
xperms=[]
checks=[]
def run(cmd,expect=0,want=None):
 assert time.monotonic()-started<180
 p=subprocess.run(list(map(str,cmd)),capture_output=True,text=True,timeout=10,preexec_fn=limits)
 ok=p.returncode==expect and (want is None or p.stdout.strip()==want)
 checks.append(dict(command=list(map(str,cmd)),returncode=p.returncode,stdout=p.stdout,stderr=p.stderr,passed=ok))
 assert ok,checks[-1]
 return p
def sub(t):return 'u:r:'+t+':s0'
def obj(t):return 'u:object_r:'+t+':s0'
def check(src,tgt,cl,perm,allowed):run([T/'policy_constraints',POLICY,sub(src),tgt,cl,perm],0 if allowed else 1)
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
run([T/'policy_query',POLICY,sub('os_rescue'),obj('p10_restore_exec'),'process','--transition'],want=sub('p10_restore'))
# Preserve all 43 original policy assertions, including the transition query.
original_policy_checks=len(checks)
assert original_policy_checks==43
for permission in ['open','read','write','getattr','ioctl']:
 check('os_rescue',obj('rescue_userdata_device'),'blk_file',permission,True)
for permission in ['create','unlink','append','execute','setattr','relabelfrom','relabelto','lock']:
 check('os_rescue',obj('rescue_userdata_device'),'blk_file',permission,False)
for permission in ['open','getattr','ioctl']:
 check('p10_restore',obj('rescue_userdata_device'),'blk_file',permission,False)
for node in ['rescue_disk_device','block_device','metadata_block_device','userdata_block_device','preloader_block_device','para_block_device','nvm_device','nvram_device']:
 check('os_rescue',obj(node),'blk_file','write',False)
for domain in ['shell','adbd']:
 for node in ['rescue_boot_device','rescue_system_device','rescue_recovery_device','rescue_disk_device','rescue_userdata_device','block_device']:
  for permission in ['open','read','write','getattr','ioctl']:
   check(domain,obj(node),'blk_file',permission,False)
for node in ['rescue_boot_device','rescue_system_device']:
 check('os_rescue',obj(node),'blk_file','open,read,write,getattr,ioctl',True)
pairs=[('os_rescue',n) for n in ['rescue_boot_device','rescue_system_device','rescue_recovery_device','rescue_disk_device','rescue_userdata_device']]+[('p10_restore',n) for n in ['rescue_boot_device','rescue_system_device','rescue_recovery_device','rescue_disk_device']]
for src,node in pairs+[('p10_restore','rescue_userdata_device')]:
 allowed=not (src=='p10_restore' and node=='rescue_userdata_device')
 for command in [0x1272,0x125d,0x1277,0x1273,0x1372,0xffff]:
  q=run([T/'policy_xperms',POLICY,src,node,hex(command)],0 if allowed and command==0x1272 else 1)
  row=json.loads(q.stdout)
  assert row['allowed']==([0x1272] if allowed else [])
  assert row['allowed_count']==int(allowed) and row['denied_count']==65536-int(allowed)
  xperms.append(row)
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
assert hashlib.sha256((A/"file_contexts.bin").read_bytes()).hexdigest()=="d82c9ca28d1d9017aea5f58d1cb9b46f6122ef22953ab32b7b4a3a8ccd07186c"
assert resource.getrusage(resource.RUSAGE_CHILDREN).ru_maxrss<1024**3
(R/'evidence/policy-checks.json').write_text(json.dumps(dict(passed=True,observed_children_maxrss_bytes=resource.getrusage(resource.RUSAGE_CHILDREN).ru_maxrss,serial=True,cpu_seconds_per_query=10,wall_seconds_per_query=10,suite_command_start_deadline_seconds=180,policy_sha256=hashlib.sha256(POLICY.read_bytes()).hexdigest(),checks=checks,original_policy_checks=original_policy_checks,original_context_checks=29,added_checks=len(checks)-72,compiled_context_lookups=lookups,compiled_rows=len(list(actual.elements())),xperms=xperms),indent=2)+'\n')
assert lookups==29
print('POLICY_CONTEXT_PASS',len(checks),'checks;',lookups,'lookups')
