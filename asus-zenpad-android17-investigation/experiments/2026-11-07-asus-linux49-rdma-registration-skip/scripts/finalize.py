"""Write concise handoff and scoped delivery pins after verification and VM stop."""
from pathlib import Path
import gzip, hashlib, json
R=Path(__file__).resolve().parents[1]
E=R/'evidence'
sha=lambda d:hashlib.sha256(d).hexdigest()
p=json.loads((E/'packaging-receipt.json').read_text())
b=json.loads((E/'build-receipt.json').read_text())
d=json.loads((E/'compiled-dt-modules.json').read_text())
branch=json.loads((E/'registration-branch-check.json').read_text())
assert branch['status']=='PASS'
assert json.loads((E/'after.stdout').read_text())['status']=='TERMINATED'
assert json.loads((E/'install-plan.json').read_text())['mode']=='PLAN_ONLY'
mapraw=gzip.decompress((R/'artifacts/System.map.gz').read_bytes())
assert sha(mapraw)==b['artifacts']['System.map']['sha256']
assert len(mapraw)==b['artifacts']['System.map']['bytes']
B=R.parent/'2026-11-07-asus-linux49-retained-clock-capture'
assert (R/'scripts/decode.py').read_bytes()==(B/'scripts/decode.py').read_bytes()
warnings=[s for s in (E/'compile-1.log').read_text().splitlines() if 'warning:' in s]
handoff=dict(status='DELIVERED_ONE_DIAGNOSTIC_HEADLESS_RDMA_REGISTRATION_SKIP',physical_GO=False,physical_trial=False,VM_status='TERMINATED',capture_UUID=p['run_uuid'],candidate=p['candidate'],full_p10=p['full_p10'],System_map=dict(uncompressed=b['artifacts']['System.map'],gzip=dict(bytes=(R/'artifacts/System.map.gz').stat().st_size,sha256=sha((R/'artifacts/System.map.gz').read_bytes()))),compile_attempts=1,max_jobs=8,warnings=len(warnings),parent_PLAN=f'python3 -B {R}/source/install.py',parent_install=f'python3 -B {R}/source/install.py --execute',expected_skip_lines=d['expected_skip_lines'],no_device_or_private_access=True,no_next_build=True)
(E/'handoff.json').write_text(json.dumps(handoff,indent=2)+'\n')
(R/'README.md').write_text(f'''# DIAGNOSTIC / headless RDMA registration skip

Question: does omitting only RDMA0/1 IRQ registration clear the previously observed PID1 loop boundary?

Status: **one candidate built, packaged and checked; VM TERMINATED.** No device/ADB/root/install/reboot/private factory/raw target-log access, physical GO, or full-OS fix. Parent owns one authorized physical trial, eventual manual Power fallback, collection and interpretation. Stop after this candidate; no splits or next build.

- [candidate.img](artifacts/candidate.img): {p['candidate']['bytes']} bytes; SHA-256 `{p['candidate']['sha256']}`.
- [candidate.p10.raw](artifacts/candidate.p10.raw): {p['full_p10']['bytes']} bytes; SHA-256 `{p['full_p10']['sha256']}`.
- Fresh entry/capture UUID: `{p['run_uuid']}`. Unchanged helper UUID: `{p['helper_uuid']}`.
- Genuine [System.map.gz](artifacts/System.map.gz), with compressed and uncompressed pins in [handoff.json](evidence/handoff.json). Large ELF/output remain on the VM at `/srv/android/asus-linux49-rdma-registration-skip-20261107-d140b2bf`.

[Source diff](source/changes.patch) changes only `disp_is_intr_enable()` and same-width entry/capture metadata. RDMA0/1 return 0 after one diagnostic log using existing mapped `dispsys_irq[]`; all other predicate values are unchanged. Register mapping, `irq_of_parse_and_map`, IRQ assignments, other requests and initialization remain intact. No added MMIO or RDMA/GIC/device-enable modification.

Both RDMA nodes are present in the actual compiled DT. Expect exactly these two lines if the display probe reaches the matches; IRQ values must come from runtime, not the DT cells:

```text
{chr(10).join(d['expected_skip_lines'])}
```

These are expected lines, **not runtime registration receipts**. [Compiled DT module inventory](evidence/compiled-dt-modules.json) lists every compatible match. DT status alone would not suppress this direct node lookup.

Checks passed: actual remote driver matched local prototype before patch; source pre/post pins; actual ELF skip branches before `request_threaded_irq`; one extracted predicate behavior comparison; original capture sources/hooks, 5952-byte layout and decoder preserved; config, compiled hardware DT, runtime DT and entire wrapped ramdisk byte-identical. Actual source uses `#if 0` for legacy `disp_init_irq()` registrations (not the brief's `!CONFIG_OF`); config is `CONFIG_OF=y`, and linked legacy init has no registration call. Other scoped display request sites are DSI TE, with no active RDMA bypass found. See [branch receipt](evidence/registration-branch-check.json), [build receipt](evidence/build-receipt.json), [linked capture](evidence/linked-capture.json), and [packaging receipt](evidence/packaging-receipt.json).

One `make -j8 Image.gz-dtb` succeeded; {len(warnings)} compiler warning lines are preserved in `evidence/compile-1.log`. Independent `cp -a --reflink=auto` source/output copies preserve the frozen base and nested repositories; no full-tree hash audit or clean/product build. Readiness, build and fetch used the same owned SSH master with compiler/fetch TCP fallback disabled. Initial readiness timeout and inspection-tool failure are preserved in `evidence/`; no blind redispatch occurred. Exact VM identity and final TERMINATED state are in lifecycle evidence.

Packaging preserves load addresses/reservations, initrd `[0x44000000,0x4403e9d8)`, guard through `0x4403f007`, and exact header/chosen arguments:

```text
{p['bootargs']}
```

The entry tag's inherited `dt=94cde...` is historical reference provenance, not current runtime-DT identity. Its `base=` now pins the actual frozen capture Image. Actual Image.image_size, ranges and LK geometry passed existing checks. The current supplied full-p10 `4b474d6e714871dcefbba9510ff3d25f66e13147171ae39b0fa670c7cd70402e` was appended to admission, not freshly read here. [Installer diff](source/install.diff) changes only hashes, actual size, profile and that preimage; `execute`, `Transport`, `Guard`, dependencies and adapters are preserved, with `adb` copied mode 0755.

Exactly one actual default PLAN passed the truthful isolated public-reader harness; delivered guards/readers are unchanged. Private inputs and physical admission remain the parent's checks. Parent commands:

```sh
python3 -B {R}/source/install.py
python3 -B {R}/source/install.py --execute
```

Installer does not reboot. After the parent obtains its complete console through the established reader, decode locally:

```sh
python3 -B {R}/scripts/decode.py /absolute/path/to/parent-complete-console.txt --uuid {p['run_uuid']} > /absolute/path/to/parent-private-decoded.json
```

Require exact full-p10 readback, fresh entry/capture UUID, both skip lines, complete committed capture rows and loss=0. Missing/torn/dropped capture is UNKNOWN. A counter sample belongs to its completed token/parent; an unfinished clock capture can reflect preemption. The cached display LASTPC epoch is unestablished and no storm or clock-core cause is proved.

Parent outcomes: loop counter reaches the ≥1.5 s target with after-counts and SIGALRM flag → this diagnostic exposure cleared the observed boundary, subject to timing/logging perturbation; same boundary with verified skips → negative for RDMA registration necessity in this exposure; no PID1 → inconclusive boot dependency. Neither outcome establishes universal causality, a display fix or shipping GO.

Continuation: perform only that parent trial and interpret its admitted evidence. Do not rebuild from this handoff. To symbolize offline, decompress the pinned map locally; no VM restart is needed for addresses.
''')
paths=[p for folder in ['source','scripts','artifacts'] for p in (R/folder).rglob('*') if p.is_file() and '__pycache__' not in p.parts]
paths += [R/'README.md', E/'handoff.json', E/'registration-branch-check.json']
(E/'delivery-pins.json').write_text(json.dumps({str(p.relative_to(R)):dict(bytes=p.stat().st_size,sha256=sha(p.read_bytes())) for p in sorted(paths)},indent=2)+'\n')
print(json.dumps(handoff,indent=2))
