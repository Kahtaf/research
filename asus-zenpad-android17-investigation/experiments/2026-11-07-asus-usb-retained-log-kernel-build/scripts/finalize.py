from pathlib import Path
import hashlib,json
R=Path(__file__).resolve().parents[1]
def read(n):return json.loads((R/n).read_text())
build=read('evidence/build-receipt.json');status=read('evidence/build-status.json');pkg=read('evidence/packaging-receipt.json');plan=read('evidence/install-plan.json');iso=read('evidence/plan-isolation-receipt.json');delivery=read('evidence/remote-delivery.json')
assert status['status']=='complete' and status['compile_exit']==0 and len(status['commands'])==1
assert pkg['image']==delivery['image'] and pkg['full_p10']==delivery['full_p10']
assert plan['candidate_sha256']==pkg['image']['sha256'] and plan['full_p10_sha256']==pkg['full_p10']['sha256']
next_command=f'python3 -B {R}/source/install.py --execute'
receipt=dict(status='ONE_DIAGNOSTIC_KERNEL_BUILT_PACKAGED',compile_exit=0,build_attempts=1,make_invocations=1,image=pkg['image'],full_p10=pkg['full_p10'],kernel=build['artifacts']['arch/arm64/boot/Image.gz-dtb'],raw_Image=build['artifacts']['arch/arm64/boot/Image'],config=build['artifacts']['.config'],logger_after_sha256='8373baa301650d2bf3befe547df11a3079e22c51aec8a207de64eae0f1bb3348',patch_sha256='9d9790f13e837ab7569a706e790d99c372d69c3700e8767811723c0bdd0718fa',installer=str(R/'source/install.py'),plan=iso,vm_prefix='/srv/android/asus-usb-retained-log-kernel-build-20261107',no_device_card_adb_root_helper_private_input_access=True,no_cloud_lifecycle_changes=True,no_subagents=True,no_independent_review_or_broad_tests=True,physical_boot_proven=False,firmware_header_state='unobserved',actual_reset_cause='unobserved',full_OS_readiness_proven=False,next_parent_command=next_command,parent_next='Own one recovery-only trial and collect actual retained logs/report; installer itself never reboots.')
(R/'evidence/RECEIPT.json').write_text(json.dumps(receipt,indent=2)+'\n')
config=receipt['config'];kernel=receipt['kernel'];image=receipt['image'];full=receipt['full_p10']
(R/'README.md').write_text(f'''# Linux-owned retained-console diagnostic kernel

Question: can the guarded Linux-owned retained-console initialization produce diagnostic checkpoints on this ASUS Android17 port?

Status: **one actual `make -j8 Image.gz-dtb` exited 0; one candidate packaged; one isolated PLAN_ONLY exited 0. Physical boot unproved.** This is a diagnostic build, not fullOS readiness. Firmware header state and actual reset cause remain unobserved.

Important outputs:

- `artifacts/candidate.img`: {image['bytes']} bytes; SHA-256 `{image['sha256']}`.
- `artifacts/Image.gz-dtb`: {kernel['bytes']} bytes; SHA-256 `{kernel['sha256']}`.
- `artifacts/resolved.config`: {config['bytes']} bytes; SHA-256 `{config['sha256']}`. Entire config is byte-identical to the baseline.
- Full p10: {full['bytes']} bytes; SHA-256 `{full['sha256']}`. It remains on the VM at `/srv/android/asus-usb-retained-log-kernel-build-20261107/artifacts/candidate.p10.raw`; the root installer constructs these exact bytes locally.
- `source/install.py`, `source/install.diff`, `source/package_probe.py`, exact patch and final logger source.
- `evidence/RECEIPT.json`, `build-status.json`, `build-receipt.json`, `changed-source-pins.json`, `original-selected-inputs.json`, `log-summary.json`, `packaging-receipt.json`, `install-plan.json`, `plan-isolation-receipt.json`, and `remote-delivery.json`.

Only patch SHA-256 `9d9790f13e837ab7569a706e790d99c372d69c3700e8767811723c0bdd0718fa` was applied with fuzz 0, no offsets and no compile corrections. Logger preimage `15c4e2069326c7e2ecd2679240983913fc51122f5149be215e4707cb76de0a64`; postimage `8373baa301650d2bf3befe547df11a3079e22c51aec8a207de64eae0f1bb3348`. Source was independently copied with ordinary `cp -a`, no hardlinks to baseline, into the owned prefix. Output and TMPDIR were fresh. Address space was unlimited; no build supervisor timeout. Baseline selected inputs remained unchanged. No full source-tree rehash, source fix, rebuild, independent review, or repeated host cases.

The actual compiled gzip Image stream and decompressed Image are byte-preserved in the candidate. V2 markers 00/01 and later 05/06 are present. Only inherited `/chosen` bootargs/initrd metadata is repackaged in the DT. Wrapped ramdisk is byte-identical, SHA-256 `51a6d8deb3368c8b8a10d6d730ca21c6b157fda5f940d5ba7cdcb2d2a6788e46`. Original diagnostic init/report behavior and stock header/address contract remain. Header and chosen cmdline are exactly:

```text
androidboot.selinux=permissive bootopt=64S3,32N2,64N2 build_version=3 console=null maxcpus=1
```

Initrd cells remain `0x44000000..0x4404e898`. No watchdog, timer, reservation, charging, radio, audio, or other settings changed.

The installer changes only actual candidate/full-p10 SHA, actual length, profile and the appended exact previously observed preimage `c9d4506c90fa12f6a77a5e34368312307903eb9e0c04d47d5461f2e455b062e3`. `execute()`, `Transport`, `Guard`, and both legacy adapters remain byte-identical; all allowed preimages remain.

To honor this worker's prohibition on private-input/root-helper access, `scripts/plan_only.py` called the delivered installer's actual PLAN branch exactly once with in-memory substitutions for the two inherited restricted dependency readers. It used the pinned public baseline candidate for header geometry. It blocked socket/subprocess/device/private/helper access. It validated the actual candidate/full-p10 hashes, length and preserved header contract. It did **not** validate private stock backups or root dependency hashes; root execution retains all original checks. The delivered installer source was not modified by this isolation.

Continuation: root alone runs the following under its standing authorization, then owns one recovery-only reboot, safe normal return and collection of actual retained log and fresh report. This installer does not reboot:

```sh
{next_command}
```

Do not rerun `scripts/run_build.py` or `scripts/build.py`: an existing owned attempt is refused. Full source/out/build logs remain under `/srv/android/asus-usb-retained-log-kernel-build-20261107`. Large artifacts need not be fetched. `SHA256SUMS` pins this small local public delivery. No device, card, ADB, root-helper or private-input access, cloud lifecycle changes, other-worker/AOSP edits, or subagents occurred.
''')
files=sorted(p for p in R.rglob('*') if p.is_file() and p.name!='SHA256SUMS')
size=sum(p.stat().st_size for p in files)
assert size<32*1024*1024,size
(R/'SHA256SUMS').write_text(''.join(hashlib.sha256(p.read_bytes()).hexdigest()+'  '+str(p.relative_to(R))+'\n' for p in files))
print(json.dumps(dict(delivery_bytes=size,receipt=str(R/'evidence/RECEIPT.json'),next_parent_command=next_command)))
