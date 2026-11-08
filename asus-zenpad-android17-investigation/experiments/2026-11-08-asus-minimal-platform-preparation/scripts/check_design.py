from pathlib import Path
import hashlib,importlib.util,json,re,shutil,subprocess,tempfile
R=Path(__file__).resolve().parents[1]
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
parse=lambda p:{m[1]:(m[2] or 'n') for m in re.finditer(r'^(?:# )?CONFIG_(\w+)(?:=(.*)| is not set)$',p.read_text(),re.M)}
b=parse(R/'config/baseline.config');a=parse(R/'config/resolved.config');intent=json.loads((R/'config/intent.json').read_text())
assert sha(R/'config/baseline.config')=='708a88175ea777c09410000dfe5cf562ccbf764955eb9deaadda7326d0a966e1'
for n,v in intent['request'].items():assert a.get(n,'n')==v,(n,a.get(n),v)
keepers='SMP NR_CPUS HOTPLUG_CPU PREEMPT HZ ARM_GIC ARM_GIC_V3 MTK_GIC_EXT MTK_SYSIRQ MTK_SYS_CIRQ ARM_ARCH_TIMER ARM_ARCH_TIMER_EVTSTREAM MTK_TIMER MTK_ARCHCOUNTER_TIMESYNC CPU_FREQ CPU_IDLE MTK_BASE_POWER MTK_FREQ_HOPPING POWER_SUPPLY MTK_PMIC MTK_PMIC_WRAP MTK_SMART_BATTERY ASUS_P00A_MAIN_BATTERY_SOC ASUS_P00A_BATTERY_DIAGNOSTIC ASUS_P00A_BQ25896 THERMAL THERMAL_ASUS_P00A MTK_THERMAL VIRTUAL_SENSOR_THERMAL WATCHDOG WATCHDOG_CORE MEDIATEK_WATCHDOG MTK_WD_KICKER POWER_RESET KEYBOARD_MTK KPD_PWRKEY_USE_PMIC REGULATOR REGULATOR_MT6323 REGULATOR_SYM827 COMMON_CLK_MEDIATEK MTK_INFRACFG MTK_SCPSYS_MT8163 MEDIATEK_MT6577_AUXADC ASUS_P00A_RETAINED_BOOT_TRACE SERIAL_8250_CONSOLE'.split()
for n in keepers:assert a.get(n)==b.get(n),(n,b.get(n),a.get(n))
assert a['CPU_FREQ']=='y' and a['PREEMPT']=='y'
assert a.get('SERIAL_8250_CONSOLE','n')=='n'
assert json.loads((R/'evidence/07_resolve_closure.json').read_text())['stderr']==''
identity=json.loads((R/'evidence/design-identity.json').read_text())
assert identity['resolved_config_sha256']==sha(R/'config/resolved.config')
assert identity['compiled_candidate_sha256'] is None and identity['packaged_candidate_sha256'] is None
manifest=json.loads((R/'dt/status-manifest.json').read_text());paths=[x['path'] for x in manifest]
assert len(paths)==len(set(paths))
p=R.parent/'2026-11-07-asus-linux49-calibrated-entry-build/source/fdt.py'
spec=importlib.util.spec_from_file_location('existing_fdt',p);m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
_,nodes,_=m.parse((p.parent/'expected-runtime.dtb').read_bytes())
for path in paths:
 assert path in nodes,path
 assert not any(x in path for x in ['reserved','memory','thermal','pmic','regulator','pwrap','keypad','toprgu','interrupt-controller','timer','cpufreq'])
dts=R/'source/proposed/arch/arm64/boot/dts/mediatek/asus-p00a.dts'
old=(R/'source/baseline/arch/arm64/boot/dts/mediatek/asus-p00a.dts').read_text()
new=dts.read_text();args=a['CMDLINE'].strip('"')
expected=old.replace('console=ttyMT0,921600n1 root=/dev/ram',args)
assert new.split('\n/* One RAM-only consumer removal set.')[0]==expected
assert re.findall(r'&\{([^}]+)\} \{ status = "disabled"; \};',new)==paths
assert identity['board_dts_source_sha256']==sha(dts)
tag=(R/'source/proposed/arch/arm64/kernel/asus_entry_tag.h').read_text()
text=tag.split('#define ASUS_ENTRY_TAG "')[1].split('"\n')[0].replace('\\n','\n')
assert len(text.encode())==int(re.search(r'ASUS_ENTRY_TAG_LEN (\d+)',tag)[1])
assert identity['run_uuid'] in tag and identity['resolved_config_sha256'] in tag
helper=(R/'source/ram_pid1.c').read_text()
for forbidden in ['sched_setscheduler','sched_setparam','setpriority','SCHED_FIFO','/sys/','/dev/block','/dev/mmc','udev','USB','clock_settime']:
 assert forbidden not in re.sub(r'/\*.*?\*/', '', helper, flags=re.S),forbidden
loop=helper.split('for (i = 0; i < 2000000U; i++) {')[1].split('}')[0]
assert 'report' not in loop and 'clock' not in loop
assert 'volatile unsigned int state' in helper and 'volatile unsigned long long checksum' in helper
handler=helper.split('static void on_alarm(int signal_number)')[1].split('}')[0]
assert 'alarm_seen = 1;' in handler and 'report' not in handler
assert 'cycle <= 5' in helper and 'sigsuspend' in helper and 'SIGALRM' in helper
(R/'tmp').mkdir(exist_ok=True)
with tempfile.TemporaryDirectory(prefix='patch-qa-',dir=R/'tmp') as temp:
 root=Path(temp);(root/'out').mkdir();shutil.copyfile(R/'config/baseline.config',root/'out/.config')
 for p in (R/'source/proposed').rglob('*'):
  if p.is_file():
   rel=p.relative_to(R/'source/proposed');dest=root/'kernel'/rel;dest.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(R/'source/baseline'/rel,dest)
 q=subprocess.run(['patch','-p1','-i',str(R/'minimal-platform.delta.patch')],cwd=root,text=True,capture_output=True)
 assert q.returncode==0,q.stdout+q.stderr
 assert (root/'out/.config').read_bytes()==(R/'config/resolved.config').read_bytes()
 for p in (R/'source/proposed').rglob('*'):
  if p.is_file():assert (root/'kernel'/p.relative_to(R/'source/proposed')).read_bytes()==p.read_bytes()
 for n in ['ram_pid1.c','run_identity.h']:assert (root/'helper'/n).read_bytes()==(R/'source'/n).read_bytes()
receipt=json.loads((R/'evidence/08_freeze_design.json').read_text())
assert receipt['owned_out_files']==['.config','.config.old']
for key in ['kernel_compiled','helper_compiled','packaged','device_contact']:assert receipt[key] is False
result=dict(status='STATIC_PREPARATION_CHECKS_PASS',config_requests_satisfied=True,keeper_configs_equal_baseline=keepers,olddefconfig_warnings=0,dt_status_paths_verified=len(paths),source_change_files=receipt['changed_source_files'],single_combined_patch_applies=True,entry_tag_bytes=len(text.encode()),helper_review='source contracts only; no compiler or runtime check',no_kernel_helper_or_host_compilation=True,no_packaging_or_device_contact=True)
(R/'evidence/design-check.json').write_text(json.dumps(result,indent=2)+'\n')
print(json.dumps(result,indent=2))
