from pathlib import Path
import ast,hashlib,json,difflib,shutil,sys,importlib.util
sys.dont_write_bytecode=True
R=Path(__file__).resolve().parents[1];W=R.parent;B=W/'2026-11-07-asus-stock-entry-refusal-capture';P=W/'2026-11-07-asus-stock-entry-writer-control-r2'
def boundary(event,args):
 if event=='open':assert not any(x in str(args[0]) for x in ('/private/','/device-backup/','root_shell_wifi.py','mtk-su-mirror-b','/dev/'))
 if event.startswith(('socket.','subprocess.')) or event in ('os.system','os.posix_spawn'):raise RuntimeError(event)
sys.addaudithook(boundary)
sha=lambda b:hashlib.sha256(b).hexdigest()
p=json.loads((R/'evidence/packaging-receipt.json').read_text());run=p['run_uuid'];replay=json.loads((R/'evidence/replay.json').read_text());plan=json.loads((R/'evidence/plan-isolation-receipt.json').read_text())
assert sha((B/'artifacts/candidate.p10.raw').read_bytes())==p['current_preimage']
before=(B/'source/asus_entry_text.S').read_text();after=(R/'source/asus_entry_text.S').read_text()
assert after==before.replace('.Laet_linux:\n\tcmp x14, #0x200','.Laet_linux:\n\tcmp x14, #0x40')
plain=(P/'source/asus_entry_text.S').read_text().replace('.Laet_linux:\n\tcmp x14, #0x200','.Laet_linux:\n\tcmp x14, #0x40')
assert sha(plain.encode())=='e56fffecd0f825439d3711ab931180d58a5a320e70ebb8b30fcc5e8442cd631d'
assert '\tmov x14, #0x200\n' in after
assert (R/'source/entry.S').read_bytes()==(B/'source/entry.S').read_bytes()
for n in ['adb','legacy_adb.py','bootformat.py','stock-marker-only.dtb']:
 assert (R/'source'/n).read_bytes()==(B/'source'/n).read_bytes()
for name in ['preparation.json','completion.json','slot-original.disasm','stock-ram_console_early_init.disasm','stock-aee_rr_reboot_reason_show.disasm','stock-aee_rr_reboot_reason_proc_open.disasm']:
 shutil.copyfile(P/'evidence'/name,R/'evidence'/('prior-r2-'+name))
from bootformat import parse_image,ungzip
_,kernel,_,_=parse_image((R/'artifacts/candidate.img').read_bytes());raw,_=ungzip(kernel[512:]);base=0xffffffc000080000
for pointer in (0xffffffc000c0a948,0xffffffc001002ef8):
 assert int.from_bytes(raw[pointer-base:pointer-base+8],'little')==0xffffffc000696b14
sources={}
for n in ['entry.S','asus_entry_text.S','asus_entry_tag.h','readback.S','control.ld','install.py']:
 a=(B/'source'/n).read_bytes();b=(R/'source'/n).read_bytes();sources[n]=dict(before_sha256=sha(a),after_sha256=sha(b),before_bytes=len(a),after_bytes=len(b))
 (R/'evidence'/(n.replace('.','-')+'.diff')).write_text(''.join(difflib.unified_diff(a.decode().splitlines(True),b.decode().splitlines(True),fromfile='capture/'+n,tofile='linux-offset-control/'+n)))
source_receipt=dict(sources=sources,corrected_plain_assembly_sha256=sha(plain.encode()),future_C_sha256=sha((R/'source/future-4.9/arch/arm64/kernel/asus_retained_trace.c').read_bytes()),failure_114='derived Linux offset < 0x40 (64); all other IDs retain original conditions',fallback_mov_x14_0x200_unchanged=True,callback_table_and_kallsyms_pointers_unchanged=True,inherited_fixed_helper_slot_proof='prior-r2-completion.json',tag_writer_field='Inherited original R2 writer identifier 32f22ec9...; active source hashes are pinned here and in file-manifest.json')
(R/'evidence/source-pins.json').write_text(json.dumps(source_receipt,indent=2)+'\n')
# Check observer parse contract against the actual replayed record values and bytes read by the wrapper.
spec=importlib.util.spec_from_file_location('parse_trial',R/'source/parse_trial.py');parser=importlib.util.module_from_spec(spec);spec.loader.exec_module(parser)
rows=[]
for case in replay['late']:
 fields=[int(v,16) for v in case['prints'][0]['actual_fields']]
 line=('ASUS-ENTRY-DIAG '+run+' magic=%016x x0=%016x el=%x sctlr=%016x status=%x\n')%tuple(fields)
 actual=b''.join(bytes.fromhex(x['actual_bytes']) for x in case['prints'] if 'actual_bytes' in x)
 result=parser.parse(line.encode()+actual)
 assert result['record_commit']==case['record_commit'] and result['actual_complete_fresh_OEM_tag']==case['actual_complete_fresh_OEM_tag']
 rows.append(dict(case=case['case'],record_commit=result['record_commit'],actual_complete_fresh_OEM_tag=result['actual_complete_fresh_OEM_tag'],dual_positive=result['dual_positive']))
(R/'evidence/observer-contract.json').write_text(json.dumps(dict(cases=rows,scope='Host parsing of locally replayed actual record values and actual snapshot bytes; no physical proof.'),indent=2)+'\n')
p.update(status='ONE_CANDIDATE_FOCUSED_REPLAY_ONE_ISOLATED_PLAN_NO_PHYSICAL_TRIAL',readback_bounds='saved != NULL; 0x400 <= off_console < 0x80000; 0 < size <= 0x80000-off; start == 0; precision=min(size,234)',slot_gap_before_record=300-p['slot']['wrapper_and_format'])
(R/'evidence/packaging-receipt.json').write_text(json.dumps(p,indent=2)+'\n')
completion=dict(status=p['status'],candidate=p['candidate'],full_p10=p['full_p10'],run_uuid=run,readback_table=rows,source_pins='source-pins.json',plan=plan,physical_trial=False,kernel_4_9_built=False,next_action='Parent owns ONE guarded stock trial. Admit one corrected 4.9 build only after BOTH positives. Any negative: stop and report; no variant.',patch_scope='entry B, original clear BL, existing unused 352B callback slot; append in original prezero BSS reservation',fixed_PID1_scope='byte-identical original complete ramdisk and legacy RAM USB helper; no proc diagnostic path use or new reporter',conditions='Only parent literal cmp x14 lower bound changed; fallback and complete PL/LK/header/alignment/nonoverlap/capacity guards preserved')
(R/'evidence/completion.json').write_text(json.dumps(completion,indent=2)+'\n')
tag=parser.TAG.decode();slot=p['slot'];rowtext='\n'.join('| '+x['case']+' | '+str(x['record_commit'])+' | '+str(x['actual_complete_fresh_OEM_tag'])+' |' for x in rows)
readme=f'''# Stock Linux offset control — scoped experiment 2

Question: does the parent-corrected Linux offset commit in the stock early hook, and does the complete fresh OEM text survive through the actual incoming snapshot readback?

Status: **one candidate packaged; focused actual-instruction replay and one isolated installer PLAN passed. No physical trial and no 4.9 build.** Parent owns one stock trial. Require both independent positives before admitting one 4.9 build with the staged parent correction. Any negative: stop and report; no additional calibration variant or driver fix.

The preceding physical trial established early magic `454559535452454e`, x0 `4e000000`, CurrentEL `8` (EL2), SCTLR `30c50830`, status `72` hex (114), under late UUID `ddfa517b-e809-45c8-83d9-a573403b3e68`; normal Android returned as `be73a526-a85c-4880-a9d6-6c2babd80aac`. This is the parent-supplied physical result, not a new measurement here. ID 114 formerly rejected derived Linux offset below 512 despite stock using a smaller derived offset when valid nonzero LK records exist.

## One package and pins

| Artifact | Bytes | SHA-256 |
|---|---:|---|
| `artifacts/candidate.img` | {p['candidate']['bytes']} | `{p['candidate']['sha256']}` |
| `artifacts/candidate.p10.raw` | {p['full_p10']['bytes']} | `{p['full_p10']['sha256']}` |
| Unmodified public donor image | 7745536 (see source donor) | `dc0b98e66798e3abc019f454921b1c84ff3ce58e356e26d0785e05b7714d3427` |
| Original raw stock Image | {p['raw_before']['bytes']} | `{p['raw_before']['sha256']}` |
| Patched raw Image | {p['raw_after']['bytes']} | `{p['raw_after']['sha256']}` |

Donor image byte count is recorded by the pinned source parser; the SHA is authoritative. Current full p10 preimage: `{p['current_preimage']}`. Candidate full p10 is exactly **16740352** bytes, zero-padded after the Android image. Full before/after bytes and appended bytes are in `evidence/packaging-receipt.json`; source pre/post SHA-256 values and diffs are in `evidence/source-pins.json` and `evidence/*-*.diff`. `evidence/file-manifest.json` pins every delivered source, QA output and evidence file.

The instrumented writer differs from capture by exactly `.Laet_linux: cmp x14,#0x200` → `cmp x14,#0x40`. The default `mov x14,#0x200` remains unchanged. **ID 114 now means derived Linux offset <64**; all other IDs and conditions are unchanged (`evidence/failure-ids.tsv`). Complete PL/LK extent, alignment, nonoverlap, header and console-capacity checks remain. No new fix was invented.

The parent-corrected plain assembly SHA is `e56fffecd0f825439d3711ab931180d58a5a320e70ebb8b30fcc5e8442cd631d`; corrected C SHA is `76d9ff38bbf47995594a4795fe5af5b22f78b93fa91f6190bb4bbdf1c864721e`. Exact copies and `correction.patch` are in `source/future-4.9/`, **handoff only, unbuilt**. The OEM tag's `writer=` identifier is inherited R2 baseline identity; these source pins identify the applied correction.

## Actual dual observer and bounds

Fresh shared run UUID: **`{run}`**. Complete actual OEM tag, including its terminating newline (234 bytes):

```text
{tag}```

The tag is stored by the early writer. The late wrapper never prints a constant copy: it prints actual own-record fields first, then passes validated **saved incoming snapshot + off_console** to priority-1 `%.*s`, then calls original `__memset_io`. Saved global is VA `0xffffffc001278568`. It requires saved nonnull, `0x400 <= off_console < 0x80000`, `0 < size <= 0x80000-off_console`, start=0; precision is `min(size,234)`. It neither scans an unbounded string nor reads past the admitted snapshot. A short/partial text result is not complete-tag calibration.

At original clear BL VA `0xffffffc000f41564` (raw offset `0xec1564`), the wrapper uses the existing unused slot `[0xffffffc000696b14,0xffffffc000696c74)` (raw offset `0x616b14`, 352 bytes). Code is **{slot['wrapper_code']} bytes**, code+formats **{slot['wrapper_and_format']} bytes**, leaving **{300-slot['wrapper_and_format']} bytes** before the record. Record is fixed at offset **300**, VA `0xffffffc000696c40`, physical `0x40696c40`, length **40**; 12 bytes remain after it. The linker and packaging assertions prove nonoverlap. No active production slot or new BSS record was used.

The five little-endian u64 record fields are magic, original x0, CurrentEL, matching SCTLR (or sentinel), terminal status. Record is initially zero. Actual early magic is `454559535452454e`; terminal commit is `ffff`. Late format is exactly:

```text
ASUS-ENTRY-DIAG {run} magic=%016llx x0=%016llx el=%llx sctlr=%016llx status=%llx
```

A 48-byte aligned frame preserves original clear x0/x1/x2 and x29/LR/SP; x18–x28 are untouched. Both printk calls may clobber caller-saved registers. Original clear target is `0xffffffc00008a688`; original printk is `0xffffffc000abe7a8`. Early record capture, all terminal refusal IDs, and targeted `DC CVAC` publication are unchanged from capture (`evidence/cache-visibility.json`). Early boot x0–x3, x18–x30 and SP survive.

The Image entry B at raw offset 0 branches to appended VA `{p['entry']['virtual']}` / PA `{p['entry']['physical']}`, returning to PA `0x40080040`. Append ends at `{p['entry']['append_end']}` before original BSS stop `0xffffffc001330018`, within original Image reservation/LK capacity. No other original raw spans change. Stock callback table and kallsyms pointer values remain unchanged; inherited sole fixed-PID1 helper does not invoke the diagnostic proc callback. The exact prior unused-slot/callgraph proof and stock code excerpts are retained as `evidence/prior-r2-*` and `prior-*`.

Stock DT is byte-identical to capture's compatible-member-only `asus,p00a` marker DT; original 512MB placeholder and other properties stay. Runtime `0x7d600000` bank is a **replay fixture only**. Whole wrapped ramdisk SHA is `{p['ramdisk_sha256']}`; helper remains `631a0aa5e72ee4110357ddac12bc5e5436ef3b1924cf64355f6fae99dc96d272`. No reporter compile, RAM-dump facility, same-boot helper change, normal BOOT/SYSTEM/DATA write, or clear/reset/watchdog change occurred.

## Focused local evidence

| Actual instruction replay | Record commit | Actual complete fresh OEM text read before clear |
|---|---|---|
{rowtext}

Low-LK derives `0xc0`; zero-LK falls back to `0x200`. Header overlap and PL/LK platform overlap refuse before any OEM store. All late cases print the actual record unconditionally and call the original clear with original arguments; adversarial printk/clear substitutes clobber x0–x17, and preserved ABI registers/LR/SP remain intact. `evidence/replay.json` retains exact fields, refusal tests, read pointers and actual snapshot bytes. Parser checks use those replayed bytes (`evidence/observer-contract.json`). MRS state is an EL2 fixture; DC addresses are checked without emulating coherence. Printk/clear are local ABI substitutes. **Host replay is not physical retention or 4.9 entry proof.**

The first interpreter attempt stopped at a missing Capstone import before replay/package; its stderr is retained as `qa/import-failure.stderr`. Existing local dependencies supplied the successful replay, without install. Standalone clang assembly and Rust-toolchain ld.lld linking only; no full kernel build.

## Parent command and readback contract

Exact parent install command, for the parent's already-guarded single physical stock-trial workflow (not executed here):

```sh
python3 {R}/source/install.py --execute
```

Installer changes relative to capture are only candidate/full pins, size/profile, and appending current `10c4c72da182f8164c238c27901b855e963eb1b5b66bb13827878f9f9c64370e` preimage. `execute`, `Transport`, `Guard` and adapters are unchanged; substitutions are reversible to the capture installer. One isolated PLAN called actual `main()` once with a pinned public stock template and an **in-memory source-check no-op**, disclosed in `evidence/plan-isolation-receipt.json`. Delivered guards and original readers remain intact. This PLAN did not validate private inputs or device state.

After the parent's ONE stock trial and stock return, save the complete raw retained log separately and parse it locally:

```sh
python3 {R}/source/parse_trial.py /absolute/path/to/complete-retained.log
```

Require both independently: (1) matching fresh diagnostic UUID plus actual early magic `454559535452454e` and terminal status `ffff`; (2) every byte of the complete 234-byte fresh OEM tag above present in the actual saved log, including newline. The parser reads log bytes, reports matched offsets, and never emits the expected constant as observed evidence. Numeric record fields parse as hex. Parent must establish complete capture and provenance; do not feed source/README/command transcripts as the log.

A late UUID alone, zero/missing magic, or `ffff` without complete actual OEM text is insufficient. A complete tag without the fresh valid commit record is independently insufficient. Preserve any negative evidence and stop; do not generate another control variant. Only dual-positive **stock calibration** admits one subsequent 4.9 build with the exact parent correction. This unit makes no 4.9-entry claim.

No device/ADB/network/SSH/cloud/private inputs/full kernel build/VM startup/install/reboot/subagents were used. Continue from the packaged pins; do not rerun assembly/replay/package/PLAN or start another variant.
'''
# Use the actual public donor size rather than a guessed documentation number.
donor=W/'2026-11-07-asus-stock-legacy-ram-usb-reporter/artifacts/candidate.img'
readme=readme.replace('7745536 (see source donor)',str(donor.stat().st_size))
(R/'README.md').write_text(readme)
(R/'qa/build-notes.txt').write_text('Standalone commands, executed once each:\nclang --target=aarch64-none-elf -c -x assembler-with-cpp source/entry.S -o qa/entry.o\nclang --target=aarch64-none-elf -c -x assembler-with-cpp source/readback.S -o qa/readback.o\n/OWNER_HOME/.rustup/toolchains/1.97.1-aarch64-apple-darwin/lib/rustlib/aarch64-apple-darwin/bin/gcc-ld/ld.lld -T source/control.ld -e capture_entry qa/entry.o qa/readback.o -o qa/control.elf\nPYTHONPATH=../2026-11-06-asus-stock-programmatic-control/.venv/lib/python3.13/site-packages python3 source/check_capture.py\npython3 source/plan_only.py\nNo replay failures; one pre-replay import failure retained. No install or dependency download.\n')
manifest={str(f.relative_to(R)):dict(bytes=f.stat().st_size,sha256=sha(f.read_bytes())) for folder in ['source','qa','artifacts','evidence'] for f in (R/folder).rglob('*') if f.is_file() and f.name!='file-manifest.json'}
manifest['README.md']=dict(bytes=(R/'README.md').stat().st_size,sha256=sha((R/'README.md').read_bytes()))
(R/'evidence/file-manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
print(json.dumps(dict(status=p['status'],pins=p['full_p10'],source_pins=sources,observer=rows),indent=2))
