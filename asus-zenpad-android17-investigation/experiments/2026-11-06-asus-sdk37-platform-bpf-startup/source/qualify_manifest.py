from pathlib import Path
import os,json,re,hashlib,subprocess as s,struct
os.sched_setaffinity(0,{min(os.sched_getaffinity(0))})
O=Path('/srv/android/asus-sdk37-platform-bpf-startup-20261106');T=Path('/srv/android/lineage24');R=Path('/srv/android/asus-network-runtime')
def sha(p):
 with p.open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def sections(p):
 d=p.read_bytes();shoff=struct.unpack_from('<Q',d,40)[0];ent,count,idx=struct.unpack_from('<HHH',d,58);heads=[struct.unpack_from('<IIQQQQIIQQ',d,shoff+i*ent) for i in range(count)];names=d[heads[idx][4]:heads[idx][4]+heads[idx][5]];return {names[h[0]:].split(b'\0')[0].decode():hashlib.sha256(d[h[4]:h[4]+h[5]]).hexdigest() for h in heads if h[2]&2 or h[1] in (9,)}
comparison={}
for name in ['clatd','dscpPolicy','offload','test']:
 a=R/'artifacts/bpf-original'/(name+'.o');b=O/'inputs/runtime-root-r2/apex/com.android.tethering/etc/bpf/mainline'/(name+'.o');x,y=sections(a),sections(b);comparison[name]={'prior_sha256':sha(a),'actual_captured_sha256':sha(b),'allocated_and_relocation_sections_equal':x==y,'different_sections':[k for k in x.keys()|y.keys() if x.get(k)!=y.get(k)]}
(O/'evidence/connectivity-object-equivalence.json').write_text(json.dumps(comparison,indent=2)+'\n')
pre=O/'run-preimage-r2';post=O/'run-postimage-r2';neg=O/'run-mandatory-negative-r2'
logs={n:(p/'serial.log').read_text(errors='replace') for n,p in [('preimage',pre),('postimage',post),('mandatory_negative',neg)]}
assert 'EXEC_RESULT /system/bin/network_loader rc=134' in logs['preimage'] and 'Error when loading /system/etc/bpf/bpfRingbufProg.bpf: Invalid argument' in logs['preimage']
assert 'EXEC_RESULT /system/bin/network_loader rc=125' in logs['postimage'] and 'Skip /system/etc/bpf/bpfRingbufProg.bpf below its kernel minimum' in logs['postimage']
assert 'EXEC_RESULT /system/bin/network_loader rc=134' in logs['mandatory_negative'],logs['mandatory_negative'][-3000:]
assert 'WHOLE_LOADER_RESULT mainline_done=0' in logs['mandatory_negative']
preinputs=json.loads((pre/'inputs.json').read_text());postinputs=json.loads((post/'inputs.json').read_text());delta={k for k in preinputs.keys()|postinputs.keys() if preinputs.get(k)!=postinputs.get(k)};assert delta=={'system/bin/bpfloader','entropy.seed'},delta
selection=json.loads((O/'evidence/selection.json').read_text());status=[]
for obj in selection['objects']:
 path=obj['install_path'];row={'path':path,'captured':not obj.get('missing',False),'sha256':obj.get('sha256')}
 if path.startswith('system/etc/bpf/'):
  error=re.findall(r'Error when loading /?'+re.escape(path)+r': ([^\n\r]*)',logs['postimage']);row['reported_errors']=sorted(set(re.sub(r'OBSERVED_LOGDW.*','',x).strip('| ') for x in error));row['ringbuf_kernel_minimum_skip']=path.endswith('bpfRingbufProg.bpf');row['startup_critical_in_original_source']=path.endswith('bpfRingbufProg.bpf');row['load_qualified']=False
 elif obj.get('missing'):row['gate']='No compiled output on actual selected install chain at capture; vendor stage runs with empty vendor object directory.'
 status.append(row)
pins=[l for l in logs['postimage'].splitlines() if l.startswith('PIN ')];(O/'evidence/runtime-pins.txt').write_text('\n'.join(pins)+'\n')
(O/'evidence/object-runtime-status.json').write_text(json.dumps(status,indent=2)+'\n')
active_pre=sha(T/'system/bpf/loader/bpfloader.rs');assert active_pre=='1548dffa03b5091bbb9b7cfcce92495ee2167f417e90b431117cf31ea77b4bd2'
source_head=s.check_output(['git','-C',str(T/'system/bpf'),'rev-parse','HEAD'],text=True).strip()
resources={}
for mode,p in [('preimage',pre),('postimage',post),('mandatory_negative',neg)]:
 conf=json.loads((p/'command.json').read_text());res=(p/'host-resources.txt').read_text();resources[mode]={'rss_kib':int(re.search(r'Maximum resident set size \(kbytes\): (\d+)',res).group(1)),'rlimit_as_bytes':conf['rlimit_as_bytes'],'guest_ram_mib':conf['guest_ram_mib'],'cpu_affinity':conf['cpu_affinity']};assert resources[mode]['rss_kib']<1024**2
checks={'preimage_reproduces_ringbuf_einval_abort':True,'postimage_reaches_actual_setproperty_125':True,'mandatory_corrupt_netd_rejected_exit_134':True,'pre_post_fixture_input_delta':sorted(delta),'all_selected_platform_objects_captured':all(not x.get('missing') for x in selection['objects'] if x['install_path'].startswith('system/etc/bpf/')),'selected_platform_count':sum(x['install_path'].startswith('system/etc/bpf/') for x in selection['objects']),'missing_selected_outputs':[x for x in selection['objects'] if x.get('missing')],'runtime_pin_count':len(pins),'resources':resources,'active_system_bpf_preimage_unchanged':active_pre,'system_bpf_git_head':source_head,'no_new_kernel_config_requirement':True,'full_platform_features_qualified':False,'service_readiness_qualified':False,'physical_go':False}
(O/'evidence/qualification.json').write_text(json.dumps(checks,indent=2)+'\n');print(json.dumps(checks,indent=2))
print('OPTIONAL FAILURES')
for l in logs['postimage'].splitlines():
 if any(x in l for x in ['libbpf:','PIN path=/sys/fs/bpf/vendor']):print(l)
