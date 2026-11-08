from pathlib import Path
import json,re,hashlib,datetime
R=Path('/srv/android/asus-sdk37-lmkd-functional');results={}
def readrun(n):
 O=R/('run-boot-'+n);raw=(O/'serial.log').read_bytes();t=re.sub(r'\[\s*\d+\.\d+\]\s*','',raw.decode('utf-8',errors='replace'));return O,t
for n in ['r4','r5','r10','r11','r12','r13','r14','r15','r17','r18','r20','r21','r22','r23']:
 O,t=readrun(n);a={'status':json.loads((O/'status.json').read_text()),'serial_sha256':hashlib.sha256((O/'serial.log').read_bytes()).hexdigest(),'serial_bytes':(O/'serial.log').stat().st_size}
 a['abort']=(O/'abort-request.json').exists();a['properties']={k:v for k,v in re.findall(r'LMKD_PROP_(\w[\w.]+)=(true|false|unset|[0-9]+)',t)}
 a['psi_registered']='Using psi monitors for memory pressure detection' in t;a['psi_fd_numbers']=sorted(set(int(x) for x in re.findall(r'DAEMON_FD /proc/\d+/fd/(\d+) -> /proc/pressure/memory',t)));a['epoll_entries']=[{'fd':int(fd),'events_hex':ev} for fd,ev in re.findall(r'tfd:\s*(\d+)\s+events:\s*([0-9a-fA-F]+)',t)]
 a['daemon_domain']='u:r:lmkd:s0' in t;a['enforcing']='VALUE /sys/fs/selinux/enforce 1' in t
 a['native_adjs']=[{'pid':int(p),'adj':int(v)} for p,v in re.findall(r'NATIVE_ADJ pid=(\d+) value=(-?\d+)',t)]
 a['notifications']=[{'pid':int(p),'uid':int(u)} for p,u in re.findall(r'DAEMON_KILL_NOTIFICATION pid=(\d+) uid=(\d+)',t)]
 a['child_final']=[{'pid':int(p),'wait_status':int(st),'daemon_notification':bool(int(note))} for p,st,note in re.findall(r'CHILD_FINAL pid=(\d+) status=(\d+) daemon_notification=(\d+)',t)]
 a['rounds']=[{'round':int(r),'notifications':int(n),'killcnt':int(c),'foreground_alive':int(f)} for r,n,c,f in re.findall(r'ROUND_PRESSURE_END round=(\d+) daemon_notifications=(\d+) killcnt=(\d+) foreground_alive=(\d+)',t)]
 a['recoveries']=[{'round':int(r),'foreground_heartbeat':int(f),'daemon_alive':int(d),'killcnt':int(c)} for r,f,d,c in re.findall(r'RECOVERY round=(\d+) foreground_heartbeat=(\d+) daemon_alive=(\d+) killcnt=(\d+)',t)]
 a['kernel_oom_log']=bool(re.search(r'invoked oom-killer|Out of memory:|Killed process \d+',t));a['swap_write_errors']=t.count('Write-error on swap-device');a['foreground_adj_verified']=any(x['adj']==-1000 for x in a['native_adjs']);a['memtotal_KiB']=sorted(set(map(int,re.findall(r'VALUE /proc/meminfo MemTotal:\s*(\d+)',t))))
 a['swap_KiB']=sorted(set(map(int,re.findall(r'VALUE /proc/meminfo SwapTotal:\s*(\d+)',t))));a['workload_swap_kB']=list(map(int,re.findall(r'PROTECTED_WARMUP_END workload_swapped_kB=(\d+)',t)))
 a['zram_samples']=[]
 for chunk in re.split(r'STATS ',t)[1:]:
  stage=chunk.split()[0];m=re.search(r'VALUE /sys/block/zram0/mm_stat\s+([\d ]+)',chunk)
  if m:
   vals=list(map(int,m[1].split()));a['zram_samples'].append({'stage':stage,'fields_bytes_except_page_counters':vals})
 a['psi_totals_us']=[{'kind':k,'total':int(v)} for k,v in re.findall(r'VALUE /proc/pressure/memory (some|full) .*?total=(\d+)',t)]
 a['zram_label']=re.findall(r'ZRAM_LABEL result=\d+ value=(\S+)',t)
 a['backing_devices']=sorted(set(re.findall(r'VALUE /sys/block/zram0/backing_dev (\S+)',t)))
 if n in ['r20','r21']:
  checks={'normal_terminal':a['status']['returncode']==0 and not a['status']['timeout'] and not a['abort'],'actual_low_ram_props':all(a['properties'].get(k)==v for k,v in {'ro.config.low_ram':'true','ro.config.per_app_memcg':'false','ro.lmk.use_new_strategy':'true','ro.lmk.use_minfree_levels':'false'}.items()),'psi_start_and_two_real_fds':a['psi_registered'] and len(a['psi_fd_numbers'])>=2,'psi_epoll_registration':len({fd for fd in a['psi_fd_numbers'] if any(e['fd']==fd and int(e['events_hex'],16)&2 for e in a['epoll_entries'])})==2,'enforcing_lmkd_domain':a['enforcing'] and a['daemon_domain'],'approximately_stock_memory':a['memtotal_KiB']==[2001792],'zram_active':a['swap_KiB']==[524284] and a['backing_devices']==['none'],'two_daemon_evictions':len(a['notifications'])==2 and len(a['rounds'])==2 and [r['killcnt'] for r in a['rounds']]==[1,2],'sigkill_correlates':all(any(x['pid']==v['pid'] and x['wait_status']==9 and x['daemon_notification'] for x in a['child_final']) for v in a['notifications']),'protected_foreground_recovers_twice':a['foreground_adj_verified'] and len(a['recoveries'])==2 and all(x['foreground_heartbeat']==1 and x['daemon_alive']==1 for x in a['recoveries']),'no_kernel_oom_or_swap_write_error':not a['kernel_oom_log'] and not a['swap_write_errors'],'real_pressure':any(x['total']>0 for x in a['psi_totals_us'])}
  a['checks']=checks;a['accepted']=all(checks.values())
 results[n]=a
_,t17=readrun('r17');_,t18=readrun('r18');_,t4=readrun('r4');_,t15=readrun('r15')
negatives={'missing_PSI_ENOENT':('No kernel psi monitor support (errno=2)' in t4 and not results['r4']['psi_registered']),'invalid_window_EINVAL':("write failed for psi stall type 'some'; errno=22" in t17 and not results['r17']['psi_registered']),'old_strategy_MEMCG_v1_rejected':('Old kill strategy can only be used with v1 cgroup hierarchy' in t18 and not results['r18']['psi_registered']),'original_zram_label_denied':('mkswap: /dev/block/zram0: Permission denied' in t15 and 'u:object_r:ram_device:s0' in results['r15']['zram_label'])}
summary={'utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'default_low_ram_functional_pass_with_staged_label_fix':all(results[n]['accepted'] for n in ['r20','r21']) and all(negatives.values()),'negative_checks':negatives,'runs':results,'parser_revision':'r2: distinguish the two EPOLLPRI monitor fds from the additional read-only PSI statistics fd; r1 false rejection preserved','limits':['No full framework/GMS/hardware usability acceptance','Compiled policy unchanged, but fixture uses diagnostic su-domain harness and a one-line vendor file-context candidate','Auxiliary protected incompressible overload r23 aborted after swap-write failures; QEMU exit 0 does not mean pass','r11/r12 used defaults because prop.default was not consumed; superseded by r20/r21','r13/r14 ineffective config negatives superseded by r17/r18','r21 runtime succeeded; post-run text display raised UnicodeDecodeError; raw evidence retained']}
(R/'evidence/qualification.json').write_text(json.dumps(summary,indent=2));print(json.dumps({'pass':summary['default_low_ram_functional_pass_with_staged_label_fix'],'negative_checks':negatives,'main_checks':{n:results[n]['checks'] for n in ['r20','r21']}},indent=2))
