# One minimal-platform build — stopped on compiler dependency failure

Question: can the accepted reduced-consumer configuration build and package with its retained protection closure?

Status: **STOPPED after the single kernel build failed. No retry, kernel repair, package, installer/profile, isolated PLAN, decoder or target action.** The static ARM64 helper compiled once and its genuine minimal initramfs was generated. The exact VM is verified `TERMINATED`; only this spike's SSH master was closed. Original preparation, calibrated ancestor and current installation remain preserved.

The concrete blocker is retained `MTK_DEVAPC_DRIVER=y` together with reviewed `MTK_IN_HOUSE_TEE_SUPPORT=n`. This exposes a pre-existing non-TEE branch in `drivers/misc/mediatek/devapc/mt8163/devapc.c`: line 122 uses undefined `E_MASK_DOM`, line 123 uses undefined `APC_ATTR`, and lines 134/139/164 produce unused-function errors under the existing `-Werror`. Its local `devapc.h` does not declare those types. This is a substantive compile dependency failure, so the accepted stop rule applies. No driver stub, warning suppression, TEE re-enable or keeper removal was attempted.

Review [BUILD-STOP.md](BUILD-STOP.md), [the exact compiler log](evidence/kernel-compile.log), [failure receipt](evidence/failure-receipt.json), and [failing source snapshot](evidence/failure-source/devapc.c). Source/config changes after frozen preparation are in [after-preparation.patch](source/after-preparation.patch). These are build-input changes, not a recovery candidate.

| Genuine input/output | SHA256 / value |
|---|---|
| Corrected config, unchanged after make | `add8f8e85e0fe007364da835f2d45d91663551876387ba4a695e410d4c1cc7bb` |
| Corrected helper C, authoritative parent bytes | `b9551c582306936e913f7d746cd62de6ffbcb708e2e4ab150893ff5790033037` |
| Static AArch64 `/init` | `37e9e2a2d73447947fb33e57e9513fa6079517b571f5a41bc58fbb91f84633fc`, 772248 bytes |
| Board DTS after parent overlay, before derived geometry | `48f9b0537ee19b3f21727378044df4bb46fbff6add0b60535709d446cf3ae821` |
| Final board DTS source, with exact initrd bounds | `2d0c95c12d0fce6629dede4e0eff6590725de9ef5dbbb1f0acc0f3e63fca41b6` |
| Source/run UUID | `a60fca94-e760-4ce5-a790-5c9a818ce406` |
| Actual gzip initramfs payload / initrd interval | 319962 bytes; `0x44000000..0x4404e1da` |
| Kernel attempt | One `Image.gz-dtb`, max `-j8`, exit 2; no Image or vmlinux |

The initramfs contains only static `init` plus `dev` and `proc` directories. `/init` creates the kmsg character node in RAM. Its compiled compute loop contains exactly the 2M unsigned workload, without calls; independent host arithmetic gives final state `0x2093acf8`, checksum `4296231513146560`. The compiled SIGALRM handler consists only of address/value setup, a flag store and return. Main links the alarm/sigsuspend pattern and two low-frequency direct clock syscalls. It retains normal scheduler/one-CPU checks, ordinary retained printk stage records and normal reboot on success/clear error. No target execution or calibrated timing claim. See [helper verification](evidence/helper-verification.json).

The initrd end was derived before the kernel build. Only two assembly end-literal pairs changed from `0x4403f007` to `0x4404e1da`, retaining the guard structure and calibrated 0xc0 admission. The end remains 3874342 bytes below console `0x44400000`. Chosen bounds match that payload; addresses/reservations otherwise remain unchanged. Entry metadata uses the actual corrected config hash and explicitly labels the DT hash `dts-source`.

Independent ordinary source copy: `/srv/android/asus-minimal-platform-build-20261108`; partial out remains there. The metadata free-space/copy/overlay receipt is [copy-overlay.json](evidence/copy-overlay.json). No full out copy or shared mutable hardlinks. Prepared source pins and calibrated ancestor Image/config were reverified unchanged in [stop receipt](evidence/stop-receipt.json).

Continuation: parent reviews the DEVAPC/non-TEE dependency before any further change or build authorization. Do not rerun this attempt's scripts or construct a package from partial output. The thermal/PMIC/BQ inhibition, BAT/SOC/notifications, CPUFreq/SPM/HPS/idle and watchdog/power-key configurations remain explicitly retained, but final linked bindings and physical protection were not qualified. This host compiler result says nothing about device liveness or the previous physical stall's cause. No automatic add-backs or second build.
