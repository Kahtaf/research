# Authorized continuation: final link failure

The one config gate passed and the exact ancestor TEE selection compiled. The one authorized Image continuation returned exit 2 at `vmlinux` linking:

```text
met_tracing_record_cmdline -> tracing_record_cmdline (undefined)
virtual_sensor_set_cur_state -> setMaxbrightness (undefined)
battery_meter_dts_remove -> unregister_netdevice_notifier (undefined)
battery_meter_dts_probe -> register_netdevice_notifier (undefined)
```

These are the only four unique undefined symbols in the actual log. The accompanying CALL26 relocation errors refer to those same unresolved symbols. The failed callers and relocations are preserved from the genuine `drivers/built-in.o`; no relinking or rebuilt ELF was used to obtain evidence. The DEVAPC object now selects TEE as intended, so the original missing-type compiler blocker was passed. No claim is made about final linked keepers, runtime TEE or physical protection.

Command that ran once in this continuation (record only; **do not rerun**):

```sh
make -C /srv/android/asus-minimal-platform-build-r2-20261108/kernel \
  O=/srv/android/asus-minimal-platform-build-r2-20261108/out \
  ARCH=arm64 CROSS_COMPILE=aarch64-linux-gnu- HOSTCC=gcc HOSTCXX=g++ \
  LOCALVERSION=-minplat -j8 Image.gz-dtb
```

Existing warning flags, including -Werror, remained. The process finished naturally without a new memory cap or timeout-kill. The failed initial make and this authorized continuation are both retained. No native helper command was run here. Its exact previous executable and genuine minimal initramfs were independently copied and hash-checked; no C source, signal behavior, compute result, IRQ parser or helper logging variant was introduced.

The one olddefconfig was run with the copied native `out/scripts/kconfig/conf`, `ARCH=arm64`, `SRCARCH=arm64`, `KERNELVERSION=4.9.337`, owned srctree/objtree/config paths and the parent requested input. It completed with no warnings. Exact input, output, diff, ancestor mapping and provenance are preserved in the gate receipt. Source hashing after the build found only the entry tag's authorized config-hash metadata difference. The partial DT is byte-identical to the initial attempt, including exact chosen initrd geometry and enabled secure carveout.

No complete Image.gz-dtb, final vmlinux or System.map exists. No genuine recovery candidate, full-p10 hash, installer/profile, PLAN or decoder test result is fabricated. The staged successful-build verification script was never run because its required successful Image did not exist. Candidate/linked acceptance remains unperformed.

The parent-supplied physical recovery pin remains `d78e6ddd7f4a555201515df3aef6d8d7f15203c20e3b8d201ea7eb2f4c5df081`; it was not freshly observed. No original installer/controller/private/root/backup/readback guard or adapter was modified. The copied `source/adb` remains 0755. No ADB, tablet, root or private target logs were accessed.

The exact VM `PROJECT_REDACTED/us-central1-a/PROJECT_REDACTED`, ID `8549823276971553556`, was stopped after evidence collection. `evidence/after.stdout` verifies TERMINATED. Only `/tmp/asumr2-1108`, this continuation's owned SSH master, was closed. Partial out remains in the independent remote prefix for later authorized inspection.

Parent read-only commands:

```sh
cat 2026-11-08-asus-minimal-platform-build-r2/evidence/config-gate.json
cat 2026-11-08-asus-minimal-platform-build-r2/evidence/link-failure-receipt.json
cat 2026-11-08-asus-minimal-platform-build-r2/evidence/partial-DT-receipt.json
```

Any repair, consumer add-back, keeper change or further make invocation needs a new parent decision. None is proposed or dispatched automatically. The same experiment's first physical trial has not happened. This host link failure supplies no physical liveness, walltime, storage/fullOS, protection or unique fault-location result.
