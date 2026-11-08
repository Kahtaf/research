from pathlib import Path
import hashlib,json,stat,gzip,shutil,difflib
R=Path(__file__).resolve().parents[1];B=R.parent/'2026-11-08-asus-arm64-delay-loop-observation'
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
read=lambda n:json.loads((R/'evidence'/n).read_text())
save=lambda n,d:(R/'evidence'/n).write_text(json.dumps(d,indent=2)+'\n')
i=read('identity.json');u=i['run_uuid'];p=read('packaging-receipt.json');linked=read('linked-capture.json');status=read('build-status.json');route=read('route-proof.json')
assert status['status']=='complete' and status['compile_attempts']==1 and status['max_jobs']==8
assert read('controls.json')['status']=='PASS_FOCUSED_WRITER_AND_ROUTE_CONTROLS' and read('decoder-controls.json')['status']=='PASS'
assert read('plan-isolation-receipt.json')['actual_installer_main_calls']==1 and route['status']=='PASS_ACTUAL_ELF_ROUTES'
assert read('after.stdout')['status']=='TERMINATED' and not (R/'s').exists()
remote=R.parent/'2026-11-06-asus-product-input-build-kit/scripts/remote.py';assert sha(remote)=='c22884576a780cbb1ddf5e1b02f0b6e9d6eb5c25f8d9bc82fb077543f05cf4ab'
for n,k in [('candidate.img','candidate'),('candidate.p10.raw','full_p10'),('Image.gz-dtb','compiled_Image_gz_dtb'),('resolved.config','config')]:assert sha(R/'artifacts'/n)==p[k]['sha256']
rawmap=gzip.decompress((R/'artifacts/System.map.gz').read_bytes());assert hashlib.sha256(rawmap).hexdigest()==read('build-receipt.json')['artifacts']['System.map']['sha256'];assert rawmap==(R/'artifacts/System.map').read_bytes()
m=dict(status='PASS_GENUINE_VM_MAP',compressed_sha256=sha(R/'artifacts/System.map.gz'),uncompressed=dict(bytes=len(rawmap),sha256=hashlib.sha256(rawmap).hexdigest()),vmlinux_fetched=False,out_fetched=False);save('System.map-uncompressed.json',m)
decoders={}
for n in ['decode.py','decode_switch.py','decode_work.py','decode_power.py','decode_pmic.py']:
 assert (R/'scripts'/n).read_bytes()==(B/'scripts'/n).read_bytes();decoders[n]=sha(R/'scripts'/n)
save('preserved-decoders.json',decoders)
(R/'protocols').mkdir(exist_ok=True)
for n in ['power.md','pmic.md']:shutil.copy2(B/'protocols'/n,R/'protocols'/n)
shutil.copy2(B/'protocol.md',R/'protocols/delay-v1.md')
for n in ['bootformat.py','fdt.py','adb','legacy_adb.py']:assert (R/'source'/n).read_bytes()==(B/'source'/n).read_bytes()
assert stat.S_IMODE((R/'source/adb').stat().st_mode)==0o755
# Recheck the complete installer text, not just selected methods.
a=(B/'source/install.py').read_text();z=(R/'source/install.py').read_text()
pre=next(l for l in a.splitlines() if l.startswith('INSTALL_PREIMAGES='))
changes={"IMAGE_SHA='"+p['base_candidate']['sha256']+"'":"IMAGE_SHA='"+p['candidate']['sha256']+"'","FULL_SHA='"+p['admitted_current_full_p10']+"'":"FULL_SHA='"+p['full_p10']['sha256']+"'",'len(image)==7989248':'len(image)=='+str(p['candidate']['bytes']),'exact-arm64-delay-loop-f3da846c-r1':'exact-selected-cntpct-2ac3b1e4-r1',pre:pre[:-1]+",'"+p['admitted_current_full_p10']+"')"}
# Equal image length is valid: it is still a permitted, identical literal.
for before,after in reversed(list(changes.items())):assert z.count(after)==1;z=z.replace(after,before)
assert z==a
(R/'source/install.diff').write_text(''.join(difflib.unified_diff(a.splitlines(True),(R/'source/install.py').read_text().splitlines(True),fromfile='base/source/install.py',tofile='candidate/source/install.py')))
save('preservation.json',dict(status='PASS_SCOPED_PRESERVATION',changed_kernel_files=list(read('source-pins.json')),source_reverse_check=read('source-checks.json'),base_inodes_and_nested_repository_scope='base-freeze.json / repository-preservation.json',config=p['config'],entire_wrapped_ramdisk=p['ramdisk'],runtime_DT=p['runtime_DTB'],compiled_DT=p['compiled_DTB'],initrd=p['initrd'],load_layout=p['layout'],old_capture_bytes=26752,delay_area_bytes=2560,old_five_decoders=decoders,PMIC_operations_phasehooks_RDMA_diagnostics='scoped source pins unchanged plus linked skip marker',preserved_sources=linked['preserved_sources'],execute_Transport_Guard_adapters_byte_identical=True,installer_only_changes=['hashes','profile','length','append parent supplied current preimage'],adb_mode='0755',charging_DT_permission='ABSENT; unchanged actual DT',remote_py_sha256=sha(remote),physical_trial=False))
save('prepost.json',dict(base_remote=i['base_remote_root'],owned_remote=i['remote_root'],source_prepost=read('source-pins.json'),expected_current_full_p10=p['admitted_current_full_p10'],current_pin='parent supplied; no device observation',candidate=p['candidate'],full_p10=p['full_p10'],base_untouched='repository-preservation.json',config=p['config']))
commands=dict(PLAN=f'python3 -B {R}/source/install.py',parent_one_trial_install=f'python3 -B {R}/source/install.py --execute',decode=f'python3 -B {R}/scripts/decode_delay.py /absolute/path/to/parent-complete-console.txt --uuid {u} > /absolute/path/to/parent-private-delay.json',offline_public_summary=f'python3 -B {R}/scripts/symbolize_delay.py --decoded /absolute/path/to/parent-private-delay.json',build=status['command'],worker_run_scripts=['vm.py start','inspect.py','prepare.py','source_checks.py','dispatch.py','check_controls.py','fetch_verify.py','route_proof.py','check_decoder.py','check_boundaries.py (executed via stdin; persisted equivalent source)','package.py','plan_only.py','vm.py stop','finalize.py'],remote_channel='owned persistent master; -o ControlMaster=no -o ProxyCommand=false; no TCP fallback')
save('exact-commands.json',commands)
limits=['First completed selected physical start proves current access only; backend claim alone proves no access.','Missing start/return is UNKNOWN finite boundary, no automatic trap/stall inference.','Advancing then missing return does not exonerate later reads; stable values do not prove a global counter stop.','Only within selected physical domain subtract from selected start; no PMIC/IRQ virtual cross-domain arithmetic.','Positive clears this exposure and supports read-route hypothesis; timing perturbation remains; no mechanism/production/global-health claim.','ADC POST and RAM PID1 completion are separate parent checks.','Sparse preempt/IRQmask is not IRQ history. Cached old reset PC epoch remains unestablished.','Delivered installer guards intact; isolated PLAN does not validate private stock/root dependency chains.','Parent one physical trial, standing eventual Power fallback; UNKNOWN STOP, consult Large before next guess. No automatic retry/variant/fullOS GO.']
h=dict(status='DELIVERED_ONE_SELECTED_CNTPCT_DELAY_CONTROL_STOP',run_uuid=u,candidate=p['candidate'],full_p10=p['full_p10'],expected_current_full_p10=p['admitted_current_full_p10'],current_pin_supplied_not_freshly_observed=True,base_remote=i['base_remote_root'],owned_remote=i['remote_root'],config=p['config'],System_map=m,helper_uuid=p['helper_uuid'],ramdisk=p['ramdisk'],DT_compiled=p['compiled_DTB'],DT_runtime=p['runtime_DTB'],bootargs=p['bootargs'],initrd=p['initrd'],layout=p['layout'],capture=dict(version='A49DL2',old_bytes=26752,delay_bytes=2560,combined_bytes=29312,header_bytes=192,header_fields=9,header_tail=168,selected_read_domain=dict(before_claim=0,selected_raw_physical=1),other_offsets_unchanged=True,all_matched_samples=True,no_PID119_sample3_gate=True),checks=dict(compile_attempts=1,compiler_corrections=0,actual_ELF='route-proof.json / route-proof.md / delay-loop.disasm',source='source-checks.json / source-pins.json',controls='controls.json / decoder-controls.json',preservation='preservation.json',packaging='packaging-receipt.json',isolated_PLAN='plan-isolation-receipt.json',checker_corrections='checker-corrections.jsonl'),commands=commands,VM=dict(project='PROJECT_REDACTED',zone='us-central1-a',instance='PROJECT_REDACTED',id='8549823276971553556',final='TERMINATED',own_master_closed=True),device_contacted=False,physical_GO=False,full_OS_GO=False,parent_owns_one_physical_trial=True,standing_eventual_Power_fallback=True,limits=limits)
save('handoff.json',h)
(R/'artifacts/SHA256SUMS').write_text(''.join(sha(x)+'  '+x.name+'\n' for x in sorted((R/'artifacts').iterdir()) if x.is_file() and x.name!='SHA256SUMS'))
(R/'README.md').write_text(f'''# Selected CNTPCT delay read-route control

Question: does a raw physical read route allow the strictly selected battery voltage PMIC delay exposure to complete?

Status: **one candidate built and packaged; STOP**. UUID `{u}`. Parent owns one physical trial and eventual Power fallback. Worker contacted no device and ran no installer execute.

- [Candidate](artifacts/candidate.img): {p['candidate']['bytes']} bytes; SHA256 `{p['candidate']['sha256']}`.
- [Full p10](artifacts/candidate.p10.raw): SHA256 `{p['full_p10']['sha256']}`. Expected current full p10 `{p['admitted_current_full_p10']}` is parent supplied.
- [Handoff and exact commands](evidence/handoff.json), [all artifact hashes](artifacts/SHA256SUMS), [genuine System.map.gz](artifacts/System.map.gz), [uncompressed map pins](evidence/System.map-uncompressed.json). vmlinux/out stay on VM.
- [Actual linked route proof](evidence/route-proof.md), [disassembly](evidence/delay-loop.disasm), [source diff](source/changes.patch), [source pre/post](evidence/prepost.json), [preservation](evidence/preservation.json).
- [A49DL2 protocol](protocol.md), [decoder](scripts/decode_delay.py), [offline symbolizer](scripts/symbolize_delay.py), [focused controls](evidence/controls.json), [decoder controls](evidence/decoder-controls.json), [one isolated PLAN](evidence/plan-isolation-receipt.json).

One `make -j8 Image.gz-dtb` passed without compiler corrections. Three kernel files changed. Only a nonzero strictly joined cookie uses inline raw CNTPCT for start and every condition read, each with the original single ISB. It bypasses virtual OOL regardless of key; cookie0 retains original get_cycles direct/OOL. The source loop/arithmetic/capture order restores byte-exact by reversing two call substitutions. A49DL2 adds selected_read_domain in the same2560 bytes; header tail168, every other offset unchanged. All five old decoders/layouts remain exact. Strict generation, identity, publication, loss and refusal semantics remain.

Exact base `{i['base_remote_root']}/{{kernel,out}}` was independently copied using `cp -a --reflink=auto`; scoped base hashes/inodes/nested repositories remain preserved. Config `{i['config_sha256']}`, whole wrapped helper ramdisk, compiled/runtime DT, args, initrd bounds/load maps, PMIC operations/hooks and RDMA diagnostics remain. Charging DT permission remains absent. Installer execute/Transport/Guard/adapters are byte-exact; adb0755. Only package hashes/profile/length/current-preimage append change. The isolated PLAN truthfully substituted public readers only in memory; private dependencies were not validated and delivered guards remain intact.

VM ID8549823276971553556 is verified **TERMINATED**; owned SSH master closed; remote.py SHA unchanged. A pre-copy orchestration path error was preserved and corrected before copy/build; no extra candidate or compile.

Continuation: parent uses the exact commands for one physical trial, keeps numeric pointers/complete console private until offline genuine-map verification, verifies full p10/readback and normal stock return, and retains eventual Power fallback. Completed first selected physical read proves current access only. Selected return, ADC POST, and RAM PID1 completion are separate checks. Missing start/return is UNKNOWN finite boundary. Positive supports the read-route hypothesis with timing perturbation possible; no mechanism/shipping/global-health claim. Advancing then missing return does not exonerate later reads; stable repeated reads do not prove a global counter stop. UNKNOWN STOP; consult Large before another guess. No automatic retry/next variant/fullOS GO.
''')
print(json.dumps(dict(status=h['status'],candidate=p['candidate'],full_p10=p['full_p10'],VM=h['VM']),indent=2))
