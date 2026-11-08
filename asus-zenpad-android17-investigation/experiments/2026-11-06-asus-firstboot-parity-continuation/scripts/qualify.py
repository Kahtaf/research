from pathlib import Path
import json,hashlib,re,datetime
P=Path("/srv/android/asus-firstboot-runtime");R=Path("/srv/android/asus-firstboot-parity-continuation")
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def config(p):
 d={}
 for l in p.read_text().splitlines():
  if l.startswith('CONFIG_'):
   k,v=l.split('=',1);d[k]=v
  elif l.startswith('# CONFIG_') and l.endswith(' is not set'):d[l.split()[1]]='n'
 return d
before=config(P/'inputs/physical-baseline.config');now=config(P/'kernel-build-r7/.config');oldrows=json.loads((P/'evidence/core-kconfig-comparison.json').read_text());selected={r['option'] for r in oldrows}|{'CONFIG_CPUSETS','CONFIG_FILE_LOCKING','CONFIG_BLK_CGROUP'}|set(json.loads(Path('/srv/android/asus-android17-runtime-prereqs/handoff-r1/evidence/config-expanded-comparison-r4.json').read_text()));rows=[]
for k in sorted(selected):
 target='y' if k=='CONFIG_BLK_CGROUP' else before.get(k,'n');assert now.get(k,'n')==target,(k,now.get(k),target);rows.append(dict(option=k,physical=before.get(k,'n'),tested=now.get(k,'n'),expected=target))
(R/'evidence/firstboot-config-equivalence-r3.json').write_text(json.dumps(dict(options=rows,all_expected=True,physical_only_delta='CONFIG_BLK_CGROUP=y',fixture_repair='FILE_LOCKING restored to existing physical y',never_copy_virtual_config=True),indent=2))
checks=[]
def test(name,ok):checks.append(dict(name=name,passed=bool(ok)));assert ok,name
def log(name):
 status=json.loads((R/name/'status.json').read_text());test(name+'_completed',status['returncode']==0 and not status['timeout']);return (R/name/'serial.log').read_text()
x=log('evidence/run-cpuset-r1');test('negative_mount_old_kernel','name=mount_v2_mode pass=0 errno=2' in x and 'name=mount_blkio pass=1' in x and 'failures=1' in x)
x=log('run-cpuset-r3');test('13_cpuset_behavior_checks',len(re.findall(r'CPUSET_TEST name=\S+ pass=1',x))==13 and 'failures=0' in x)
x=log('run-policy-r4');test('policy_load_enforcing','PRODUCT_POLICY_LOAD bytes=872537 expected=872537 errno=0' in x and x.count('READ /sys/fs/selinux/enforce 1')==2 and 'policyvers 30' in x)
x=log('run-boot-r11');test('setup_cgroups_succeeded',bool(re.search(r"Command 'SetupCgroups'.*succeeded",x)));test('uid0_created','Created cgroup /sys/fs/cgroup/system/uid_0' in x and 'OBS_STAT path=/sys/fs/cgroup/system/uid_0 rc=0' in x);test('genuine_init_sid','path=/proc/1/attr/current bytes=12 value=u:r:init:s0' in x);test('genuine_ueventd_sid',bool(re.search(r'path=/proc/\d+/attr/current bytes=15 value=u:r:ueventd:s0',x)));test('genuine_ueventd_group',bool(re.search(r'path=/sys/fs/cgroup/system/uid_0/pid_(\d+)/cgroup.procs bytes=\d+ value=\1',x)));test('shell_sid','path=/proc/self/attr/current bytes=13 value=u:r:shell:s0' in x);test('enforcement','path=/sys/fs/selinux/enforce bytes=1 value=1' in x);test('genuine_coldboot_property','FIRSTBOOT_COLDBOOT_PROPERTY=true' in x);test('property_allowed','OBS_PROPERTY_ALLOWED rc=0' in x and 'name=debug.firstboot.runtime_probe length=8 value=observed' in x);test('property_denied','PROP_ERROR_PERMISSION_DENIED (0x18)' in x and 'name=persist.firstboot_runtime.denied length=0 value=' in x);test('unchanged_cgroups_json',sha(P/'inputs/boot-r10/root/system/etc/cgroups.json')=='ab2ed667ff45958843fb0c6ee953a5512def0ae87470c4358aa9576a6a4b2e22');test('honest_missing_apexd_gate',"Cannot find '/system/bin/apexd'" in x and 'bootstrap-apexd-failed' in x)
x=log('run-locks-r1');test('5_posix_lock_checks',len(re.findall(r'LOCK_TEST name=\S+ pass=1',x))==5 and 'LOCK_PROBE_END failures=0' in x)
(R/'evidence/qualification-r3.json').write_text(json.dumps(dict(utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),checks=checks,all_passed=True,scope='Kernel/cgroups/genuine init/ueventd/SELinux/property IPC only',crypto_apex_authenticated_adbd=False,optional_memcg_not_enabled=True,cpu_hotplug_tested=False),indent=2));print('qualification checks',len(checks),'config options',len(rows))
