from pathlib import Path
import json,hashlib,datetime,subprocess,shutil
R=Path('/srv/android/asus-firstboot-parity-continuation');P=Path('/srv/android/asus-firstboot-runtime');T=Path('/srv/android/lineage24')
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
checks=json.loads((R/'evidence/qualification-r3.json').read_text())['checks']
def check(n,v):checks.append({'name':n,'passed':bool(v)});assert v,n
runs=['run-cpuset-r3','run-locks-r1','run-policy-r4','run-boot-r11','run-locks-r2'];inputs={}
for name in runs:
 cmd=json.loads((R/name/'command.json').read_text());kernel=Path(cmd[cmd.index('-kernel')+1]);check(name+'_resource_bound',cmd[cmd.index('-smp')+1]=='1' and cmd[cmd.index('-m')+1]=='1024' and cmd[cmd.index('-nic')+1]=='none');check(name+'_kernel_binding',kernel==P/('kernel-build-r6/arch/arm64/boot/Image' if name=='run-locks-r2' else 'kernel-build-r7/arch/arm64/boot/Image'))
 inputs[name]={p.name:{'bytes':p.stat().st_size,'sha256':sha(p)} for p in (R/name).iterdir() if p.is_file() and p.suffix not in ['.ext4']}
neg=(R/'run-locks-r2/serial.log').read_text();status=json.loads((R/'run-locks-r2/status.json').read_text())
check('locking_negative_completed',status=={'returncode':0,'timeout':False})
check('locking_negative_detects_missing_support','LOCK_TEST name=parent_lock pass=0 errno=13' in neg and 'LOCK_TEST name=child_after_unlock pass=0 errno=13' in neg and 'LOCK_PROBE_END failures=3' in neg)
check('identical_lock_probe_elf',sha(R/'run-locks-r1/init')==sha(R/'run-locks-r2/init'))
boot=(R/'run-boot-r11/serial.log').read_text();check('genuine_property_sockets',"Created socket '/dev/socket/property_service'" in boot and "Created socket '/dev/socket/property_service_for_system'" in boot)
combined=json.loads((R/'evidence/combined-parity.json').read_text());check('290_scoped_sources_match',len(combined['sources'])==290 and combined['all_selected_equal']);check('134_scoped_options_match',len(combined['selected_config'])==134)
consumed=[P/'inputs/early-r1/init_first_stage',P/'inputs/boot-r10/root/system/bin/init',P/'inputs/boot-r10/root/system/bin/ueventd',P/'inputs/boot-r10/root/system/bin/firstboot-observer',P/'inputs/boot-r10/root/system/etc/cgroups.json',P/'inputs/boot-r10/root/system/etc/init/hw/init.rc',P/'inputs/boot-r10/fstab.mt8163',P/'inputs/boot-r10/work/file_contexts.bin']
for p in (P/'inputs/boot-r10/root').rglob('*sepolicy*'):
 if p.is_file():consumed.append(p)
inputs['consumed']=[{'path':str(p),'exists':p.exists(),'symlink':str(p.readlink()) if p.is_symlink() else None,'sha256':sha(p) if p.is_file() else None} for p in consumed]
inputs['r7_config']={'sha256':sha(P/'kernel-build-r7/.config')};inputs['r7_image']={'sha256':sha(P/'kernel-build-r7/arch/arm64/boot/Image')};inputs['r6_config']={'sha256':sha(P/'kernel-build-r6/.config')}
(R/'evidence/runtime-input-hashes.json').write_text(json.dumps(inputs,indent=2))
q={'utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'checks':checks,'all_passed':True,'count':len(checks),'scope':'r7 cgroup/SID/enforcing product policy/property IPC/POSIX lock parity; combined r5 scoped source and config equality','full_boot':False,'combined_kernel_executed':False,'hardware_tested':False,'crypto_apex_adbd_chain_tested':False,'mandatory_lock_semantics_tested':False,'memory_controller_tested':False,'cpu_hotplug_tested':False}
(R/'evidence/qualification-final.json').write_text(json.dumps(q,indent=2));print('Final checks',len(checks))
for n in ['.config']:shutil.copyfile(P/'kernel-build-r7'/n,R/'evidence/r7.config')
shutil.copyfile(Path('/srv/android/asus-build-continuation/integration-r5/resolved.config'),R/'evidence/combined-r5.config')
shutil.copyfile(P/'inputs/late-outputs-r1/manifest.json',R/'evidence/late-outputs-prior-manifest.json')
processes=subprocess.check_output(['ps','-eo','pid,ppid,etime,args'],text=True).splitlines(); selected=[l for l in processes if 'prebuilts/siso/linux-x86/siso ' in l or (l.strip().split() and l.strip().split()[0]=='78673')]
(R/'evidence/build-status-final.json').write_text(json.dumps({'utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'processes':selected,'last_log_bytes':Path('/srv/android/asus-device-product/logs/full-build-r5.log').read_bytes()[-1500:].decode(errors='replace'),'no_active_source_or_out_mutation':True},indent=2))
