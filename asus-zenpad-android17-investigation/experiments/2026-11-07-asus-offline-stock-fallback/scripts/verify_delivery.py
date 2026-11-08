"""Inspect this actual delivery; no image admission, device or broad suites."""
from pathlib import Path
import sys,struct,json,gzip,hashlib,ast,difflib,importlib.util
sys.dont_write_bytecode=True
R=Path(__file__).resolve().parents[1];sys.path.insert(0,str(R/'source'));import bootformat as b
old=R.parent/'2026-11-07-asus-sd-init-core-integration'
def function(text,name):
 start=text.index(name);pos=text.index('{',start);depth=1;end=pos+1
 while depth:
  depth+=(text[end]=='{')-(text[end]=='}');end+=1
 return text[start:end]
for n in ['common.h','sd_mount.h','recovery_phase.h','sha256.h']:assert (R/'source'/n).read_bytes()==(old/'source'/n).read_bytes()
for name in ['static int session(', 'static int identity(', 'static int open_part(', 'static int validate_fd(']:assert function((R/'source/rescue.c').read_text(),name)==function((old/'source/rescue.c').read_text(),name)
for name in ['static int write_role(', 'static int status_bound(', 'static int recovery_readback(', 'static int preflight(', 'static void make_trigger(', 'static int check_trigger(']:assert function((R/'source/sd_frontend.c').read_text(),name)==function((old/'source/sd_frontend.c').read_text(),name)
assert (R/'source/restore_core.h').read_bytes()==(R.parent/'2026-11-06-asus-ram-original-recovery-restorer/source/restore_core.h').read_bytes()
for p in [*(R/'source').glob('*.py'),*(R/'scripts').glob('*.py')]:ast.parse(p.read_text(),filename=str(p))
e=b.parse_cpio(gzip.decompress((R/'artifacts/common-rootfs.cpio.gz').read_bytes()))
for n in ['os-rescue','rescue-sd','rescue-sd-supervisor','p10-restore']:
 d=(R/'artifacts'/n).read_bytes();b.elf_static(d);assert struct.unpack_from('<H',d,16)[0]==2;assert e['sbin/'+n][3]==d
for n in ['sepolicy','file_contexts.bin']:assert e[n][3]==(R/'artifacts'/n).read_bytes()
assert e['init'][3]==(R/'inputs/init').read_bytes()
assert e['rescue.original.manifest']==(0o100444,0,0,(R/'inputs/original-stock.manifest').read_bytes())
assert b.sha(e['rescue.original.manifest'][3])=='605cdec038dafe3dddabfe92b8bd6cd189734f740230dfc362d02a43421e4e47'
assert not any(n in e for n in ['rescue.manifest','rescue.sd.arm','rescue.current.binding','system/bin/sh','sbin/adbd'])
rc=e['init.rc'][3].decode();assert rc.count('socket os_rescue_control stream 0600 root root')==1 and rc.count('socket os_rescue stream 0600 shell shell')==1
assert 'start rescue-sd-offline' not in rc and 'oneshot' in rc and 'on init' in (R/'source/init.offline.action.rc').read_text()
assert 'terminal_manifest_binding.h' not in '\n'.join(p.read_text() for p in (R/'source').glob('*') if p.suffix in ['.h','.c'])
spec=importlib.util.spec_from_file_location('join',R/'scripts/final_package.py');join=importlib.util.module_from_spec(spec);spec.loader.exec_module(join)
try:join.five_roles((R/'inputs/original-stock.manifest').read_bytes())
except ValueError:pass
else:raise AssertionError('normal final join accepted original pair')
for name in ['rescue.c','sd_frontend.c','supervisor.c']:
 (R/'evidence'/(name+'.patch')).write_text(''.join(difflib.unified_diff((old/'source'/name).read_text().splitlines(True),(R/'source'/name).read_text().splitlines(True),fromfile='completed-core/'+name,tofile='offline-stock/'+name)))
art={n:dict(bytes=(R/'artifacts'/n).stat().st_size,sha256=b.sha((R/'artifacts'/n).read_bytes())) for n in ['os-rescue','rescue-sd','rescue-sd-supervisor','p10-restore','sepolicy','file_contexts.bin','common-rootfs.cpio.gz']}
(R/'artifacts/ARTIFACTS.json').write_text(json.dumps(art,indent=2)+'\n')
receipt=dict(passed=True,normal_writer_session_and_guards_unchanged=True,normal_client_source_readback_status_phase_bodies_unchanged=True,restore_core_unchanged=True,actual_static_ELFs=4,actual_common_archive_matches_products=True,original_pair_manifest_genuine=True,missing_final_authorities_do_not_auto_start=True,normal_final_join_rejects_original_pair=True,no_missing_production_binding_header=True,real_final_assembly_executed=False,physical_boot_sd_selinux_poweroff_verified=False)
(R/'evidence/final-local-check.json').write_text(json.dumps(receipt,indent=2)+'\n');print(json.dumps(art,indent=2))
