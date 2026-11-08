"""Write the one-candidate public handoff from actual receipts; no transport."""
from pathlib import Path
import ast,difflib,hashlib,json,re,stat
R=Path(__file__).resolve().parents[1];E=R/'evidence';A=R/'artifacts';B=R.parent/'2026-11-08-asus-sparse-observer-liveness'
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
load=lambda n:json.loads((E/n).read_text())
save=lambda n,v:(E/n).write_text(json.dumps(v,indent=2)+'\n')
i=load('identity.json');p=load('packaging-receipt.json');build=load('build-status.json');linked=load('watchdog-linked.json');pl=load('plan-isolation-receipt.json');vm=load('after.stdout')
assert build['compile_attempts']==1 and build['status']=='complete' and build['compile_exit']==0
assert pl['actual_installer_main_calls']==1 and pl['device_contacted'] is False
assert vm['status']=='TERMINATED' and vm['id']=='8549823276971553556' and not (R/'s').exists()
remote=R.parent/'2026-11-06-asus-product-input-build-kit/scripts/remote.py';assert sha(remote)=='c22884576a780cbb1ddf5e1b02f0b6e9d6eb5c25f8d9bc82fb077543f05cf4ab'
for n,key in [('candidate.img','candidate'),('candidate.p10.raw','full_p10'),('Image.gz-dtb','compiled_Image_gz_dtb'),('resolved.config','config'),('runtime.dtb','runtime_DTB'),('ramdisk.wrapped','ramdisk')]:
 assert sha(A/n)==p[key]['sha256'] and (A/n).stat().st_size==p[key]['bytes']
assert p['admitted_current_full_p10']=='8ed918339c0adcfdad461390b0316073b515b43e839ec8094975546e314f8b22'
def block(s,name):
 n=next(n for n in ast.parse(s).body if getattr(n,'name',None)==name)
 return ''.join(s.splitlines(True)[n.lineno-1:n.end_lineno])
old=(B/'source/install.py').read_text();new=(R/'source/install.py').read_text()
for n in ['execute','Transport','Guard']:assert block(old,n)==block(new,n)
(R/'source/install.diff').write_text(''.join(difflib.unified_diff(old.splitlines(True),new.splitlines(True),fromfile='sparse-base/source/install.py',tofile='sparse-watchdog/source/install.py')))
for n in ['bootformat.py','fdt.py','adb','legacy_adb.py']:assert (R/'source'/n).read_bytes()==(B/'source'/n).read_bytes()
assert stat.S_IMODE((R/'source/adb').stat().st_mode)==0o755
# Original liveness algorithm is reused verbatim, with identity provided by this spike.
assert (R/'scripts/decode_liveness.py').read_bytes()==(B/'scripts/decode_sparse.py').read_bytes()
tag=(R/'source/arch/arm64/kernel/asus_entry_tag.h').read_text().splitlines()[0]
entry=json.loads(tag.split(' ',2)[2]).rstrip('\n')
contract=dict(run_uuid=i['run_uuid'],entry_line=entry,mode=i['mode'],watchdog_prefix=i['watchdog_prefix'],canonical_tails=[
 'event=probe route=mtk_wdt_probe caller=<16 lowercase hex LR>',
 'event=error site=<alloc|map|watchdog_register|reboot_notifier|restart_handler|pm_notifier|reset_controller> rc=<nonzero signed decimal>',
 'event=stop before=<8 lowercase hex> after=<8 lowercase hex> en_before=<0|1> en_after=<0|1> caller=<16 lowercase hex LR>',
 'event=probe_done rc=0 req_mode=<8 lowercase hex> req_irq_en=<8 lowercase hex>',
 'event=restart route=mtk_reset_handler caller=<16 lowercase hex LR>'],
 success_messages='probe entry, original stop before/after, probe_done snapshot; restart one message per entry; errors only on existing active error/warning branches',
 IRQ='IRQ/FIQ failure blocks disabled by #if 0 in exact source/ELF; no invented active error branch',
 filter='only exact fresh watchdog prefix added to inherited bounded printable-ASCII whitelist; newline allowed only as final character; old helper suffixes unchanged',
 helper_prefix=i['helper_prefix'],helper_event_suffixes=i['helper_event_suffixes'],helper_alarm_suffix=i['helper_alarm_suffix'],direct_markers=i['direct_markers'],
 emitter='288-byte stack buffer, bounded scnprintf, existing direct retained writer; no printk/timekeeping/MMIO/allocation/sleep/recorder self-hook; compiler existing stack protector has canary-failure edge',
 sink='unchanged trylock/guard/mapping/cache payload+header PoC cleans with DSB SY. Refusal/drop/tear/perturbation possible. No sink lock spans original hardware operations.',
 watchdog_admission='exact full compiled entry and mode identity plus canonical fresh watchdog records; independent of helper/PID1/loop outcome; source-pin and map contract belong to this image',
 caller='Raw LR remains parent-private. Optional candidate-pinned System.map[.gz] resolves LR-4 to named immediate caller/callsite. No original-requester or preloader-producer inference.',
 meaning='EN0/EN1 only readback at that instant, not write-caused change, stop acceptance, reset-agent exoneration or deadline identity. probe_done rc0 is original probe return including possible deferred registration.',
 absent='RECORD_ABSENT, never proof never called or no software reset; liveness stays a separate outcome including UNKNOWN_STOP',
 old_six_protocols='deliberately absent; never claimed passing',physical_admission='parent independently binds complete installed full-p10 readback and fresh stock boot; no parser substitutes for these')
save('mode-contract.json',contract)
commands=dict(PLAN=f'python3 -B {R}/source/install.py',parent_one_trial_install=f'python3 -B {R}/source/install.py --execute',parser=f'python3 -B {R}/scripts/decode_sparse.py /absolute/parent-private/complete-console.txt --system-map {R}/artifacts/System.map.gz > /absolute/parent-private/sparse-wdt-result.json',map_pin=f"python3 -B -c 'import gzip,hashlib; from pathlib import Path; d=gzip.decompress(Path(\"{R}/artifacts/System.map.gz\").read_bytes()); print(len(d),hashlib.sha256(d).hexdigest())'",build_already_completed_once=build['command'],limit='Commands for parent review only. This worker ran one isolated PLAN; no execute/device/physical/fullOS GO. No repeat build or automatic trial.')
save('exact-commands.json',commands)
save('prepost.json',dict(source=load('source-pins.json'),old_candidate=p['base_candidate'],new_candidate=p['candidate'],old_full_p10=p['admitted_current_full_p10'],new_full_p10=p['full_p10'],old_Image_gz_dtb=load('base-inspection.json')['image_sha256'],new_Image_gz_dtb=p['compiled_Image_gz_dtb'],old_and_new_config=p['config'],old_and_new_compiled_DT=p['compiled_DTB'],old_and_new_runtime_DT=p['runtime_DTB'],old_and_new_ramdisk=p['ramdisk'],old_and_new_helper=p['init'],lengths_unchanged=True,parent_current_pin_supplied_not_freshly_observed=True))
preservation=dict(**p['preservation'],helper=p['init'],config=p['config'],compiled_DT=p['compiled_DTB'],runtime_DT=p['runtime_DTB'],ramdisk=p['ramdisk'],args=p['bootargs'],initrd=p['initrd'],layout=p['layout'],charging_permission='unchanged ABSENT via entire DT byte equality',original_driver_tokens_after_observation_removal_identical=load('local-controls.json')['original_driver_tokens_after_observation_removal_identical'],original_liveness_parser_bytes_identical=True,sparse_hot_readiness='six zero BSS pointers, zero STLR ready publications in both exact base and candidate',sparse_writer_byte_identical=True,RDMA_skip_preserved=True,remote_py_sha256=sha(remote))
save('preservation.json',preservation)
handoff=dict(status='DELIVERED_ONE_SPARSE_WATCHDOG_OBSERVATION_CANDIDATE_STOP',run_uuid=i['run_uuid'],candidate=p['candidate'],full_p10=p['full_p10'],expected_current_full_p10=p['admitted_current_full_p10'],current_pin_supplied_not_freshly_observed=True,base_remote=i['base_remote'],owned_remote=i['remote_root'],mode=i['mode'],watchdog_prefix=i['watchdog_prefix'],config=p['config'],helper=p['init'],ramdisk=p['ramdisk'],compiled_DT=p['compiled_DTB'],runtime_DT=p['runtime_DTB'],bootargs=p['bootargs'],initrd=p['initrd'],layout=p['layout'],System_map=load('System.map-uncompressed.json'),source_pins=load('source-pins.json'),source_ELF_proof=['register-qualification.json','watchdog-linked.json','linked-capture.json','source-checks.json','repository-preservation.json','scoped-linked.disasm','watchdog-object.disasm'],verification=dict(kernel_compile_attempts=1,jobs=8,compile_corrections=0,isolated_PLAN_calls=1,controls='local-controls.json + map-parser-controls.json',preserved_failures=['control-correction.txt','elf-check-1.stderr','elf-check-correction.txt','register-check-correction.txt']),VM=dict(id=vm['id'],project='PROJECT_REDACTED',zone='us-central1-a',name='PROJECT_REDACTED',final='TERMINATED',own_master_closed=True,remote_py_sha256=sha(remote),new_assets=False,credential_changes=False),commands=commands,limits=['No device/ADB/root/private factory/raw target-log/execute contact or physical trial','One parent trial and accepted eventual Power fallback; parent separately binds full readback and new stock boot','No retry/next unit/watchdog fix/GIC build/physical/fullOS GO','Watchdog facts are observation only; separate liveness may remain UNKNOWN','Preloader decimal32 is not qualified raw RGUSTATUS; cached __delay+212 epoch unestablished','Dispatch-to-stock estimate32.450876s includes firmware and is not candidate uptime','Sparse sink may fail or perturb; no absence-to-never-called inference','Isolated PLAN substituted only restricted public readers in memory; private stock/root chains not validated; delivered guards unchanged','large out/vmlinux stay on existing stopped VM'])
save('handoff.json',handoff)
for directory in [A]:
 (directory/'SHA256SUMS').write_text(''.join(f'{sha(f)}  {f.name}\n' for f in sorted(directory.iterdir()) if f.is_file() and f.name!='SHA256SUMS'))
print(json.dumps(dict(status=handoff['status'],candidate=p['candidate'],full_p10=p['full_p10'],VM=vm['status']),indent=2))
