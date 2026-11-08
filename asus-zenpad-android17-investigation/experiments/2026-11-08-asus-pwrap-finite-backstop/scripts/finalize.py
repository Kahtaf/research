from pathlib import Path
import hashlib,json,stat
R=Path(__file__).resolve().parents[1];E=R/'evidence';O=R/'output'
i=json.loads((E/'identity.json').read_text());p=json.loads((E/'packaging-receipt.json').read_text());b=json.loads((E/'build-receipt.json').read_text());checks=json.loads((E/'focused-checks.json').read_text());after=json.loads((E/'after.stdout').read_text())
assert checks['passed'] and after['id']=='8549823276971553556' and after['status']=='TERMINATED'
assert not Path('/tmp/aspwrap-1108').exists() and json.loads((E/'build-status.json').read_text())['status']=='complete'
assert stat.S_IMODE((R/'source/adb').stat().st_mode)==0o755
assert hashlib.sha256((R/'artifacts/candidate.img').read_bytes()).hexdigest()==p['candidate']['sha256']
assert hashlib.sha256((R/'artifacts/candidate.p10.raw').read_bytes()).hexdigest()==p['full_p10']['sha256']
assert i['helper_uuid']=='ef56ad88-6904-4452-90a1-3744beaa3c78' and i['control_uuid']=='342c9034-6b6f-4d95-aa67-9228b0904eb2'
commands=dict(build=b.get('kernel_command',json.loads((E/'build-status.json').read_text())['kernel_command']),parent_install_reference_only=['python3',str(R/'source/install.py'),'--execute'],parent_decoder_reference_only=['python3',str(R/'scripts/decode_boundary.py'),'<parent-console-payload.txt>','--installed-full-sha256',p['full_p10']['sha256'],'--fresh-stock-boot-reference','<parent-fresh-reference>','--complete-console-reference','<parent-complete-horizon-reference>'],physical_commands_executed=False)
handoff=dict(status='ONE_CANDIDATE_DELIVERED_STOP_NO_TRIAL',identity=i,pins={k:p[k] for k in ['candidate','full_p10','base_full_p10','init','ramdisk','config','compiled_Image_gz_dtb','compiled_DTB','runtime_DTB','installer']},remote_vmlinux=b['artifacts']['vmlinux'],genuine_System_map=b['artifacts']['System.map'],commands=commands,checks=dict(production_loop=json.loads((E/'loop-checks.json').read_text())['passed'],source_ELF_package_parser=checks['passed'],one_actual_isolated_PLAN=json.loads((E/'plan-isolation-receipt.json').read_text())['actual_installer_main_calls'],kernel_builds=b['kernel_builds'],helper_compiles=b['helper_compiles']),vm=dict(id=after['id'],status=after['status'],owned_master_closed=True,channel='/tmp/aspwrap-1108',TCP_fallback=False),physical_trial=False,stop='Parent owns at most ONE separately bound physical trial; no retune/repeat/variant/storage advance')
(E/'handoff.json').write_text(json.dumps(handoff,indent=2)+'\n')
(O/'HANDOFF.md').write_text(f'''# One finite pwrap backstop candidate — STOP

Implemented and packaged one candidate. One incremental kernel build, zero helper compiles, one restricted actual installer PLAN. No device/ADB/root/private target logs/factorydata access, install, reboot or physical trial. Exact VM `8549823276971553556` is verified TERMINATED and the owned master is closed. No further build, variant or trial was run.

* Candidate: [`../artifacts/candidate.img`](../artifacts/candidate.img), {p['candidate']['bytes']} bytes, SHA256 `{p['candidate']['sha256']}`.
* Fullp10: [`../artifacts/candidate.p10.raw`](../artifacts/candidate.p10.raw), {p['full_p10']['bytes']} bytes, SHA256 `{p['full_p10']['sha256']}`.
* Fresh kernel `{i['kernel_uuid']}`, profile pwrap-finite-v1, record format 1, finite budget **16,777,216**.
* Parent/current fullp10 `{p['base_full_p10']}` is appended to the original installer preimage set.
* Helper run `{i['helper_uuid']}` and control `{i['control_uuid']}` are frozen and distinct. Entire wrapped ramdisk SHA `{p['ramdisk']['sha256']}`; init/helper SHA `{p['init']['sha256']}`.
* Configuration SHA `{p['config']['sha256']}` remains identical. Compiled/runtime hardware DT, short bootargs, initrd `0x44000000..0x4403e92a`, entry guard `0x4403f007`, and load layout are preserved.

Behavior change is confined to the pwrap wait backstop, plus its rare fixed record and cold post-callback drain/identity/admission plumbing. Original 10 ms deadline precedes readiness; success, helper-local backward-clock handling, final readiness and -ETIMEDOUT recovery remain. No delay, locks, retry/sample count, hardware writes or policy changes.

Budget derivation uses the exact CPU OPP/clock sources and linked minimum work, with >16x headroom over an optimistic 10 ms iteration envelope: [derivation](../evidence/BUDGET-DERIVATION.md). Candidate ELF has 56 minimum instructions in the selected not-ready iteration against a conservative floor of 48. Count is not wall time; the supported execution envelope is an assumption, not a measured silicon limit. Single stalled operations, locks, latch retry and original delay remain outside its protection.

[Source patch](../source/changes.patch), [source/ELF proof and limits](../evidence/SOURCE-ELF-PROOF.md), [record/parser contract](RECORD-CONTRACT.md), [complete pins/commands](../evidence/handoff.json), [focused checks](../evidence/focused-checks.json), [PLAN isolation](../evidence/plan-isolation-receipt.json).

The one first-winner record stores original start, last already-existing clock sample, iteration count, idle/WFVLDCLR/explicit-other wait ID, and final readiness/result. It adds no raw MMIO snapshot. Native code shows no publication under ADC/regmap IRQ-save locks; the known battery property callback returns before the drain. No observation of that record means UNKNOWN, including a record never drained or a dropped publication. Publication is attempted once with no drain retry.

Kernel/out remain independently copied at `{i['remote_root']}/{{kernel,out}}`; new vmlinux SHA `{b['artifacts']['vmlinux']['sha256']}` stays remote. Local Image.gz-dtb/config/genuine System.map.gz are in artifacts; uncompressed map SHA `{b['artifacts']['System.map']['sha256']}`.

Parent reference commands, **not executed here**:

```sh
python3 {R}/source/install.py --execute
python3 {R}/scripts/decode_boundary.py 'PARENT_CONSOLE_PAYLOAD.txt' --installed-full-sha256 {p['full_p10']['sha256']} --fresh-stock-boot-reference '<parent-fresh-reference>' --complete-console-reference '<parent-complete-horizon-reference>'
```

The installer retains every original delivered guard/reader, execute/Transport/Guard and adapter body; adb is 0755. The PLAN substituted only restricted in-memory public readers. Private backup/root-chain validation is pending in the parent's normal execution environment; it was not bypassed in delivered code. No new controller or endpoint.

The decoder retains strict original first-line/framing and calibration rules. The original stockproc preamble/raw/refusal remain untouched. Supply an honestly bound console payload separately; do not treat absent records as a unit or physical success. Synthetic decoder controls do not constitute physical calibration.

Parent owns **ONE** exact fullp10 readback/fresh-stock-boot/complete-console trial and verified stock return. A fired record plus correct sustained normal-policy compute/2M checksum and useful afterIRQ/MMC/finish observations may support this intervention, not hardware cause. A record without sustained progress is partial evidence; absence/negative/unknown cannot exclude poll/counter/MMIO/delay. Stop after the one trial, without automatic retuning, repeats, next variants or storage advance. WRET remains before C return, not proof of userspace resumption.
''')
(R/'README.md').write_text('''# Finite pwrap backstop

Question: can one independently consumed finite budget preserve the exact current pwrap deadline/recovery semantics while recording its first exhaustion?

Status: **one candidate delivered; STOP**. One incremental kernel build (-j8), zero helper compiles, five production-loop cases, focused source/ELF/preservation/parser checks, one restricted actual PLAN. No device access or physical trial. Owned SSH master closed; exact VM verified TERMINATED.

Important outputs: [handoff and candidate links](output/HANDOFF.md), [record contract](output/RECORD-CONTRACT.md), [budget derivation](evidence/BUDGET-DERIVATION.md), [complete source patch](source/changes.patch), [source/ELF proof](evidence/SOURCE-ELF-PROOF.md), [pins/commands](evidence/handoff.json), [checks](evidence/focused-checks.json).

Budget: 16,777,216 returned not-ready iterations; count is not wall time. Existing 10 ms deadline and final readiness behavior remain. Frozen helper/ramdisk/config/DT/bootargs/guards are preserved.

Continuation: do not rerun preparation/build/package/PLAN. Parent owns at most ONE separately bound physical trial and stock return. Missing or undrained records are UNKNOWN; no hardware-cause, userspace-resumption, exclusion or automatic storage-advance claim. No retune, repeat or additional loop variant. See handoff before any continuation.
''')
files={}
for tree in ['source','scripts','artifacts','output']:
 for pth in (R/tree).rglob('*'):
  if pth.is_file() and '__pycache__' not in pth.parts:files[str(pth.relative_to(R))]=dict(bytes=pth.stat().st_size,sha256=hashlib.sha256(pth.read_bytes()).hexdigest())
for pth in E.iterdir():
 if pth.is_file() and pth.name not in ['ARTIFACT-MANIFEST.json']:files[str(pth.relative_to(R))]=dict(bytes=pth.stat().st_size,sha256=hashlib.sha256(pth.read_bytes()).hexdigest())
files['README.md']=dict(bytes=(R/'README.md').stat().st_size,sha256=hashlib.sha256((R/'README.md').read_bytes()).hexdigest())
(E/'ARTIFACT-MANIFEST.json').write_text(json.dumps(files,indent=2)+'\n');print(json.dumps(dict(status=handoff['status'],full_p10=p['full_p10'],VM=handoff['vm']),indent=2))
