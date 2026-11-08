"""Focused local artifact/assembly inspection; no build, image admission or device."""
from pathlib import Path
import sys,gzip,json,ast,struct,difflib,importlib.util
sys.dont_write_bytecode=True
R=Path(__file__).resolve().parents[1];sys.path.insert(0,str(R/'source'))
import bootformat as b
old=R.parent/'2026-11-07-asus-microsd-offline-prearmed'
for n in ['common.h','sd_mount.h','recovery_phase.h','sd_frontend.c','sha256.h']:assert (R/'source'/n).read_bytes()==(old/'source'/n).read_bytes()
assert (R/'artifacts/rescue-sd').read_bytes()==(old/'artifacts/sd_frontend.aarch64').read_bytes()
for n in ['os-rescue','rescue-sd','rescue-sd-supervisor']:
 d=(R/'artifacts'/n).read_bytes();b.elf_static(d);assert struct.unpack_from('<H',d,16)[0]==2
for p in [*(R/'source').glob('*.py'),*(R/'scripts').glob('*.py')]:ast.parse(p.read_text(),filename=str(p))
e=b.parse_cpio(gzip.decompress((R/'artifacts/common-rootfs.cpio.gz').read_bytes()))
for name,an in [('sbin/os-rescue','os-rescue'),('sbin/rescue-sd','rescue-sd'),('sbin/rescue-sd-supervisor','rescue-sd-supervisor'),('sepolicy','sepolicy'),('file_contexts.bin','file_contexts.bin')]:assert e[name][3]==(R/'artifacts'/an).read_bytes()
assert e['init'][3]==(R/'inputs/init').read_bytes()
assert e['sbin/ueventd']==(0o120777,0,0,b'../init')
rc=e['init.rc'][3].decode();action=(R/'source/init.offline.action.rc').read_text()
assert 'on init\n' in action and 'on boot\n' not in action and action.count('start rescue-sd-offline')==1
assert rc.count('start os-rescue')==1 and rc.count('socket os_rescue stream 0600 shell shell')==1
assert rc.count('oneshot')==3 and rc.count('disabled')==3
for line in (rc+action).splitlines():
 words=line.split()
 if words and not words[0].startswith('#'):assert words[0] not in ('rm','restart','class_start','onrestart')
assert not any(n in e for n in ['sbin/p10-restore','system/bin/sh','sbin/adbd','rescue.manifest','rescue.sd.arm'])
assert b'start rescue-sd-offline' not in e['init.rc'][3]
spec=importlib.util.spec_from_file_location('final_join',R/'scripts/final_package.py');m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
try:m.five_roles(m.ordinary(R.parent/'2026-11-06-asus-stock-only-ram-rescue-build/artifacts/original-stock.manifest',1024**2))
except ValueError:pass
else:raise AssertionError('two-role manifest was admitted')
(R/'evidence/daemon-readiness.patch').write_text(''.join(difflib.unified_diff((old/'source/rescue.c').read_text().splitlines(True),(R/'source/rescue.c').read_text().splitlines(True),fromfile='offline-prearmed/rescue.c',tofile='sd-init-core/rescue.c')))
receipt=dict(static_target_ELFs=['os-rescue','rescue-sd','rescue-sd-supervisor'],ELF_type='ET_EXEC',no_dynamic_or_interpreter=True,frontend_and_guards_byte_identical_to_offline_prearmed=True,common_archive_artifacts_byte_equal=True,stock_init_preserved=True,operational_action_event='init',automatic_normal_client_starts_in_common=0,automatic_normal_client_starts_after_final_join=1,wrapper_focused_cases=['actual waitpid exit0 requests reboot','exit1 retains recovery','SIGKILL retains recovery','exec failure exit127 retains recovery'],two_role_final_join_refused=True,no_fake_five_role_or_arm_id_created=True,physical_boot_verified=False,sd_hardware_verified=False)
(R/'evidence/final-local-check.json').write_text(json.dumps(receipt,indent=2)+'\n')
arts={n:dict(bytes=(R/'artifacts'/n).stat().st_size,sha256=b.sha((R/'artifacts'/n).read_bytes())) for n in ['os-rescue','rescue-sd','rescue-sd-supervisor','sepolicy','file_contexts.bin','common-rootfs.cpio.gz']}
(R/'artifacts/ARTIFACTS.json').write_text(json.dumps(arts,indent=2)+'\n')
print(json.dumps(arts,indent=2))
