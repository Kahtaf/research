from pathlib import Path
import base64,difflib,hashlib,json,os,re,subprocess
R=Path('/srv/android/asus-minimal-platform-build-r3-20261108');F=Path('/srv/android/asus-minimal-platform-build-r2-20261108');K=R/'kernel';O=R/'out';E=R/'evidence'
assert not (E/'final-config-gate.json').exists()
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
parse=lambda s:{m[1]:(m[2] or 'n') for m in re.finditer(r'^(?:# )?CONFIG_(\w+)(?:=(.*)| is not set)$',s,re.M)}
s=(O/'.config').read_text();pins=['ANDROID_PARANOID_NETWORK','NETWORK_FILESYSTEMS','SECCOMP_FILTER','TRACING_EVENTS_GPIO']
for n in pins:
 s,count=re.subn(r'^(?:# )?CONFIG_'+n+r'(?:=.*| is not set)$','# CONFIG_'+n+' is not set',s,flags=re.M);assert count==1,n
(R/'source/visible-defaults-off.config').write_text(s);(O/'.config').write_text(s)
env=dict(os.environ,ARCH='arm64',SRCARCH='arm64',KERNELVERSION='4.9.337',srctree=str(K),objtree=str(O),KCONFIG_CONFIG=str(O/'.config'),CC='aarch64-linux-gnu-gcc',HOSTCC='gcc')
q=subprocess.run([str(O/'scripts/kconfig/conf'),'--olddefconfig','Kconfig'],cwd=K,env=env,text=True,capture_output=True)
assert q.returncode==0 and not q.stderr,q.stderr
before=(F/'out/.config').read_text();after=(O/'.config').read_text();a=parse(before);b=parse(after)
delta={n:dict(before=a.get(n,'n'),after=b.get(n,'n')) for n in sorted(a.keys()|b.keys()) if a.get(n,'n')!=b.get(n,'n')}
classification={
'NET':'accepted core networking initialization, loopback/netlink; not only uevents',
'GENERIC_NET_UTILS':'hidden NET helper infrastructure',
'NLATTR':'netlink attribute support for NET core',
'MAY_USE_DEVLINK':'hidden reachability helper; NET_DEVLINK remains off; not a devlink driver',
'RPS':'hidden default-y core receive steering, no new netdevice driver',
'RFS_ACCEL':'hidden default-y core flow steering, no NIC selected',
'CPU_RMAP':'selected core CPU reverse-map support for RFS',
'XPS':'hidden default-y core transmit steering, no NIC selected',
'BQL':'hidden default-y core byte-queue limit support',
'DQL':'core dynamic queue limit helper selected by BQL',
'NET_FLOW_LIMIT':'hidden default-y core flow limit support under RPS',
'NET_RX_BUSY_POLL':'hidden default-y generic busy-poll API, no helper/socket polling workload introduced',
'FTRACE':'accepted trace configuration menu/core infrastructure',
'ENABLE_DEFAULT_TRACERS':'accepted selection of core TRACING without active GENERIC_TRACER',
'TRACING':'core trace infrastructure; generic tracing-on flag set after init, nop/default events inactive',
'NOP_TRACER':'default nop tracer with no-op start/stop',
'EVENT_TRACING':'core event definitions and controls; no event enable bootarg or active event set',
'CONTEXT_SWITCH_TRACER':'hidden commandline/context-switch recording support selected by EVENT_TRACING; not SCHED_TRACER',
'RING_BUFFER':'generic minimal trace ring buffers allocated, not zero footprint',
'TRACEPOINTS':'dormant static tracepoint infrastructure',
'TRACE_CLOCK':'generic tracing clock helpers, no clock/counter configuration change',
'BINARY_PRINTF':'trace-core binary printf helper',
'BRANCH_PROFILE_NONE':'explicit no branch profiling',
'DISABLE_TRACE_PRINTK':'replaces trace_printk usage with existing pr_debug behavior',
'VS_BACKLIGHT_COOLER':'accepted removal of absent LCD brightness consumer only'
}
assert set(delta)<=set(classification),delta
for n,v in delta.items():assert v['after']==('n' if n=='VS_BACKLIGHT_COOLER' else 'y'),(n,v)
for n in pins:assert b.get(n,'n')=='n',n
for n in ['NETDEVICES','INET','IPV6','NETFILTER','PACKET','UNIX','WLAN','WIRELESS','BT','RFKILL','NET_KEY','NET_SCHED','NET_CLS_ACT','NET_DEVLINK','FUNCTION_TRACER','FUNCTION_GRAPH_TRACER','SCHED_TRACER','FTRACE_SYSCALLS','KPROBE_EVENT','UPROBE_EVENT','BPF_EVENTS','FTRACE_STARTUP_TEST','EVENT_TRACE_TEST_SYSCALLS','GENERIC_TRACER','MTK_COMBO','MTK_COMBO_WIFI','MTK_COMBO_BT','MTK_CCCI_DEVICES','USB','MMC','FB','SOUND','MEDIA_SUPPORT','MTK_SENSOR_SUPPORT']:
 assert b.get(n,'n')=='n',(n,b.get(n))
assert b['DISABLE_TRACE_PRINTK']=='y' and b['NET']=='y' and b['TRACING']=='y'
assert b.get('UEVENT_HELPER')==a.get('UEVENT_HELPER') and b.get('UEVENT_HELPER_PATH')==a.get('UEVENT_HELPER_PATH')
assert sha(K/'arch/arm64/boot/dts/mediatek/asus-p00a.dts')=='2d0c95c12d0fce6629dede4e0eff6590725de9ef5dbbb1f0acc0f3e63fca41b6'
assert sha(O/'arch/arm64/boot/dts/mediatek/asus-p00a.dtb')=='156e92ec5d4f5c4bd20169128c8aed0a89b43636d945d648392aaaec8b9bf82e'
assert sha(R/'helper/init')=='37e9e2a2d73447947fb33e57e9513fa6079517b571f5a41bc58fbb91f84633fc'
assert (R/'artifacts/ramdisk.wrapped').read_bytes()==(F/'artifacts/ramdisk.wrapped').read_bytes()
tag=K/'arch/arm64/kernel/asus_entry_tag.h';s=tag.read_text();assert s.count('6f8abd4290b19aad386770200825d3065e74fd8fb311d4b1b20c7af2cc621dc6')==1;tag.write_text(s.replace('6f8abd4290b19aad386770200825d3065e74fd8fb311d4b1b20c7af2cc621dc6',sha(O/'.config')))
i=json.loads((F/'evidence/identity.json').read_text());old=i['config_sha256'];i['config_sha256']=sha(O/'.config');i['entry_tag']=i['entry_tag'].replace(old,i['config_sha256']);i['history']='initial compiler failure + r2 link failure + one combined r3 continuation; helper compiled once originally and reused';(E/'identity.json').write_text(json.dumps(i,indent=2)+'\n')
# Remaining trace defaults: exact selected helper source and directly relevant Kconfig definitions.
extras={}
for n in ['kernel/trace/trace_sched_switch.c','net/core/Makefile','net/Kconfig']:
 p=K/n
 if p.is_file():extras['evidence/source-facts/'+n]=p.read_bytes()
record=dict(status='FINAL_CONFIG_GATE_PASS',olddefconfig_calls=2,second_resolution='only four newly visible unwanted defaults pinned off, same intent, no matrix',resolved_sha256=sha(O/'.config'),delta=delta,new_y_classification={n:classification[n] for n,v in delta.items() if v['after']=='y'},consumer_removal={'VS_BACKLIGHT_COOLER':classification['VS_BACKLIGHT_COOLER']},visible_defaults_pinned_off=pins,all_other_r2_effective_values_equal=True,UEVENT_HELPER_unchanged=True,DT_source_and_compiled_DT_unchanged=True,helper_ramdisk_unchanged=True,source_change_only='entry config SHA metadata',source_fact_gate='MET wrapper has no module/init function; trace default nop/empty event boot list/minimal buffers; backlight cooler only LCD brightness, scoped references self-only',trace_footprint='generic tracing_on flag defaults enabled after trace init; nop selected and empty boot event list; main ring requested size 1 and event temp PAGE_SIZE, each subject to two-page minimum plus reader/per-CPU metadata; default expansion target 1441792 bytes is not forced by this cmdline/config',NET_confound='netlink/loopback/core plus hidden generic queue/steering facilities; no connectivity/protocol/netdevice add-back',kernel_build_started=False)
(E/'final-config-gate.json').write_text(json.dumps(record,indent=2)+'\n');(E/'final-config-vs-r2.patch').write_text(''.join(difflib.unified_diff(before.splitlines(True),after.splitlines(True),fromfile='r2/.config',tofile='r3/.config')))
files={};paths={'artifacts/resolved.config':O/'.config','source/visible-defaults-off.config':R/'source/visible-defaults-off.config','source/asus_entry_tag.h':tag}
for p in E.glob('*'):paths['evidence/'+p.name]=p
for n,p in paths.items():extras[n]=p.read_bytes()
for n,d in extras.items():files[n]=dict(data=base64.b64encode(d).decode(),sha256=hashlib.sha256(d).hexdigest())
print(json.dumps(dict(files=files,gate=record)))
