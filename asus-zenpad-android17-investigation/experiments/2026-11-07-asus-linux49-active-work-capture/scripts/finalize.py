from pathlib import Path
import hashlib,json,gzip,stat,difflib
R=Path(__file__).resolve().parents[1];E=R/'evidence';B=R.parent/'2026-11-07-asus-linux49-scheduler-switch-capture'
sha=lambda b:hashlib.sha256(b).hexdigest()
read=lambda n:json.loads((E/n).read_text())
write=lambda n,d:(E/n).write_text(json.dumps(d,indent=2)+'\n')
p=read('packaging-receipt.json');build=read('build-receipt.json');linked=read('linked-capture.json');identity=read('identity.json');ctx=read('context.json');u=identity['run_uuid'];abi=read('hook-abi.json')
assert read('after.stdout')['status']=='TERMINATED'
assert read('install-plan.json')['mode']=='PLAN_ONLY'
assert read('encoding-controls.json')['status']=='PASS'
assert linked['status']=='PASS_SCOPED_SOURCE_AND_ACTUAL_ELF'
assert read('build-status.json')['compile_attempts']==1 and read('build-status.json')['compile_exit']==0
assert abi['status']=='PASS'
assert (R/'scripts/decode.py').read_bytes()==(B/'scripts/decode.py').read_bytes()
assert stat.S_IMODE((R/'source/adb').stat().st_mode)==0o755
mapgz=(R/'artifacts/System.map.gz').read_bytes();mapraw=gzip.decompress(mapgz)
assert sha(mapraw)==build['artifacts']['System.map']['sha256']
assert sha((R.parent/'2026-11-06-asus-product-input-build-kit/scripts/remote.py').read_bytes())=='c22884576a780cbb1ddf5e1b02f0b6e9d6eb5c25f8d9bc82fb077543f05cf4ab'
for name,key in [('candidate.img','candidate'),('candidate.p10.raw','full_p10')]:assert sha((R/'artifacts'/name).read_bytes())==p[key]['sha256']
layout=dict(version='A49SW2',capture_UUID=u,relative_to_legacy_start=5952,legacy_bytes=5952,switch_bytes=3648,combined_bytes=9600,rows=10,ring_rows=8,row_bytes=320,fixed_PID1_out_slot=8,fixed_PID1_in_slot=9,offsets=dict(identity=0,metadata=64,sticky_faults=256,begin_guard=320,rows=384,end_guard=3584),row_fields=['sequence','raw_cntvct','prev_pid','prev_state_bits','next_pid','next_prio','next_policy','prev_prio','preempt_count','context','capture_serial_anchor','current_func','current_work','worker_flags'],field_encoding='14 fields, each 16 lowercase hex digits separated by a space, at row+9+i*17',new_fields=dict(current_func=196,current_work=213,worker_flags=230),comm='16 raw comm bytes as 32 hex at +248..279',generation='sequence at +9..24 and tail +288..303; newline at +319; metadata generation total+1 at +9 and +160',worker_flags=dict(bit0='explicit PF_WQ_WORKER',bit1='own current_wq_worker non-NULL',valid_values=[0,1,3],no_worker='both pointers zero unless bit1 set',null_function='no active function at this seam; later work remains possible'),reservation='unchanged cap_init runtime check pos<=sz_console and CAP_SIZE+SW_SIZE<=sz_console-pos, before any capture writes; combined log_size committed/cleaned before readiness; unchanged append writer',mapping='unchanged guarded OEM normal-cacheable console 0x44400000..0x44480000; actual admitted h->sz_console determines available capacity',commit='invalid marker cleaned; whole payload with matching generation/tail cleaned+dsb sy; valid marker cleaned last; no new lock',faults='unchanged separate monotonic loss/guard/busy/admission/overflow latches; partial or torn latch rejected',preinit='unchanged readiness: calls before sw_area publication do not record and lie outside observation horizon',decoder='rejects wrong protocol, adjacency/combined span/guards, malformed fields/validity, partial loss, torn generations, ring/fixed disagreement, chronology and serial anchor horizon')
write('switch-layout.json',layout)
commands=dict(PLAN=f'python3 -B {R}/source/install.py',decode_legacy=f'python3 -B {R}/scripts/decode.py /absolute/path/to/parent-complete-console.txt --uuid {u}',decode_switch=f'python3 -B {R}/scripts/decode_switch.py /absolute/path/to/parent-complete-console.txt --uuid {u}',symbolize=f'python3 -B {R}/scripts/symbolize.py --decoded /absolute/path/to/parent-private-switch.json')
limits=['Diagnostic candidate only; no physical/fullOS GO, execute, target contact or next build.', 'Current active function ownership at this seam is the only new question. No work pointer/function dereference, pwq/name walk, process_one_work hook, timer/PMIC/driver/policy/frequency change.', 'NULL current_func with worker present means no active function at this seam; does not exclude later work.', 'An active function does not establish culprit, permanent starvation, scheduler failure, or execution after finish_task_switch.', 'Before-ready calls are outside the horizon; missing/torn/lost/nonadmitted data is UNKNOWN, no automatic retry.', 'Synchronous encoding and cache cleaning under the existing rq lock can perturb timing.', 'Raw actual pointer output remains parent-private until offline symbolization; no target logs were read.', 'Parent owns one physical trial, eventual manual fallback, exact identity/geometry/readback checks and interpretation.']
warn=[l for l in (E/'compile-1.log').read_text().splitlines() if 'warning:' in l];(E/'compiler-warnings.txt').write_text('\n'.join(warn)+'\n')
failures=sorted(p.name for p in E.glob('checker-failure-*'))
corrections=read('checker-corrections.json') if (E/'checker-corrections.json').exists() else []
markers=[f'ASUS49-ENTRY run={u}',f'A49CAP1 uuid={u} rows=15 row=384 fields=17 header=192','A49FAULT 0',f'A49SW2 uuid={u}','VA49SH   <matching generation/metadata/tail>','A49SLOSS 0 guard=0 busy=0 admission=0 overflow=0',f'A49SGUARD BEGIN {u}',f'A49SGUARD END   {u}','VA49S 00..09 <320 bytes; matching sequence/tail; 14 fields and comm>','ASUS49-DIAG headless RDMA IRQ registration skipped module=2 name=rdma0 linux_irq=<runtime mapped IRQ>','ASUS49-DIAG headless RDMA IRQ registration skipped module=3 name=rdma1 linux_irq=<runtime mapped IRQ>']
h=dict(status='DELIVERED_ONE_DIAGNOSTIC_ACTIVE_WORK_CAPTURE',physical_GO=False,fullOS_GO=False,physical_trial=False,VM_status='TERMINATED',VM=dict(project='PROJECT_REDACTED',zone='us-central1-a',instance='PROJECT_REDACTED',id='8549823276971553556'),remote_root=ctx['remote_root'],base_remote_root=ctx['base_remote_root'],capture_UUID=u,helper_UUID=p['helper_uuid'],candidate=p['candidate'],full_p10=p['full_p10'],admitted_current_full_p10=p['admitted_current_full_p10'],current_preimage_supplied_not_read=True,compiled_Image_gz_dtb=p['compiled_Image_gz_dtb'],raw_Image=p['raw_Image'],System_map=dict(uncompressed=build['artifacts']['System.map'],gzip=dict(bytes=len(mapgz),sha256=sha(mapgz)),uncompressed_verified_locally=True,vmlinux='VM only'),config=p['config'],preservation=p['preservation'],compile_attempts=1,max_jobs=8,warnings=len(warn),compiler_source_corrections=0,verification_checker_corrections=len(corrections),verification_checker_correction_receipt='checker-corrections.json',verification_checker_failure_receipts=failures,default_PLAN_calls=1,PLAN_isolation='truthful in-memory restricted public readers only; delivered guards unchanged',commands=commands,expected_markers=markers,capture_layout=layout,hook_ABI=abi,limits=limits,no_device_or_private_access=True,no_execute=True,no_next_build=True)
write('handoff.json',h)
active=json.loads((E/'host-controls/positive-decoded.json').read_text());inactive=json.loads((E/'host-controls/inactive-decoded.json').read_text())
examples=dict(synthetic_host_encoding_only=True,runtime_evidence=False,active={k:active['records'][0][k] for k in ['sequence','PF_WQ_WORKER','worker_present','worker_flags','current_func','current_work','active_work_assessment']},inactive={k:inactive['records'][0][k] for k in ['sequence','PF_WQ_WORKER','worker_present','worker_flags','current_func','current_work','active_work_assessment']},note='Values are fabricated host-control inputs; actual kernel fields were not observed here.')
write('decoded-examples.json',examples)
(R/'README.md').write_text(f'''# Active work at the scheduler capture seam

Question: what active work function did the selected current worker already own at the existing scheduler switch seam?

Status: **ONE diagnostic candidate built and packaged; existing VM verified TERMINATED.** Parent owns one physical trial, eventual manual fallback and interpretation. No device/ADB/root/private factory/raw target logs, execute, physical/fullOS GO or next build.

- [candidate.img](artifacts/candidate.img): {p['candidate']['bytes']} bytes; SHA-256 `{p['candidate']['sha256']}`.
- [candidate.p10.raw](artifacts/candidate.p10.raw): {p['full_p10']['bytes']} bytes; SHA-256 `{p['full_p10']['sha256']}`.
- [System.map.gz](artifacts/System.map.gz): {len(mapgz)} bytes; SHA-256 `{sha(mapgz)}`. Genuine uncompressed map: {len(mapraw)} bytes, SHA-256 `{sha(mapraw)}`; verified locally. `vmlinux` remains VM-only. Offline symbolization needs no VM restart.
- Fresh entry/legacy/switch UUID: `{u}`. Full helper/ramdisk UUID stays `{p['helper_uuid']}`.
- [Handoff](evidence/handoff.json), [source diff](source/changes.patch), [source pre/posts](evidence/source-pins.json), [scoped preservation](evidence/linked-capture.json), [ownership proof](evidence/ownership-proof.md), [actual hook ABI](evidence/hook-abi.json), [disassembly](evidence/scoped-hooks.disasm), [layout](evidence/switch-layout.json), [host controls](evidence/encoding-controls.json), [synthetic decoded examples](evidence/decoded-examples.json).

The public prior result captured runnable PID1 out at sequence1234 to PID119 kworker/0:3, normal priority120/policy0, with no later switch in a complete finite nofault capture. It did not capture an active function or prove execution after finish_task_switch. This unit adds only own-worker `READ_ONCE(current_func)` and `READ_ONCE(current_work)` snapshots plus PF_WQ_WORKER/worker-present validity at that same seam, immediately after saved prev_state and before vtime/perf/rq unlock/lifetime changes. The exact branch already includes workqueue_internal.h and current_wq_worker() returns kthread_data(current) only in task context with PF_WQ_WORKER. Current task/worker lifetime and actual CPU0, nr_cpu_ids1, IRQ-disabled admission are explained in the ownership proof and linked ABI receipt. No last_func substitution, work->func dereference, pwq/name walk or new seam is introduced.

A valid own worker with a non-NULL current_func reports `active_function_snapshot`. A valid own worker with NULL current_func reports `no_active_function_at_seam`; this leaves later work inconclusive. Non-worker and worker-unavailable are explicitly separate validity outcomes. The host examples use fabricated numeric pointers and are **not runtime evidence**. None of these observations automatically establishes culprit, starvation, scheduler failure or execution after the seam. Actual raw pointer values must stay parent-private until symbolized.

A49SW2 uses 320-byte rows, 14 numeric fields, all 16 comm bytes, matching sequence/tail, eight bounded ring slots and fixed latest PID1-out/in slots. The old 5952-byte area/decoder are unchanged. The switch area is 3648 bytes; cap_init's existing actual OEM console bound check reserves all **9600 combined bytes before append/readiness**. It adds 640 fixed bytes within the same admitted console and preserves hardware DT/reservations/mapping. Invalid-before-payload/clean+dsb/valid-last publication, guards, sticky faults, busy/overflow and before-ready semantics remain. The decoder rejects wrong protocol, malformed/partial fields or loss, torn generations, cross-slot disagreement and inconsistent finite horizon. Timing can change from encoding/cache cleaning under the existing rq lock.

Base `{ctx['base_remote_root']}/{{kernel,out}}`; owned output `{ctx['remote_root']}`. Independent inodes via cp -a --reflink=auto, preserving frozen/nested repositories without a full-tree audit. Exactly one make -j8 Image.gz-dtb succeeded; {len(warn)} warning lines retained, zero compiler/source corrections. One checker-only correction resolved duplicate local trace_init symbol selection; initial output and script are preserved separately in [checker corrections](evidence/checker-corrections.json). Candidate source was unchanged. [Repository preservation](evidence/repository-preservation.json), [source-copy receipt](evidence/source-copy.json), [build receipt](evidence/build-receipt.json), [package receipt](evidence/packaging-receipt.json), [packager changes](source/package.diff), [installer diff](source/install.diff).

Config remains `{p['config']['sha256']}`. Genuine output config, runtime and compiled hardware DT, whole wrapped helper ramdisk, initrd geometry, bootargs/mappings and timer/counter/core behavior/RDMA skips compare unchanged. Installer execute/Transport/Guard/adapters are byte-identical; only pins, profile, actual length and append-only current full-p10 `{p['admitted_current_full_p10']}` change. This current pin came from parent and was not read from target. adb remains 0755. The previous preserved packager was reused with base/pin/profile updates. [One isolated default PLAN](evidence/install-plan.json) passed using only the prior truthful in-memory restricted public reader substitutions; [limitations](evidence/plan-isolation-receipt.json). Delivered readers/guards remain intact.

Readiness/build/fetch used one owned persistent SSH master with ProxyCommand=false on channels, preserving remote.py SHA c22884576a780cbb1ddf5e1b02f0b6e9d6eb5c25f8d9bc82fb077543f05cf4ab. Only this master was closed. [Final VM state](evidence/after.stdout): TERMINATED, ID8549823276971553556 in PROJECT_REDACTED/us-central1-a.

Parent PLAN (no execute authorized by this handoff):

```sh
{commands['PLAN']}
```

After the parent's single physical trial and established complete-console collection, decode locally; placeholder paths are parent-private:

```sh
{commands['decode_legacy']}
{commands['decode_switch']} > /absolute/path/to/parent-private-switch.json
{commands['symbolize']}
```

Expected: fresh ASUS49-ENTRY, A49CAP1 and A49SW2 identities; A49FAULT 0; canonical VA49SH; A49SLOSS 0 guard=0 busy=0 admission=0 overflow=0; both UUID-bound A49SGUARD lines; ten 320-byte VA49S rows; unchanged RDMA0/1 registration-skip markers with runtime IRQ values. Full marker strings and exact commands are in handoff.json. Parent still owns identity/geometry/full-p10 readback checks. Missing/torn/nonadmitted results are UNKNOWN, with no automatic retry.

Continuation: parent interprets its one authorized physical trial. NULL does not exclude later work. Stop after this candidate; no physical/fullOS GO or next build.
''')
paths=[p for n in ['source','scripts','artifacts'] for p in (R/n).rglob('*') if p.is_file() and '__pycache__' not in p.parts]+[R/'README.md']
paths += [p for p in E.iterdir() if p.is_file() and p.name!='delivery-pins.json']
write('delivery-pins.json',{str(p.relative_to(R)):dict(bytes=p.stat().st_size,sha256=sha(p.read_bytes())) for p in sorted(paths)})
print(json.dumps({k:h[k] for k in ['status','VM_status','capture_UUID','candidate','full_p10','System_map','compile_attempts','default_PLAN_calls']},indent=2))
