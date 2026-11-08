from pathlib import Path
import hashlib,json,struct,sys
R=Path(__file__).resolve().parents[1];sys.path.insert(0,str(R/'source'))
import bootformat as b
pack=json.loads((R/'evidence/packaging-receipt.json').read_text());build=json.loads((R/'evidence/build-receipt.json').read_text());plan=json.loads((R/'evidence/install-plan.json').read_text());status=json.loads((R/'evidence/build-status.json').read_text())
assert status['compile_exit']==0 and len(status['commands'])==1
assert plan['mode']=='PLAN_ONLY' and plan['device_contacted'] is False and plan['reboot'] is False
assert plan['candidate_sha256']==pack['image']['sha256'] and plan['full_p10_sha256']==pack['full_p10']['sha256']
header,kernel,ramdisk,_=b.parse_image((R/'artifacts/candidate.img').read_bytes());raw,dt=b.ungzip(kernel[512:])
text_offset,image_size,flags=struct.unpack_from('<3Q',raw,8);assert raw[56:60]==b'ARM\x64'
ka,ra,ta=struct.unpack_from('<I',header,12)[0],struct.unpack_from('<I',header,20)[0],struct.unpack_from('<I',header,32)[0]
assert ka==0x40080000 and ra==0x44000000 and ka+image_size<ra and ra+len(ramdisk)-512<0x44400000 and ta==0x4e000000
layout=dict(ARM64_magic=raw[56:60].hex(),text_offset=hex(text_offset),image_size=image_size,flags=hex(flags),kernel_address=hex(ka),kernel_end_conservative=hex(ka+image_size),ramdisk_address=hex(ra),ramdisk_end=hex(ra+len(ramdisk)-512),retained_range='0x44400000..0x44480000',tags_address=hex(ta),page_size=2048,overlap=False)
(R/'evidence/layout.json').write_text(json.dumps(layout,indent=2)+'\n')
def pin(p):return dict(bytes=p.stat().st_size,sha256=hashlib.sha256(p.read_bytes()).hexdigest())
files={str(p.relative_to(R)):pin(p) for p in [*sorted((R/'artifacts').iterdir()),R/'source/early-retained-checkpoint.patch',R/'source/install.py'] if p.is_file() and p.name!='SHA256SUMS'}
receipt=dict(status='DELIVERED_ONE_FULL_BUILD_PACKAGED_PLAN_ONLY_NO_PHYSICAL_TRIAL',remote_prefix='/srv/android/asus-early-retained-kernel-probe-20261107',build_exit=status['compile_exit'],full_build_invocations=1,max_jobs=8,rlimit_as=status['rlimit_as'],kernel_release=build['release'],kernel_version=build['version'],timestamp=build['build_timestamp'],files=files,config_delta={},resolved_config_sha256=build['artifacts']['.config']['sha256'],package=pack,plan=plan,original_selected_inputs_unchanged=True,source_copy='cp -a preserved retained-trace/kernel only; fresh out',compile_corrections=[],early_api_assessment='early-api-assessment.json',hardware_contact=False,physical_linux49_execution_proven=False,charging_permission='absent',next_action='Parent owns fresh PROBE absence, guarded install, one recovery reboot, normal return and complete last_kmsg collection.')
(R/'evidence/RECEIPT.json').write_text(json.dumps(receipt,indent=2)+'\n')
size=sum(p.stat().st_size for p in R.rglob('*') if p.is_file());assert size<32*1024**2,size
(R/'README.md').write_text(f'''# Early retained checkpoint kernel probe

Question: can the full retained-trace e9 Linux 4.9 kernel publish a guarded record before paging and retain it when switching to the linear mapping?

Status: **one full independent Image+DTB build exited 0; actual recovery candidate packaged; default PLAN_ONLY passed once. No physical trial.** Stock retention/reader transport was physically proven by the parent in the retained-report-control spike; this does not prove 4.9 execution or guard passage.

Important outputs:

- `artifacts/candidate.img`: {pack['image']['bytes']:,} bytes, SHA-256 `{pack['image']['sha256']}`.
- `artifacts/Image.gz-dtb`: {files['artifacts/Image.gz-dtb']['bytes']:,} bytes, SHA-256 `{files['artifacts/Image.gz-dtb']['sha256']}`.
- `artifacts/resolved.config`: {files['artifacts/resolved.config']['bytes']:,} bytes, SHA-256 `{files['artifacts/resolved.config']['sha256']}`. Entire resolved file is byte-identical to the baseline.
- Full padded p10: {pack['full_p10']['bytes']:,} bytes, SHA-256 `{pack['full_p10']['sha256']}`. Kept on VM as `/srv/android/asus-early-retained-kernel-probe-20261107/artifacts/candidate.p10.raw`; parent installer constructs these exact padded bytes locally in memory.
- Compiled DT SHA-256 `{pack['dt_before']['sha256']}`; packaged DT SHA-256 `{pack['dt_after']['sha256']}`. Only chosen bootargs and initrd cells change from the compiled DT.
- `source/early-retained-checkpoint.patch`, `source/final/`, `source/install.py`, `source/install.diff`; `evidence/RECEIPT.json`, `build-status.json`, `build-receipt.json`, `Image.gz-dtb.log`, `packaging-receipt.json`, `install-plan.json`, `early-api-assessment.json`, `early-api-source.json`, `layout.json`, and `remote-delivery.json` record actual inputs and outputs.

Release: `4.9.337-asus-p00a-experimental-g717bb3c9e13c-dirty`; actual build version `{build['build_timestamp']}` (#1 SMP PREEMPT). No Git metadata manufactured.

The only source change is the exact three-file supplemental patch SHA-256 `2991e2f9fdab79af5d87783fec3f3e7f0721cb8911df9f172c355d272489643d`, applied with `--fuzz=0` after all three exact preimage pins matched, with no offsets or compile corrections. The source was copied only from preserved `/srv/android/asus-retained-trace-kernel-probe-20261107/kernel` using ordinary `cp -a`, without hardlinks or old output reuse. Existing retained v1 hooks, timer clk13m fix, prior port work and all other source/hardware settings are inherited. One `make -j8 Image.gz-dtb` ran with a fresh owned `out`, complete unchanged config, and unlimited RLIMIT_AS. Full source, output and actual build log remain under the new VM prefix. Original selected input pins remained unchanged; no full-tree rehash.

The early API check found flat-DT calls valid before unflattening, completed memblock/initrd/reserved-memory setup at this call site, and normal-cacheable `early_memremap`/unmap support through generic ARM64 headers. Every original guard and the payload-before-size PoC publication remain; extra bounds limit the first record and reason area to one 256 KiB mapping. The temporary pointer is cleared and mapping removed before paging. Late initialization revalidates the guards and exact early record. No OEM headers were invented or bounds weakened.

The same static diagnostic SD-report ramdisk is preserved byte-for-byte: SHA-256 `{pack['wrapped_ramdisk']['sha256']}`. It uses `PROBE.TXT`, run ID `dbbb6afb-dd70-4c35-961e-9c977d7164a8`, and the inherited 60-second normal reboot lifecycle. Header and complete chosen bootargs remain:

```text
{pack['header_cmdline']}
```

The DT's 32-bit initrd cells describe the wrapper-stripped compressed payload `0x44000000..0x4404e898`; no initrd bootarg. Actual new compiled Image bytes are preserved in the package. MTK wrappers, Android v0/2048 layout, addresses and all other header/DT fields remain under the inherited contract. No finalBOOT/product/audio kernel substitution; charging permission remains absent.

The installer is minimally specialized from the retained-probe adapter: exact new image length, candidate/full-p10 hashes and profile, plus only the exact parent-known preimage `a0e4856da4138dd401461add3104005fca67cf495da1a605c02392244dd757f8`, fully readback verified in parent run `a1c59781-d116-4fb2-a6f8-35fa37871452`. Every existing allowed preimage remains. `execute()` and `Transport` and both legacy adapters remain byte-identical. Full guarded readback, shared lock, bounded inverse, uncertainty-stop behavior and sibling source dependencies remain. Actual default PLAN_ONLY ran once, with `device_contacted=false`; no `--execute` was run.

## Parent continuation

Parent alone verifies fresh report absence, runs the guarded installer, owns one recovery reboot and safe normal return, then immediately collects complete actual last_kmsg plus exact candidate/install/boot identity and fresh SD report. Installer path: `{R/'source/install.py'}`. It does not reboot. No added review gate or alternative candidate.

Expected records:

```text
ASUS-e9-retained-v2 00 arm64_memblock_init returned; before paging_init
ASUS-e9-retained-v2 01 paging_init returned; trace ready
```

Inherited later v1 markers 02..06 and printk capture remain. Record 00 without 01 proves reaching the pre-paging checkpoint, but can still allow failure during paging, later guard revalidation or retention. No record permits earlier failure or guard refusal and does not prove nonexecution. Stock retention evidence proves the stock path only.

This worker made no device/card/ADB/root-helper call, private logs/factory/calibration/DATA access, active AOSP/product/source/out edit, other-owner process inspection/signals, cloud lifecycle action or subagent. The separate vendor-BPF worker is untouched. VM labels/disks and previously scheduled November 8 ~14:54 UTC stop were not changed.

For continuation, use the actual delivered candidate and receipts. `scripts/build.py` refuses an existing owned source/output and must not be rerun as a second build. `source/package_probe.py` reproduces packaging offline without compilation. Local public delivery is below 32 MiB; padded p10 stays on the VM.
''')
print(json.dumps(dict(ready=True,image=pack['image'],full_p10=pack['full_p10'],local_bytes=size,layout=layout)))
