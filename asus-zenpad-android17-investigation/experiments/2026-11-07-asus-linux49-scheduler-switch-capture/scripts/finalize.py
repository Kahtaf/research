from pathlib import Path
import hashlib,json,gzip,re,stat,ast
R=Path(__file__).resolve().parents[1];E=R/'evidence';P=R.parent/'2026-11-07-asus-linux49-rdma-registration-skip'
sha=lambda b:hashlib.sha256(b).hexdigest()
p=json.loads((E/'packaging-receipt.json').read_text());build=json.loads((E/'build-receipt.json').read_text());linked=json.loads((E/'linked-capture.json').read_text());identity=json.loads((E/'identity.json').read_text());u=identity['run_uuid']
assert json.loads((E/'after.stdout').read_text())['status']=='TERMINATED'
assert json.loads((E/'install-plan.json').read_text())['mode']=='PLAN_ONLY'
assert json.loads((E/'encoding-controls.json').read_text())['status']=='PASS'
assert linked['status']=='PASS_SCOPED_SOURCE_AND_ACTUAL_ELF'
assert json.loads((E/'build-status.json').read_text())['compile_attempts']==1
assert (R/'scripts/decode.py').read_bytes()==(P/'scripts/decode.py').read_bytes()
assert stat.S_IMODE((R/'source/adb').stat().st_mode)==0o755
mapgz=(R/'artifacts/System.map.gz').read_bytes();mapraw=gzip.decompress(mapgz)
assert len(mapgz)<1000000 and sha(mapraw)==build['artifacts']['System.map']['sha256']
assert sha((R.parent/'2026-11-06-asus-product-input-build-kit/scripts/remote.py').read_bytes())=='c22884576a780cbb1ddf5e1b02f0b6e9d6eb5c25f8d9bc82fb077543f05cf4ab'
for name,key in [('candidate.img','candidate'),('candidate.p10.raw','full_p10')]:assert sha((R/'artifacts'/name).read_bytes())==p[key]['sha256']
s=(E/'scoped-hooks.disasm').read_text();finish=s[s.index('<finish_task_switch>:'):];finish=finish[:finish.index('\n\n')]
sw=s[s.index('<asus_capture_switch>:'):];sw=sw[:sw.index('\n\n')]
header=s[s.index('<sw_header>:'):];header=header[:header.index('\n\n')]
assert not re.search(r'\bmsr\b',sw+header)
abi=dict(status='PASS',source_safe_point='exact original prev_state = prev->state snapshot; next statement is capture; precedes vtime/perf, finish_lock_switch, prev on_cpu clear and lifetime changes',finish_task_switch_address=linked['symbols']['finish_task_switch']['address'],hook_call_offset='0x54',prev_state_load_offset='0x4c',prev_on_cpu_clear_offset='0x84',original_rq_unlock_call_offset='0x8c',ABI=dict(x0='prev pointer (saved in x20)',x1='exact local prev_state (loaded from prev+24 into x23, then moved to x1)',saved_state_retained='x23 subsequently tested against TASK_DEAD'),recorder=linked['symbols']['asus_capture_switch'],recorder_stack_bytes=432,metadata_writer_stack_bytes=320,raw_read='one isb; mrs cntvct_el0; no arch_counter_read or timekeeping call',context='ready + nr_cpu_ids==1 + raw CPU==0 + DAIF.I set + !in_interrupt(); fail sticky admission loss otherwise',preempt_count='actual recorded at hook; original scheduler WARN/correction precedes hook unchanged; decoder requires 2',no_DAIF_write_in_recorder_or_metadata=True,normal_calls='cache clean with actual dsb sy, byte memset, sw_header; no indirect recorder calls or locks',compiler_guard=linked['compiler_stack_protector'],physical_verified=False)
(E/'hook-abi.json').write_text(json.dumps(abi,indent=2)+'\n')
layout=dict(version='A49SW1',capture_UUID=u,relative_to_legacy_start=5952,legacy_bytes=5952,switch_bytes=3008,combined_bytes=8960,console_position='ALIGN(existing log_size,64); existing OEM console offset must be cache-line aligned',reservation='cap_init under original trace_lock checks pos<=sz_console and combined<=sz_console-pos before any capture writes; reserves entire combined area by single log_size commit; readiness published last; append writer unchanged and starts at committed log_size',mapping_and_hardware_reservations='unchanged guarded OEM normal-cacheable retained console 0x44400000..0x44480000; no arbitrary memory',rows=10,ring_rows=8,row_bytes=256,fixed_PID1_out_slot=8,fixed_PID1_in_slot=9,offsets=dict(identity=0,metadata=64,sticky_faults=256,begin_guard=320,rows=384,end_guard=2944),row_fields=['sequence','raw_cntvct','prev_pid','prev_state_bits','next_pid','next_prio','next_policy','prev_prio','preempt_count','context_cpu_shift32_IRQdisabled_bit0','capture_serial_anchor'],comm='16 bytes hex at offset196 (32 ASCII), including NULs',generation='sequence at row+9 and row+232; metadata total+1 at +9 and +160; every numeric field 16 lowercase hex digits',commit='invalid marker ! cleaned to PoC+dsb before payload; payload with matching generation/tail cleaned+dsb; V marker cleaned+dsb last; cross-record consistency validated by decoder',sticky_fields='loss + independent guard,busy,admission,overflow flags, each monotonic 0->1; own64-byte line; no shared trace_lock under rq lock',preinitialization='no switch observation until sw_area release publication; absence before ready is not counted or interpreted',bounds='metadata total/first/last/retained_count/wraps; fixed latest PID1 slots cannot be erased by ring wrap; overflow latches loss and stops',retention='bounded append freezes at OEM console capacity, preserving early markers and both fixed capture areas')
(E/'switch-layout.json').write_text(json.dumps(layout,indent=2)+'\n')
warn=[l for l in (E/'compile-1.log').read_text().splitlines() if 'warning:' in l]
limits=[
 'Diagnostic only. Build/source/ELF/host/PLAN checks establish no physical or fullOS GO.',
 'Physical4.9 real PID1 is prior-proven. The old finite helper loop stopped after its initial 0.646s sample with no aftercounts/SIGALRM marker; completed historical hooks do not prove continued IRQ activity after the latest snapshot.',
 'Switch-to-PID1 is kernel task selection, not proof of userspace execution. No resumption in a finite ring/fixed snapshot is not permanent starvation.',
 'No switch after an anchor is finite captured absence only; it does not establish a softirq wedge, clock-core fault, IRQ delivery or named culprit.',
 'An admitted last PID1-out newer than last PID1-in can bound absence of observed return only through total; it cannot extrapolate beyond final captured switch.',
 'Direct CNTVCT samples and cap_serial anchors support finite chronology; they do not turn cached LASTPC into this boot epoch or prove clock correctness.',
 'Cached PMIC-ADC reset PC epoch remains UNESTABLISHED. No PMIC change or follow-up build is authorized by this handoff.',
 'Encoding/cache-clean work under rq lock perturbs latency and can change timing.',
 'Missing/torn/dropped/nonadmitted capture is UNKNOWN; no automatic retry or next build. Parent interprets after one physical trial only.'
]
commands=dict(PLAN=f'python3 -B {R}/source/install.py',decode_legacy=f'python3 -B {R}/scripts/decode.py /absolute/path/to/parent-complete-console.txt --uuid {u}',decode_switch=f'python3 -B {R}/scripts/decode_switch.py /absolute/path/to/parent-complete-console.txt --uuid {u}')
handoff=dict(status='DELIVERED_ONE_DIAGNOSTIC_SCHEDULER_SWITCH_CAPTURE',physical_GO=False,fullOS_GO=False,physical_trial=False,VM_status='TERMINATED',VM=dict(project='PROJECT_REDACTED',zone='us-central1-a',instance='PROJECT_REDACTED',id='8549823276971553556'),remote_root='/srv/android/asus-linux49-scheduler-switch-capture-20261107-3d26cc95',base_remote_root='/srv/android/asus-linux49-rdma-registration-skip-20261107-d140b2bf',capture_UUID=u,helper_UUID=p['helper_uuid'],candidate=p['candidate'],full_p10=p['full_p10'],admitted_current_full_p10=p['admitted_current_full_p10'],current_preimage_supplied_not_read=True,compiled_Image_gz_dtb=p['compiled_Image_gz_dtb'],raw_Image=p['raw_Image'],System_map=dict(uncompressed=build['artifacts']['System.map'],gzip=dict(bytes=len(mapgz),sha256=sha(mapgz)),uncompressed_verified_locally=True,vmlinux='VM only'),config=p['config'],preservation=p['preservation'],compile_attempts=1,max_jobs=8,warnings=len(warn),compiler_corrections=0,verification_checker_corrections=2,checker_failure_receipts=['verify-1-verify.stderr','verify-2-verify.stderr'],default_PLAN_calls=1,PLAN_isolation='truthful in-memory restricted public readers only; delivered guards intact',commands=commands,expected_markers=[f'ASUS49-ENTRY run={u}',f'A49CAP1 uuid={u} rows=15 row=384 fields=17 header=192','A49FAULT 0',f'A49SW1 uuid={u}','VA49SH   <matching generation/metadata/tail>','A49SLOSS 0 guard=0 busy=0 admission=0 overflow=0',f'A49SGUARD BEGIN {u}',f'A49SGUARD END   {u}','VA49S 00..09 <valid matching sequence/tail>','ASUS49-DIAG headless RDMA IRQ registration skipped module=2 name=rdma0 linux_irq=<runtime mapped IRQ>','ASUS49-DIAG headless RDMA IRQ registration skipped module=3 name=rdma1 linux_irq=<runtime mapped IRQ>'],capture_layout=layout,hook_ABI=abi,limits=limits,no_device_or_private_access=True,no_execute=True,no_next_build=True)
(E/'handoff.json').write_text(json.dumps(handoff,indent=2)+'\n')
(R/'README.md').write_text(f'''# Diagnostic scheduler-switch capture

Question: what finite task-switch observations surround the unchanged PID1 helper boundary?

Status: **ONE candidate built and packaged; VM verified TERMINATED.** Parent owns one authorized physical trial, eventual manual Power fallback, collection and interpretation. No device/ADB/root/private factory/raw target-log access occurred. No `--execute`, physical/fullOS GO, automatic UNKNOWN retry or next build.

- [candidate.img](artifacts/candidate.img): {p['candidate']['bytes']} bytes, SHA-256 `{p['candidate']['sha256']}`.
- [candidate.p10.raw](artifacts/candidate.p10.raw): {p['full_p10']['bytes']} bytes, SHA-256 `{p['full_p10']['sha256']}`.
- Whole entry/legacy/switch capture UUID: `{u}`. Helper UUID stays `{p['helper_uuid']}`.
- [System.map.gz](artifacts/System.map.gz): {len(mapgz)} bytes, SHA-256 `{sha(mapgz)}`. Its {len(mapraw)}-byte uncompressed content was verified locally, SHA-256 `{sha(mapraw)}`. `vmlinux` remains VM-only.
- Exact pins, commands, ABI, bounds and limits: [handoff.json](evidence/handoff.json). [Patch](source/changes.patch), [source pre/posts](evidence/source-pins.json), [preservation/packaging](evidence/packaging-receipt.json), [ELF receipt](evidence/linked-capture.json), [disassembly](evidence/scoped-hooks.disasm), [ABI](evidence/hook-abi.json), [layout](evidence/switch-layout.json), [host controls](evidence/encoding-controls.json).

`finish_task_switch()` calls the recorder immediately after its original `prev_state = prev->state` assignment, before `vtime_task_switch`, perf, `finish_lock_switch`, clearing `prev->on_cpu`, or freeing `prev`. Actual ELF passes `prev` in x0 and the saved long state in x1 at `finish_task_switch+0x54`; `prev->on_cpu` clears at +0x84 and original rq unlock calls at +0x8c. Reads of previous PID/priority and all current task fields finish before returning to that unchanged lifetime path. The original preempt-count warning/correction precedes the seam unchanged; recorded preempt count is the actual value at this seam.

The recorder admits only readiness + `nr_cpu_ids==1`, CPU0, IRQs disabled and task context. It neither acquires `trace_lock` nor changes IRQ masks, policy, priority, preemption behavior or routing. Actual ELF has one direct CNTVCT register read after ISB, no indirect recorder call or clock subsystem call, and no DAIF write. Normal calls are byte memset, cache clean and the private metadata writer; the inherited stack protector retains its canary-failure-only `__stack_chk_fail` branch. The cache-clean helper ends in actual `dsb sy`. No printk, allocation, scheduling, sleeping or dynamic memory is added to ordinary hook execution. Synchronous encoding and cache cleaning under rq lock can perturb timing.

Each 256-byte ASCII record holds sequence, raw counter, previous PID/exact saved state, next/current PID, next effective priority and policy, previous priority, preempt count, CPU/IRQ admission and the existing capture-serial anchor, plus all 16 current comm bytes as hex. Eight latest-switch rows wrap; slots8/9 separately retain the latest observed PID1-out/in through `total`. No shared raw spinlock is introduced under rq lock. Calls before readiness are outside the observation horizon. Post-ready admission, reentry, guard and overflow failures latch independent sticky loss.

The old 15 rows/5952 bytes and old decoder are preserved. `cap_init` checks actual OEM console bounds for **8960 combined bytes** before writes, places the new 3008 bytes immediately after the old capture, cleans/publishes the combined log-size reservation, then publishes readiness. Original mapping, DT/reservation guards and append writer remain intact. Both guard cache lines, UUID, total/first/last/wrap/count metadata, all rows and matching generation/tails are checked by the new decoder. Payload publication is invalid-before-write, clean-to-PoC+barrier, then valid marker; inconsistent cross-record snapshots fail UNKNOWN. A full append buffer still freezes instead of overwriting early capture.

The independent source/output copy uses `cp -a --reflink=auto`; scoped inodes differ and frozen repositories/artifacts remain unchanged. The four edited source files are scheduler core, recorder, recorder declarations and entry/capture metadata. Existing clock/counter/timer function bodies/hooks and RDMA skip source were preserved. Config SHA remains `{p['config']['sha256']}`. Runtime and compiled hardware DT, whole wrapped ramdisk/helper, initrd geometry, mappings, bootargs and installer `execute`/`Transport`/`Guard`/adapters are byte-identical. Source `adb` is 0755. Installer changes only exact hashes, actual length, profile and appended current full-p10 `{p['admitted_current_full_p10']}` supplied by parent, not read here.

```text
{p['bootargs']}
```

Base: `/srv/android/asus-linux49-rdma-registration-skip-20261107-d140b2bf/{{kernel,out}}`. Owned output: `/srv/android/asus-linux49-scheduler-switch-capture-20261107-3d26cc95`. One `make -j8 Image.gz-dtb` passed with {len(warn)} warning lines retained; no compile corrections, no full-tree audit, no product/AOSP work. Two checker corrections (memory alias/stack-canary classification; unrelated perf `sw_*` selector) and their failures are preserved; candidate source was unchanged. Readiness, build and fetch used one owned persistent SSH master with TCP fallback disabled for channels. It was closed after successful fetch; [final VM state](evidence/after.stdout) is TERMINATED.

Exactly one actual default installer PLAN passed with restricted public dependency readers substituted only in memory. [Isolation receipt](evidence/plan-isolation-receipt.json) states what was and was not checked. Delivered guards and readers remain intact. Parent PLAN command:

```sh
{commands['PLAN']}
```

After the parent's ONE physical trial and established complete-console collection, decode locally (paths are placeholders; no raw private console was opened here):

```sh
{commands['decode_legacy']}
{commands['decode_switch']}
```

Expected readiness/guard evidence: fresh `ASUS49-ENTRY`, `A49CAP1` and `A49SW1` UUIDs; `A49FAULT 0`; canonical committed `VA49SH` metadata; `A49SLOSS 0 guard=0 busy=0 admission=0 overflow=0`; both UUID-bound `A49SGUARD BEGIN/END` lines; ten complete `VA49S` rows with matching sequence/tails; and the two unchanged RDMA skip lines. Their Linux IRQ values must come from runtime (prior physical trial verified237/238). Parent still requires exact full-p10 readback and the established physical identity/geometry guards. Missing/torn/dropped/nonadmitted data is UNKNOWN; stop for interpretation, without automatic retry.

An admitted decode reports only finite switch order, current task identity/comm/effective priority/policy and saved previous state, ring horizon and latest PID1 transitions. An observed PID1 switch-in establishes kernel selection; it does not establish userspace return. Fixed PID1-out newer than fixed PID1-in can establish absence of a later **observed** switch-in through captured `total`, not permanent starvation. Neither absent switches nor completed historical IRQ rows establishes a permanent wedge or continued later IRQ delivery. No clock-core fault, PMIC issue, named culprit or fix follows automatically. The cached PMIC-ADC reset PC epoch remains UNESTABLISHED and is not pursued.

Continuation: parent performs only its one authorized trial, interprets admitted evidence, and stops. This candidate is diagnostic observation only. Do not make a next build from this handoff.
''')
paths=[p for n in ['source','scripts','artifacts'] for p in (R/n).rglob('*') if p.is_file() and '__pycache__' not in p.parts]
paths += [R/'README.md']+[E/n for n in ['handoff.json','hook-abi.json','switch-layout.json','linked-capture.json','encoding-controls.json','packaging-receipt.json','install-plan.json','plan-isolation-receipt.json','after.stdout']]
(E/'delivery-pins.json').write_text(json.dumps({str(p.relative_to(R)):dict(bytes=p.stat().st_size,sha256=sha(p.read_bytes())) for p in sorted(paths)},indent=2)+'\n')
print(json.dumps({k:handoff[k] for k in ['status','VM_status','capture_UUID','candidate','full_p10','compile_attempts','default_PLAN_calls']},indent=2))
