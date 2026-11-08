from pathlib import Path
import hashlib,json,struct
R=Path(__file__).resolve().parents[1]
pack=json.loads((R/'evidence/packaging-receipt.json').read_text());build=json.loads((R/'evidence/build-receipt.json').read_text());plan=json.loads((R/'evidence/install-plan.json').read_text())
assert plan['mode']=='PLAN_ONLY' and plan['device_contacted'] is False and plan['reboot'] is False
assert plan['candidate_sha256']==pack['image']['sha256'] and plan['full_p10_sha256']==pack['full_p10']['sha256']
def pin(p):return dict(bytes=p.stat().st_size,sha256=hashlib.sha256(p.read_bytes()).hexdigest())
files={str(p.relative_to(R)):pin(p) for p in [*sorted((R/'artifacts').iterdir()),R/'source/retained-boot-trace.patch',R/'source/timer-clock.patch',R/'source/diagnostic.config',R/'source/install.py']}
receipt=dict(status='DELIVERED_FULL_COMPILE_AND_PLAN_ONLY_NO_PHYSICAL_TRIAL',remote_prefix='/srv/android/asus-retained-trace-kernel-probe-20261107',build_exit=0,max_jobs=8,kernel_release=build['release'],kernel_version=build['version'],timestamp=build['build_timestamp'],files=files,config_delta=build['config_delta'],package=pack,plan=plan,original_selected_inputs_unchanged=True,prior_276_port_delta_preserved_by_independent_full_source_copy=True,hardware_contact=False,physical_linux49_boot_proven=False,physical_go=False,next_action='Parent verifies fresh PROBE.TXT absence, executes preserved installer, owns one adb reboot recovery and immediate stock last_kmsg collection.')
(R/'evidence/RECEIPT.json').write_text(json.dumps(receipt,indent=2)+'\n')
(R/'artifacts/SHA256SUMS').write_text(''.join(f"{v['sha256']}  {p}\n" for p,v in files.items() if p.startswith('artifacts/')))
(R/'README.md').write_text(f'''# Retained trace + APXGPT diagnostic kernel probe

Question: can the full e9 Linux 4.9 fixture with the delivered retained startup logger and named APXGPT clk13m selection produce a recoverable execution boundary?

Status: full independent build exit 0; packaged recovery-only SD-report probe; actual default PLAN_ONLY passed. Physically untested. No device, ADB/USB, card, root helper, private DATA/calibration/table access, cloud lifecycle, process management or other-job contact occurred.

Important outputs:

- `artifacts/Image.gz-dtb`: {files['artifacts/Image.gz-dtb']['bytes']:,} bytes, SHA-256 `{files['artifacts/Image.gz-dtb']['sha256']}`.
- `artifacts/resolved.config`: SHA-256 `{files['artifacts/resolved.config']['sha256']}`. The only resolved delta is `CONFIG_ASUS_P00A_RETAINED_BOOT_TRACE=y`.
- `artifacts/candidate.img`: {pack['image']['bytes']:,} bytes, SHA-256 `{pack['image']['sha256']}`.
- `artifacts/candidate.p10.raw`: {pack['full_p10']['bytes']:,} bytes, SHA-256 `{pack['full_p10']['sha256']}`.
- `evidence/RECEIPT.json`, `build-status.json`, `build-receipt.json`, `changed-source-pins.json`, `original-selected-inputs.json`, `log-summary.json`, `packaging-receipt.json` and `install-plan.json` preserve actual pins and checks.
- `source/install.py` is the minimal preserved installer. `execute()` and `Transport` and both legacy adapters are byte-identical to the silent single-CPU parent. Its new actual image length/hashes and profile are bound; only full preimage `5c8926304eaf38bbe9e2d5e8750c89cda025ce376c0103d3589f416e213cb453` is added alongside inherited pins. Original `902b` remains admitted. The inherited Wi-Fi transport and sibling dependencies remain required.

Release: `4.9.337-asus-p00a-experimental-g717bb3c9e13c-dirty`. Actual new build timestamp: `{build['build_timestamp']}`. No Git metadata was manufactured. The existing full e9 source was copied with ordinary `cp -a` into `/srv/android/asus-retained-trace-kernel-probe-20261107/kernel`; all make/config outputs are in the new `out`. Full source/out/logs remain there. The previous 276 source port delta and e9 config are inherited intact; selected original source/config/Image/generated inputs were checked unchanged. No full-tree rehash sweep was performed. Original/frozen/active/AOSP/product sources and output were not changed. Build used `-j8` with all 16 CPUs available and no artificial memory cap.

Both exact delivered patches were applied: retained trace `a0efbb7dee1688b07b0accebb8ef7f22a183fd58752aad9447bf89f1ba78cdbb` and timer clock `13294c10548d583e7fa86a4010fd3455822e3ba012a001cb40a6ecb1378d0816`. The timer postimage is `0c9e26f54ecbbdd8d60c9ed35cbfb62820b6a515ef25d0750fd16c3834db2913`; named `clk13m` replaces index 0 while the separate bus gate remains. It is not a proven boot cause.

The exact unchanged static SD-report wrapped ramdisk is SHA-256 `51a6d8deb3368c8b8a10d6d730ca21c6b157fda5f940d5ba7cdcb2d2a6788e46`. It still reports actual getpid/uname, uses `PROBE.TXT`, UUID `dbbb6afb-dd70-4c35-961e-9c977d7164a8`, and the inherited 60-second lifecycle. Both header cmdline and complete chosen bootargs are exactly:

```text
androidboot.selinux=permissive bootopt=64S3,32N2,64N2 build_version=3 console=null maxcpus=1
```

There is no initrd token. The 32-bit DT initrd cells describe the wrapper-stripped compressed payload `0x44000000..0x4404e898`. The actual new compiled Image stream is unchanged in the package; the actual compiled DT changes only chosen bootargs and initrd cells. Android v0/2048 pages, other header bytes, addresses and MTK wrappers are preserved, with actual lengths/ID regenerated.

Continuation: the parent owns fresh PROBE.TXT absence verification and the physical trial. Only the parent may run:

```sh
python3 -B {R/'source/install.py'} --execute
```

That installer does not reboot. After verified install, parent owns ONE `adb reboot recovery`, the return to stock, and immediate stock `last_kmsg` collection with exact candidate/boot identity. Look for `ASUS-e9-retained-v1 01 paging_init returned; trace ready`, then markers 02..06 around setup_arch, IRQ and time_init. First marker is after paging and before IRQ/timer initialization. Missing markers can mean an earlier failure, refused memory/header guards, or lost retention; absence does not prove Linux never executed. Retention and startup remain physically untested. Parent-reported stock 3.18 SD probe works; e9 SD and independent USB probes have not produced a 4.9 report.

Only one actual default PLAN_ONLY was run. No execute command, reboot, physical GO, Android BOOT/SYSTEM/DATA product change, other kernel fix or subagent was used. The separate stock SD rescue worker/prefix remains untouched.
''')
print(json.dumps(dict(ready=True,image=pack['image'],full_p10=pack['full_p10'],release=build['release'],owned_bytes=sum(p.stat().st_size for p in R.rglob('*') if p.is_file()))))
