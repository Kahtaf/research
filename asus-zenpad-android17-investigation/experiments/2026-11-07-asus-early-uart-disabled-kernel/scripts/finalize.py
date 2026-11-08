from pathlib import Path
import hashlib,json
R=Path(__file__).resolve().parents[1]
def read(n):return json.loads((R/'evidence'/n).read_text())
build=read('build-receipt.json');status=read('build-status.json');pkg=read('packaging-receipt.json');plan=read('install-plan.json');iso=read('plan-isolation-receipt.json');delivery=read('remote-delivery.json');gate=read('dependency-gate.json');linked=read('linked-image-assertions.json')
assert status['status']=='complete' and status['compile_exit']==0 and len(status['commands'])==1 and status['compile_attempts']==1
assert pkg['image']==delivery['image'] and pkg['full_p10']==delivery['full_p10'] and delivery['actual_readback']
assert plan['candidate_sha256']==pkg['image']['sha256'] and plan['full_p10_sha256']==pkg['full_p10']['sha256']
assert linked['absent_in_nm_and_System_map'] and gate['non_console_config_changes']==[]
next_command=f'python3 -B {R}/source/install.py --execute'
receipt=dict(status='ONE_EARLY_UART_DISABLED_DIAGNOSTIC_KERNEL_BUILT_PACKAGED',compile_exit=0,compile_attempts=1,make_compile_invocations=1,olddefconfig_exit=0,config_delta=build['config_delta'],image=pkg['image'],full_p10=pkg['full_p10'],kernel=build['artifacts']['arch/arm64/boot/Image.gz-dtb'],raw_Image=build['artifacts']['arch/arm64/boot/Image'],config=build['artifacts']['.config'],logger_sha256='8373baa301650d2bf3befe547df11a3079e22c51aec8a207de64eae0f1bb3348',source_edits=[],baseline_selected_unchanged=True,full_tree_rehash=False,linked_8250_early_path_absent=True,installer=str(R/'source/install.py'),plan=iso,vm_prefix='/srv/android/asus-early-uart-disabled-kernel-20261107',no_device_card_adb_root_helper_private_input_access=True,no_cloud_lifecycle_or_process_inspection=True,no_other_worker_or_AOSP_changes=True,no_subagents=True,no_independent_review_or_broad_tests=True,physical_boot_proven=False,causality_proven=False,cache_epoch_proven=False,UART_failure_mechanism_proven=False,full_OS_readiness_proven=False,next_root_command=next_command,root_next='Fresh USB identity/report absence; p10-only install/readback; one USB recovery entry; log collection. Worker did not install or reboot.')
(R/'evidence/RECEIPT.json').write_text(json.dumps(receipt,indent=2)+'\n')
image=pkg['image'];kernel=receipt['kernel'];full=pkg['full_p10'];config=receipt['config']
(R/'README.md').write_text(f'''# ASUS early UART disabled diagnostic kernel

Question: does disabling the unused 8250 serial console remove the early UART path associated with actual cached core0 PC `0xffffff8008f31adc`?

Status: **one native `make -j8 Image.gz-dtb` exited 0; one candidate packaged; one isolated PLAN_ONLY exited 0. No install or reboot.** Cached PC resolves in the exact baseline layout to `serial8250_early_in+0x78`, `ldr w0,[x0]`, in UPIO_MEM32 readl. Cache epoch and UART failure mechanism remain unproved; this is a candidate blocker, with no causality or full boot claim. Public finding evidence is copied under `evidence/cached-public-finding/`. Existing trial results remain in the separate trial spike.

Important outputs:

- `artifacts/Image.gz-dtb`: {kernel['bytes']} bytes; SHA-256 `{kernel['sha256']}`.
- `artifacts/resolved.config`: {config['bytes']} bytes; SHA-256 `{config['sha256']}`.
- `artifacts/candidate.img`: {image['bytes']} bytes; SHA-256 `{image['sha256']}`.
- Full p10: {full['bytes']} bytes; SHA-256 `{full['sha256']}`. Actual readback is recorded. Large file stays at `/srv/android/asus-early-uart-disabled-kernel-20261107/artifacts/candidate.p10.raw`; installer constructs the identical padded bytes locally.
- Guarded `source/install.py` and `source/install.diff`.
- `evidence/RECEIPT.json`, `config-delta.json`, `config.diff`, `dependency-gate.json`, `build-status.json`, `build-receipt.json`, `linked-image-assertions.json`, `original-selected-inputs.json`, `packaging-receipt.json`, `remote-delivery.json`, `install-plan.json`, and `plan-isolation-receipt.json`.

The only intentional change is `CONFIG_SERIAL_8250_CONSOLE=y -> n`. Actual olddefconfig naturally removes `SERIAL_EARLYCON`, `SERIAL_CORE_CONSOLE` (selected by the console), and `SERIAL_8250_FSL` (depends on the console). Exactly those four values changed y to n; no other config value changed. `SERIAL_8250=y`, `SERIAL_8250_MT6577=y`, and `SERIAL_CORE=y` remain. `FIX_EARLYCON_MEM=y`, an unconditional arm64 default, remains for the unchanged retained logger's `early_memremap` support. Kconfig/Makefile evidence and selected original source copies are included.

Source was independently copied using ordinary `cp -a`, with fresh out and TMPDIR, no hardlinks to baseline and no source edits. Selected baseline files and copied source hashes remained unchanged; no full-tree rehash. Unlimited RLIMIT_AS, same toolchain/command/release `LOCALVERSION=-g717bb3c9e13c-dirty`, no supervisor timeout, no build retry. Actual linked vmlinux nm plus System.map confirm `serial8250_early_in`, early setup/write and UART earlycon declarations absent. No 8250_early.o was built. Normal 8250/MT6577 symbols and early_memremap remain. This is a config/compile assertion, without simulation or physical testing. Full source/out/logs remain on the VM under the owned prefix; local log summary pins the actual build log.

Packaging preserves the actual compiled gzip Image and raw Image, v2 markers 00/01 and checkpoint strings 05/06. It applies only inherited chosen bootargs/initrd metadata; DT source and all other DT tokens remain unchanged. Same wrapped diagnostic ramdisk SHA-256 `51a6d8deb3368c8b8a10d6d730ca21c6b157fda5f940d5ba7cdcb2d2a6788e46`, v0 header, 2048-byte pages and stock addresses. Initrd remains `0x44000000..0x4404e898`. Header and chosen args are exactly:

```text
androidboot.selinux=permissive bootopt=64S3,32N2,64N2 build_version=3 console=null maxcpus=1
```

Installer specialization changes only candidate/full-p10 hashes, actual image length, profile, and appends prior observed full-p10 preimage `4fb2f280ba90e9e1487b3728056a67ccd4883f918cc81a1145c100a3eb999a26`. All existing preimages remain. `execute()`, `Transport`, `Guard`, and legacy adapters are byte-identical to the immediate baseline.

One isolated PLAN invokes the actual delivered main() branch with in-memory replacements for the two inherited restricted input readers, using the pinned public baseline candidate for stock header geometry. Audit isolation blocks private/device/root-helper reads, sockets and subprocesses. Actual candidate/full-p10 hashes, length and preserved header contract pass. Private stock backups and root dependency hashes were not validated by this worker; delivered input/source guards remain unchanged for root execution.

Continuation: root owns fresh USB identity/report absence, p10-only install/readback, one USB recovery entry and actual log/report collection. Next root command, under its standing authorization:

```sh
{next_command}
```

This installer does not reboot. Do not rerun prepare/build scripts: existing owned attempts are refused. No device, card, ADB, root-helper, private-input access, cloud lifecycle/process inspection, other-worker/AOSP changes, subagents, independent review or broad suites occurred. Original BOOT/SYSTEM/DATA, frozen artifacts and existing VM/disks/labels were not modified by this worker. Local public delivery stays below 32 MiB and is pinned by `SHA256SUMS`.
''')
files=sorted(p for p in R.rglob('*') if p.is_file() and p.name!='SHA256SUMS');size=sum(p.stat().st_size for p in files);assert size<32*1024**2,size
(R/'SHA256SUMS').write_text(''.join(hashlib.sha256(p.read_bytes()).hexdigest()+'  '+str(p.relative_to(R))+'\n' for p in files))
print(json.dumps(dict(delivery_bytes=size,receipt=str(R/'evidence/RECEIPT.json'),next_root_command=next_command)))
