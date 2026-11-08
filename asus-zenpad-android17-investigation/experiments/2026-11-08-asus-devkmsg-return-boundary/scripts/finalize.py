from pathlib import Path
import hashlib,json
R=Path(__file__).resolve().parents[1];E=R/'evidence';I=json.loads((E/'identity.json').read_text());P=json.loads((E/'packaging-receipt.json').read_text());B=json.loads((E/'build-receipt.json').read_text());M=json.loads((E/'System.map-uncompressed.json').read_text())
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
assert json.loads((E/'focused-checks.json').read_text())['status']=='PASS'
a=json.loads((E/'after.stdout').read_text());assert a['id']=='8549823276971553556' and a['status']=='TERMINATED'
assert not Path('/tmp/aswent-'+I['kernel_uuid'][:8]).exists()
inputs=['2026-11-08-asus-large-v2-loop-series-reassessment/ASSESSMENT.md','2026-11-08-asus-large-v2-loop-series-reassessment/RECOMMENDATION.md','2026-11-06-asus-product-input-build-kit/scripts/remote.py']
(E/'parent-input-pins.json').write_text(json.dumps({n:sha(R.parent/n) for n in inputs},indent=2)+'\n')
facts=dict(provenance='User-supplied summarized physical facts only; no private logs/target content opened',current_candidate='f6bdb96f15a1cc23af1f0a2f5d4049cba98fba40472241f291ac1e10a473deaa',current_full_p10=P['base_full_p10'],prior_milestone_variant='500k checksum expected published; no 1M/2M marker',final_only_variant='No 2M marker; last helper LOG sched.original, policy0/getparamrc0/priority0; initial clock 0.642032768',before_IRQ='PPI30 count179; PPI29 zero',horizon='3170B complete console, new stock boot, full readback, fresh control bound; stock returned',earlier_facts='FIFO actual priority1 but no finish; heavy capture finite PID1 runnable -> kworker battery ADC, none causal',interpretation='Missing records do not prove permanent hang or publication fault; hardware protections untouched')
(E/'supplied-physical-facts.json').write_text(json.dumps(facts,indent=2)+'\n')
commands=dict(plan=f'python3 -B {R}/source/install.py',execute=f'python3 -B {R}/source/install.py --execute',decoder=f'python3 -B {R}/scripts/decode_boundary.py /absolute/parent-owned/complete-console.txt --installed-full-sha256 {P["full_p10"]["sha256"]} --fresh-stock-boot-reference /absolute/parent-owned/new-stock-boot-evidence --complete-console-reference /absolute/parent-owned/complete-console-horizon-evidence',marker=f"rg -n 'ASUS_DEVKMSG_PREFIX|ASUS_SPARSE_MODE|asus_devkmsg_boundary' {R}/source/arch/arm64/kernel/asus_entry_tag.h {R}/source/arch/arm64/kernel/asus_retained_trace.c {R}/source/kernel/printk/printk.c",map_hash=f'gzip -dc {R}/artifacts/System.map.gz | shasum -a 256',map_symbols=f"gzip -dc {R}/artifacts/System.map.gz | rg ' (devkmsg_write|asus_devkmsg_boundary|log_store|asus_retained_trace_write|kmsg_fops)$'")
result=dict(status='ONE_CANDIDATE_STOP_NO_DEVICE_CONTACT_NO_PHYSICAL_GO',identity=I,artifacts={n:dict(bytes=(R/'artifacts'/n).stat().st_size,sha256=sha(R/'artifacts'/n)) for n in ['candidate.img','candidate.p10.raw','Image.gz-dtb','resolved.config','System.map.gz','runtime.dtb','ramdisk.wrapped']},System_map_uncompressed=M,remote_vmlinux=dict(path=I['remote_root']+'/out/vmlinux',**B['artifacts']['vmlinux'],left_remote=True),remote_kernel=I['remote_root']+'/kernel',remote_out=I['remote_root']+'/out',kernel_command=json.loads((E/'build-status.json').read_text())['kernel_command'],kernel_builds=1,helper_compiles=0,candidates=1,isolated_PLAN_calls=1,VM_terminated=True,owned_master_closed=True,original_postbuild_GDB_failure='Preserved in build-status.json/dispatch.stderr; compile and preservation passed before missing cross-GDB. Read-only nm/objdump fallback succeeded. No rebuild.',parent_commands_not_executed=commands)
(E/'handoff.json').write_text(json.dumps(result,indent=2)+'\n')
(E/'kernel-build-outcome.json').write_text(json.dumps(dict(status='SINGLE_INCREMENTAL_KERNEL_BUILD_SUCCEEDED',kernel_builds=1,helper_compiles=0,original_driver_status='failed after successful compile/preservation because cross-GDB unavailable',qualification_recovered_read_only=True,extra_kernel_builds=0,actual_compile_log='compile-1.log',original_status='build-status.json',recovery='qualification-recovery.json'),indent=2)+'\n')
proof=f'''# Focused source and linked-ELF proof

Exactly four kernel source files changed; exact before/after SHA256 values are in prepost.json and the complete diff in ../source/changes.patch. Baseline source was read before modification. Parent ASSESSMENT corrections govern the consultant recommendation.

The frozen helper creates char major1/minor11. drivers/char/mem.c devlist[11] selects kmsg_fops through memory_open. The actual linked kmsg_fops write_iter pointer at offset40 is {json.loads((E/'linked-route-symbols.json').read_text())['devkmsg_write']['address']}, the instrumented devkmsg_write. fs/read_write.c selects write_iter through new_sync_write for this file. printk_emit calls vprintk_emit; its linked route calls log_store. Evidence: base source, linked-kmsg-fops.txt and linked-*.disasm. O_NONBLOCK does not make allocation/copy/printk internals nonblocking.

WENT follows original user/length/logging/ratelimit checks, directly before original GFP_KERNEL kmalloc. Original copy_from_iter occurs once. Prefix parsing still modifies len, while ret retains the actual input length; boundary calls use ret on exits. Normal WRET follows original kfree, immediately before original return ret. ENOMEM WRET precedes original -ENOMEM return. EFAULT WRET follows original kfree and precedes original -EFAULT return. Removing only the additions restores the entire original devkmsg function byte-for-byte. Existing log_store, trace_init, cap_init and direct writer function bodies are byte-identical.

Actual linked devkmsg calls: entry 0xffffff800810beec before __kmalloc at 0xffffff800810bf00; EFAULT recorder 0xffffff800810bf98 after kfree at 0xffffff800810bf28; normal printk_emit 0xffffff800810c030, kfree 0xffffff800810c038, recorder 0xffffff800810c04c; ENOMEM recorder 0xffffff800810c068. Common epilogue/stack guard and C return follow. Existing LOG writer call 0xffffff80081091b0 follows original ring updates; inlined local_clock routes through sched_clock at 0xffffff8008109220, timestamp store at 0xffffff8008109228, back to original tail at 0xffffff8008109174.

asus_devkmsg_boundary is the single recorder (linked 0xffffff8008097820). It admits only current->pid==1 and in_task(). Actual PID1 is one task; userspace signal handling can occur between syscalls, not nest a syscall on the same kernel stack. The counter has no concurrent process writer. The emitter uses a 160B stack buffer and scnprintf, then the unchanged direct retained writer. Linked calls are only scnprintf, asus_retained_trace_write and compiler stack-failure guard. No clock/MMIO, allocation, recursive printk, copied user text or addresses are added. No new IRQ counter, POST stage, generation counter, retained area or broad wipe.

The writer is NOT lock-free: raw_spin_trylock_irqsave, cache flush to PoC, aligned log_size commit, unlock/restore. It can drop on unready/filter/lock/full; can truncate at full and resets may tear publication. Its accepted critical section is the only added masking/locking, never held across original allocation/copy/printk/free. The process-context recorder is compatible with this existing writer; this source/ELF proof is not a physical timing or retention guarantee.

768 selected writes maximum. Entry769 attempts one UNKNOWN write-budget marker and refuses further boundary capture without changing original writes. Both normal and early-return records use the same per-write seq and original input len; no extra user copy. Max valid boundary record including newline is 85B; fixed stack buffer160B. Existing console geometry is retained; full/dropped/torn/gapped output is UNKNOWN. Hot observer ready-pointer initialization is still disabled; old hot protocol tags are absent from actual raw Image.

Focused checks cover four units: source/ELF route and original-operation preservation; actual package/config/ramdisk/DT/guard preservation; one isolated PLAN; decoder calibration plus stale/gap/malformed/order/signal/early-return controls. Synthetic console fixtures are explicitly not device evidence. No emulator, tablet, ADB command, private target reader, install, reboot or trial was used.

Single compile succeeded. Post-build cross-GDB inspection was unavailable; original failure receipt preserved and recovered with read-only nm/objdump. No second build. Image.gz-dtb, config, scoped evidence and genuine gzip System.map fetched; vmlinux remains remote. Ordinary full independent copies followed metadata/free-space check; every copied regular file had a different mutable inode. Exact VM stopped and verified TERMINATED; only owned SSH master closed.
'''
(E/'scoped-proof.md').write_text(proof)
text=f'''# One cold devkmsg boundary candidate — STOP

One incremental -j8 Image.gz-dtb build, zero helper compiles, one package and one isolated PLAN. No device contact, physical trial, root-cause conclusion, physical GO, automatic fix or storage advance.

Candidate: [candidate.img](../artifacts/candidate.img), {P['candidate']['bytes']:,} bytes, SHA256 `{P['candidate']['sha256']}`.

Full p10: [candidate.p10.raw](../artifacts/candidate.p10.raw), {P['full_p10']['bytes']:,} bytes, SHA256 `{P['full_p10']['sha256']}`.

Fresh kernel UUID `{I['kernel_uuid']}`; profile devkmsg-boundary-v1, format1. Helper UUID `{I['helper_uuid']}` and control `{I['control_uuid']}` are deliberately reused. Exact fullp10, new stock boot and complete single-console horizon bind a trial. This is new observation instrumentation with the entire existing wrapped ramdisk unchanged, not a helper variant.

Frozen helper SHA256 `{P['init']['sha256']}`. Entire wrapped ramdisk SHA256 `{P['ramdisk']['sha256']}`. Config SHA256 `{P['config']['sha256']}`. Runtime and compiled hardware DTs, short bootargs, initrd0x44000000..0x4403e92a, guard0x4403f007 and hardware policies preserved. Genuine Image.image_size={P['layout']['Image_image_size']}, loaded end={P['layout']['loaded_Image_end']}, no overlap. Installer execute/Transport/Guard and adapters byte-identical; adb0755. Current supplied fullp10 `{P['base_full_p10']}` appended to admissions, without claiming fresh readback here.

Exact source/API and linked call proof: [scoped proof](../evidence/scoped-proof.md), [complete diff](../source/changes.patch), [before/after hashes](../evidence/prepost.json). Pins and commands: [handoff.json](../evidence/handoff.json). Build/package/PLAN receipts and synthetic parser controls remain under evidence/.

Record ABI (actual retained lines; seq decimal1..768; len is original input bytes):

```text
ASUS49-KMSG run={I['kernel_uuid']} v=1 WENT seq=N len=L
ASUS49-SYSCLOCK run={I['helper_uuid']} ...existing admitted LOG text...
ASUS49-KMSG run={I['kernel_uuid']} v=1 WRET seq=N len=L rc=R
ASUS49-KMSG run={I['kernel_uuid']} v=1 UNKNOWN reason=write-budget limit=768
```

WENT precedes original kmalloc after all original validation/ratelimit checks. WRET follows original kfree before normal C return, or records the actual original -12/-14 early exit. Log_store hook unchanged. No raw input text/address is added to the boundary records. Writer uses trylock/IRQ-save and may drop; no outer IRQ mask or lock spans original operations. Filtered setup writes may have WENT/WRET without a LOG. The overflow marker, if published, makes interpretation UNKNOWN; its absence cannot establish no loss.

The decoder enforces exact identity/version/seq/len/order/rc and matches the frozen helper's ASCII input length (<6> plus LOG plus newline). It checks full triples for initial-clock begin and successful initial-clock end, normal policy0/priority0, and reused control clock.path. Calibration and observed boundary facts are separate. Missing calibration cannot accept the instrument. Gaps/duplicates/stale/torn/unknown markers are UNKNOWN. Synthetic positive and negative fixtures are not physical observations.

Signal-handler writes are reported separately. The same PID1 thread serializes kernel syscalls, but the signal handler can run between main-flow writes. A later WENT adds sequential boundary evidence; it does not prove the intended main-flow continuation. A missing LOG may be filtering or loss, so an unlogged write's user flow is UNKNOWN.

WRET proves only its pre-C-return point was reached; it does not prove C return/syscall exit/userspace resumption. LOG without WRET narrows the captured span only. WENT without LOG is not allocation-fault proof. WRET without another WENT is not execution-loss proof. Retention/publication/scheduling/reset effects remain possible. No standalone absence classifies CPU hang/reporting failure, exonerates compute, reinterprets prior trials, or permits storage work.

Parent-only commands below were NOT executed here. Parent owns original private dependency checks, exact installed full readback, new stock boot, one trial, complete console and interpretation. The actual delivered PLAN retains all guards; the one local PLAN replaced restricted readers only in memory, so it did not validate private stock/root dependencies and grants no physical GO.

```sh
{commands['plan']}
{commands['execute']}
{commands['decoder']}
```

Execute remains install-only; it does not reboot or run a trial. Decoder references are parent attestations; the decoder does not open their contents or observe the target. Stop after the parent's one separately authorized trial; no automatic repeat/fix follows any result.

Read-only source marker and genuine map commands:

```sh
{commands['marker']}
{commands['map_hash']}
{commands['map_symbols']}
```

Uncompressed System.map: {M['bytes']:,} bytes, SHA256 `{M['sha256']}`; compressed artifact is genuine, pinned in handoff.json. Actual kernel build command is in handoff.json and build-status.json. Remote kernel/out isolated at `{I['remote_root']}`; vmlinux retained remotely at `{I['remote_root']}/out/vmlinux`, SHA256 `{B['artifacts']['vmlinux']['sha256']}`. No local vmlinux fetch. Metadata/free-space and independent-copy receipts retained.

Single kernel compile passed and source/config/DT preservation passed. A subsequent cross-GDB inspection command was unavailable; its original failed driver status is preserved. Read-only nm/objdump qualification succeeded; no rebuild or corrective variant. See kernel-build-outcome.json and qualification-recovery.json.

Exact VM PROJECT_REDACTED/us-central1-a/PROJECT_REDACTED, ID8549823276971553556, IPIP_REDACTED verified TERMINATED. Owned /tmp/aswent-{I['kernel_uuid'][:8]} master closed. No new assets/disks/accounts/caps, children, device operations or private target access.

STOP: one candidate delivered. No further implementation or physical work is authorized by this handoff.
'''
(R/'output/HANDOFF.md').write_text(text)
(R/'README.md').write_text(f'''# Cold devkmsg write boundary

Question: which admitted PID1 devkmsg entry/LOG/return boundaries are captured with the frozen final-only helper?

Status: **one candidate implemented and packaged; STOP**. One incremental kernel build, zero helper compiles, one isolated PLAN. Focused source/ELF, preservation and parser controls passed. No device/ADB/private target access, install, reboot or physical trial. Exact VM verified TERMINATED; owned SSH master closed.

Outputs: [handoff](output/HANDOFF.md), [candidate](artifacts/candidate.img), [fullp10](artifacts/candidate.p10.raw), [source diff](source/changes.patch), [source/ELF proof](evidence/scoped-proof.md), [pins and parent commands](evidence/handoff.json), [checks](evidence/focused-checks.json), [decoder](scripts/decode_boundary.py).

Candidate SHA256 `{P['candidate']['sha256']}`. Fullp10 SHA256 `{P['full_p10']['sha256']}`. Fresh kernel `{I['kernel_uuid']}`/format1; helper and control reused honestly. ENTIRE wrapped ramdisk/helper, config, DT, short bootargs and initrd bounds preserved.

Continuation: parent owns exact installed fullp10/new stock boot/complete-console binding and any separately authorized single trial. Report captured boundaries and calibration separately; missing records remain UNKNOWN. WRET is before C return, not userspace resumption. No CPU-hang/reporting-fault verdict, storage advance, automatic fix or next candidate.

Build note: compile succeeded; post-build cross-GDB inspection was unavailable. Original failure receipt preserved, read-only nm/objdump qualification passed, no rebuild. See evidence/kernel-build-outcome.json.
''')
# Hash every delivered file after documents are final; excludes only this manifest.
paths=sorted(p for p in R.rglob('*') if p.is_file() and p.name!='SHA256SUMS' and '__pycache__' not in p.parts)
(R/'SHA256SUMS').write_text(''.join(sha(p)+'  '+str(p.relative_to(R))+'\n' for p in paths))
print(json.dumps(dict(status=result['status'],candidate=P['candidate'],full_p10=P['full_p10'],files_pinned=len(paths),VM_terminated=True,owned_master_closed=True),indent=2))
