from pathlib import Path
import json,hashlib,shutil,subprocess as s,re,datetime
R=Path('/srv/android/asus-firstboot-runtime');T=Path('/srv/android/lineage24/kernel/asus/p00a-fd');K=R/'kernel-cpuset-r1';A=R/'apply-check-r1';A.mkdir();records=[]
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
cp=json.loads((R/'stagedpatches/cpuset-v2/manifest.json').read_text());bc=json.loads((R/'stagedpatches/blkio/manifest.json').read_text());files=cp['files']+[dict(path='arch/arm64/configs/asus_p00a_defconfig',before_sha256=bc['before_sha256'],after_sha256=bc['after_sha256'])]
for row in files:
 src=T/row['path'];assert sha(src)==row['before_sha256'],row;dst=A/row['path'];dst.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(src,dst)
for f in [R/'stagedpatches/blkio/0001-enable-blkio-cgroup.patch',R/'stagedpatches/cpuset-v2/0002-cpuset-v2-mode-backport.patch']:
 cmd=['patch','--batch','--fuzz=0','-p1','-d',str(A),'-i',str(f)];p=s.run(cmd,capture_output=True,text=True);records.append(dict(command=cmd,returncode=p.returncode,stdout=p.stdout,stderr=p.stderr));assert p.returncode==0,p.stdout+p.stderr
for row in files:
 assert sha(A/row['path'])==row['after_sha256'];assert sha(T/row['path'])==row['before_sha256']
 if row['path']!='arch/arm64/configs/asus_p00a_defconfig':assert (A/row['path']).read_bytes()==(K/row['path']).read_bytes()
(R/'evidence/physical-apply-validation.json').write_text(json.dumps(dict(commands=records,files=files,physical_source_unchanged=True,applied_source_equals_tested_source=True),indent=2))
old=json.loads(Path('/srv/android/asus-android17-runtime-prereqs/handoff-r1/evidence/full-source-equivalence.json').read_text());paths=set(old['selected_files']);paths.update(p.relative_to(K).as_posix() for p in (K/'security/selinux').rglob('*') if p.is_file());paths.update(['kernel/cgroup.c','kernel/cpuset.c','kernel/cgroup_freezer.c','include/linux/cgroup-defs.h','include/linux/cgroup.h','include/linux/cpuset.h']);rows=[];changed={r['path']:r for r in cp['files']}
for rel in sorted(paths):
 b=sha(T/rel);v=sha(K/rel);expected=changed.get(rel,{}).get('after_sha256',b);assert v==expected,(rel,b,v,expected);rows.append(dict(path=rel,physical_sha256=b,tested_sha256=v,expected_staged_change=rel in changed))
(R/'evidence/firstboot-source-equivalence.json').write_text(json.dumps(dict(physical_commit=old['physical_commit'],physical_readonly=True,files=rows,all_expected=True,excluded_virtual_guard='drivers/irqchip/irq-gic-v3.c inherited from accepted virtual fixture',network_patches_included=False),indent=2))
def config(p):
 d={}
 for l in p.read_text().splitlines():
  if l.startswith('CONFIG_'):
   k,v=l.split('=',1);d[k]=v
  elif l.startswith('# CONFIG_') and l.endswith(' is not set'):d[l.split()[1]]='n'
 return d
before=config(R/'inputs/physical-baseline.config');now=config(R/'kernel-build-r6/.config');oldrows=json.loads((R/'evidence/core-kconfig-comparison.json').read_text());selected={r['option'] for r in oldrows}|{'CONFIG_CPUSETS','CONFIG_FILE_LOCKING','CONFIG_BLK_CGROUP'};rows=[]
for k in sorted(selected):
 target='y' if k=='CONFIG_BLK_CGROUP' else before.get(k,'n');assert now.get(k,'n')==target,(k,now.get(k),target);rows.append(dict(option=k,physical=before.get(k,'n'),tested=now.get(k,'n'),expected=target))
assert (R/'kernel-build-r5/.config').read_bytes()==(R/'kernel-build-r6/.config').read_bytes();(R/'evidence/firstboot-config-equivalence.json').write_text(json.dumps(dict(options=rows,all_expected=True,r5_r6_config_identical=True,physical_only_delta='CONFIG_BLK_CGROUP=y',never_copy_virtual_config=True),indent=2))
checks=[]
def test(name,ok):checks.append(dict(name=name,passed=bool(ok)));assert ok,name
def log(name):
 status=json.loads((R/name/'status.json').read_text());test(name+'_completed',status['returncode']==0 and not status['timeout']);return (R/name/'serial.log').read_text()
x=log('run-cpuset-r1');test('negative_mount_old_kernel','name=mount_v2_mode pass=0 errno=2' in x and 'name=mount_blkio pass=1' in x and 'failures=1' in x)
x=log('run-cpuset-r2');test('13_cpuset_behavior_checks',len(re.findall(r'CPUSET_TEST name=\S+ pass=1',x))==13 and 'failures=0' in x)
x=log('run-policy-r3');test('policy_load_enforcing','PRODUCT_POLICY_LOAD bytes=872537 expected=872537 errno=0' in x and x.count('READ /sys/fs/selinux/enforce 1')==2 and 'policyvers 30' in x)
x=log('run-boot-r10');test('setup_cgroups_succeeded',bool(re.search(r"Command 'SetupCgroups'.*succeeded",x)));test('uid0_created','Created cgroup /sys/fs/cgroup/system/uid_0' in x and 'OBS_STAT path=/sys/fs/cgroup/system/uid_0 rc=0' in x);test('genuine_init_sid','path=/proc/1/attr/current bytes=12 value=u:r:init:s0' in x);test('genuine_ueventd_sid',bool(re.search(r'path=/proc/\d+/attr/current bytes=15 value=u:r:ueventd:s0',x)));test('genuine_ueventd_group',bool(re.search(r'path=/sys/fs/cgroup/system/uid_0/pid_(\d+)/cgroup.procs bytes=\d+ value=\1',x)));test('shell_sid','path=/proc/self/attr/current bytes=13 value=u:r:shell:s0' in x);test('enforcement','path=/sys/fs/selinux/enforce bytes=1 value=1' in x);test('genuine_coldboot_property','FIRSTBOOT_COLDBOOT_PROPERTY=true' in x);test('property_allowed','OBS_PROPERTY_ALLOWED rc=0' in x and 'name=debug.firstboot.runtime_probe length=8 value=observed' in x);test('property_denied','PROP_ERROR_PERMISSION_DENIED (0x18)' in x and 'name=persist.firstboot_runtime.denied length=0 value=' in x);test('unchanged_cgroups_json',sha(R/'inputs/boot-r10/root/system/etc/cgroups.json')=='ab2ed667ff45958843fb0c6ee953a5512def0ae87470c4358aa9576a6a4b2e22');test('honest_missing_apexd_gate',"Cannot find '/system/bin/apexd'" in x and 'bootstrap-apexd-failed' in x)
(R/'evidence/qualification-r2.json').write_text(json.dumps(dict(utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),checks=checks,all_passed=True,scope='Kernel/cgroups/genuine init/ueventd/SELinux/property IPC only',crypto_apex_authenticated_adbd=False,optional_memcg_not_enabled=True,cpu_hotplug_tested=False),indent=2));print('qualification checks',len(checks),'source files',len(paths),'config options',len(rows))
