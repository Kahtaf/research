# One direct-clock-syscall RAM control

Question: does the same finite runnable RAM PID1 loop complete when every CLOCK_MONOTONIC read explicitly enters the kernel syscall?

Status: **STOPPED — compile SSH connection timed out; no candidate produced.** Source scope, one actual production-parser GIC-0 check, and exact public kernel/base checks passed. SSH readiness succeeded at 35.25s on probe 3, but the separate compile SSH connection timed out before remote script execution. No AArch64 compiler invocation or helper fetch occurred. No automatic retry was made. The exact VM was stopped in the lifecycle's finally block and verified TERMINATED.

No device/ADB/install/reboot action, private factory payload or raw kernel log access. No kernel/product build, new resources or cap changes. Parent alone owns nearby Power readiness, actual installation/trial and interpretation. No next userspace variant is prepared.

Fresh helper identity: `ASUS49-SYSCLOCK run=f0c3c82c-d639-4d8a-90f2-155fd4224ceb`. Kernel entry UUID remains `23cdb057-295c-4b42-9ade-a4324162ad02`.

## Important outputs

- `source/init.c`, `source/init.diff`: complete scoped control and meaningful source diff against the corrected format-fix helper.
- `evidence/source-scope-receipt.json`: exact declared delta; all other functions, main, handler and bounds preserved.
- `evidence/parser-check.json`, `parser-harness.c`, `parser-compile.log`, `parser-run.log`: one host check extracting the exact production number/timer_line bodies. GIC-0/Level input reconstructs the expected numeric output. No broad matrix or emulation.
- `evidence/kernel-base-receipt.json`: exact public corrected base/kernel/config/gzip/raw pins, short bootargs and chosen end verified.
- `evidence/compile-local.stderr.log`: preserved failure, `ssh: connect to host IP_REDACTED port 22: Operation timed out`.
- `evidence/compile-dispatch.json`, `vm-lifecycle.json`, `vm-after.stdout.log`, all readiness/start/stop logs: single dispatch, exact lifecycle and verified TERMINATED.
- `evidence/final-status.json`, `installer-status.json`, `original-preservation.json`, `SHA256SUMS`: explicit incomplete status, unmodified installer/adapters and immutable original public files.

`artifacts/` is empty. Static ELF, candidate/package preservation, ramdisk-size and one default PLAN checks could not run without the compiled helper. No candidate image/full/helper hash exists. `source/install.py` is an unmodified copy of the base installer; `source/install.diff` is intentionally empty. It is **not a prepared new-candidate installer**. The scripts retain one-dispatch/one-package guards. Do not erase the failure receipts or rerun the compile lifecycle automatically.

## Exact helper delta

Source SHA-256: `550dc7514d5bf95ca49440ef3dcc110f1e4594e99e9414f28ed3e287207312c6`.
Base source SHA-256: `d6cf66e19d1f2638941b0f14b0a3428db74b6867bf1761c3491d14188db8e4ad`.

Only fresh UUID/tag, `<sys/syscall.h>`, an int wrapper returning `(int)syscall(SYS_clock_gettime,CLOCK_MONOTONIC,t)`, routing initial clock_sample and every observe-loop read through that wrapper, one explicit clock.path record, and exact known-controller GIC-0 acceptance alongside GIC/GICv2. The once-only marker is `kernel-syscall:syscall(SYS_clock_gettime);vDSO-bypassed`, phase=observe. It describes this source's path, not the old helper's path.

SIGALRM setup/handler including its one write and errno restoration, 2,000,000 iteration cap, 1,500,000,000 ns counter target, all before/after snapshots, all error logic, sole normal reboot and failure behavior remain exact. No sleeps/yields or per-iteration logs. The wrapper preserves the 0 or -1/errno contract and caller capture/restoration. Handler write is a confounder if comparisons are unmatched; this control deliberately preserves it, so a positive result could not be attributed to removing the write.

GIC-0 correction changes controller recognition only. Optional Level/Edge, numeric fields, privacy and read bounds remain exact: <=32768 bytes, eight <=4096-byte reads, 256 complete lines, eight arch_timer records, 16 CPU counters. Malformed raw text remains unlogged.

## Evidence and interpretation

The three requested public trial evidence files are copied under `evidence/prior-*`. Physical Linux4.9 and RAM PID1 are proven. Prior initial read returned 0.674848768; its finite runnable loop produced no alarm marker/post-loop/after snapshot. Complete before IRQ read was 4502B with two arch_timer lines, both parser-rejected. No zero-IRQ or stagnant-counter claim follows. Actual nohlt and printk.devkmsg=on were verified, so kernel hardware idle entry is unnecessary to reproduce that boundary. Saved PL reset32 meaning remains UNKNOWN.

The supplied read-only review identifies a conditional mismatch: ARM_ARCH_TIMER_VCT_ACCESS=n disables EL0 CNTVCT, while archdata.vdso_direct is true unless the out-of-line workaround is actually activated. vDSO sequence retry precedes fallback checking; kernel clock reading also has sequence retry. This motivates one cheaper explicit-syscall control before retained kernel checkpoints. It does not prove vDSO was actually used previously. No kernel cause is asserted.

If a future separately authorized completion of this candidate yields physical loop/after records, inspect actual samples, stop reason, alarm flag and comparable accepted IRQ counts. That would distinguish the explicit syscall control under changed kernel-entry/timing overhead; it would not prove the old helper used vDSO or prove a particular vDSO bug. Fresh identity/path marker and accepted GIC-0 output add small logging overhead. Preserve handler-write matching when interpreting any positive result.

If this control physically retains the same unfinished boundary, a userspace clock fast path is unnecessary to reproduce it. Parent then uses bounded retained kernel-side checkpoints. No further userspace variant is prepared. No IRQ/counter/root-cause conclusion follows from missing post-loop records. Kernel clock sequence retry remains possible.

Counter-target means >=1.5 nominal counter seconds, not wallclock calibration. Iteration cap below one nominal second without an alarm flag is not proof of a missed alarm. Increasing comparable IRQ counters prove recorded servicing only. Handler marker or flag=1 proves handler entry; marker write result is unchecked. Limits cannot bound a stuck syscall, and SIGALRM shares the timer/IRQ subsystem under observation.

## Exact base and compile pins

| Public base component | Bytes | SHA-256 |
|---|---:|---|
| Corrected format-fix candidate.img | 7974912 | `13033865fe5c88952efe2d5e429246a76a08689be604fb89a4776afa990c4ab8` |
| Current supplied full p10 | 16740352 | `88f79cc02d71bfe0708d6be77d66d06d3107befcee3d5d0225ecc8134942f617` |
| Compiled Image.gz-dtb | 7713482 | `97b7e1199d607f852bf52ff7766e8aa079fee92986cd3d473b765a45adbf45fb` |
| Resolved config | 126443 | `708a88175ea777c09410000dfe5cf562ccbf764955eb9deaadda7326d0a966e1` |
| Runtime gzip stream | 7649861 | `29437894a38cba034db136aa5ea3f1c930edf6ff6abcfc14a4dd652ceeebc491` |
| Runtime raw Image | 17342976 | `60755a9910450cb0303157017ddb4f6ff08874fca32bf70298bb5a91d5450381` |

Base is corrected format-fix, not original worker R1. Supplied current p10 pin is not a fresh physical read. Chosen end is 0x4403e975; start 0x44000000. Existing guard remains 0x44000000..0x4403f007, compressed payload limit 258055B. Exact command line: `bootopt=64S3,32N2,64N2 build_version=3 console=null maxcpus=1 printk.devkmsg=on nohlt`. All original public sources/scripts/artifacts were verified unchanged. Adapters copied with copy2; source/adb remains 0755. Entire base installer, including execute/Transport/Guard, is unchanged.

Prepared assembler uses those exact pins, preserves kernel gzip/raw/config/hardware DT/bootargs/addresses/MTK wrappers, updates helper/cpio and only necessary ramdisk header/hash and chosen initrd end, and stops if compressed initramfs exceeds 258055B. Prepared installer generation appends current 88f79... admission and changes only candidate/full hashes, actual image size and profile. These transformations have **not been executed or validated for a candidate**.

Intended pinned compiler: `aarch64-linux-gnu-gcc (Ubuntu 13.3.0-6ubuntu2~24.04.1) 13.3.0`, SHA `cd90adc7801f4595267f61a5d25bd3a0c6beb2f9f1f107ab919a97a12972dc9a`, flags `-static -Os -s -ffunction-sections -fdata-sections -Wl,--gc-sections -Wall -Wextra`. No compiler actually started in this attempt. Unchanged product-kit remote.py SHA `c22884576a780cbb1ddf5e1b02f0b6e9d6eb5c25f8d9bc82fb077543f05cf4ab`.

Exact VM PROJECT_REDACTED, id8549823276971553556, project PROJECT_REDACTED, zone us-central1-a, IPIP_REDACTED; labels owner=kahtaf,purpose=rom-build,expires=2026-11-12 verified before/running/after. One authorized start/stop cycle. Existing readiness limit 180s; first two failures retained; third readiness succeeded at 35.250319s. Separate compile SSH timed out. Fresh intended owned remote prefix `/srv/android/asus-linux49-direct-clock-syscall-20261107-f0c3c82c` was never reached/created by that connection. VM final status TERMINATED.

## Continuation instructions

Parent should review preserved failure and source scope. A further compile transport attempt requires an explicit parent decision under the no-automatic-retry constraint; preserve this attempt rather than clearing its dispatch guard. Do not switch kernel, guard, compiler, resources, helper behavior or create another userspace variant.

After separately authorized compile completion, essential static-ELF/package checks and one isolated actual default PLAN remain required. The inherited PLAN harness denies subprocess/socket/private/device access, substitutes a pinned public stock header and public-only source pins in memory, and leaves delivered input readers/guards intact. It does not validate private backup/root dependency manifests; parent owns fresh full checks.

Intended parent install command **only after a valid package and completed checks; NOT READY and NOT EXECUTED**:

```sh
python3 -B 2026-11-07-asus-linux49-direct-clock-syscall-control/source/install.py --execute
```

No installation should proceed from this incomplete spike. Installer normally performs guarded install/readback without reboot. Parent alone owns Power readiness, physical identity/preimage checks, installation, trial, public evidence collection/interpretation and verified stock return. Stop here; no retry or next userspace variant was prepared.
