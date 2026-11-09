# Opus review: can driver init plus the exclusive Alpine startup prove a BMA255 baseline?

2026-11-08. Read-only. I did not run any tablet, SSH, ADB, USB, sysfs or ioctl operation, did not access calibration, and changed no helper, config, profile, root image or package. The only new artifacts are this report and `sources/accelerometer-baseline-opus/running-kernel-strings.txt`, which is ignored. That file holds strings extracted offline from **our own capsule kernel**. The capsule manifest records that kernel as byte-identical to original BOOT.

## Verdict

**No.** The lead fails, and it fails for reasons more basic than the missing getters:

1. **The retained source is not the running driver.** The argument "exact original driver init" depends on source we now know differs from the binary.
2. **The running binary is the SENSORHUB build.** Its accelerometer data and enable paths go through the MD32 co-processor. Nothing in the Alpine startup boots MD32. So under the source model, an activation could not return a sample, and it would leave cached state changed. If MD32 is somehow running, the hub state is opaque and adds a possible kernel spin.

So there is no bounded activation, sample and restore plan to give. **Keep the current portrait baseline and do not write `accactive`, `accenablenodata`, `accdelay`, `accbatch`, `cpsopmode`, `md32_boot` or any `/dev/gsensor` ioctl.**

## 1. Source/binary identity is broken, and this is shown offline

Kernel in the capsule (`artifacts/recovery-capsule/recovery-alpine-stock-ram.img`):
- Wrapped kernel sha256 `b0e5d48b…0880`; payload `a3e696eb…4a4b`, matching the manifest.
- `Linux version 3.18.35 (android@mec15) … #1 SMP PREEMPT Thu Aug 9 12:33:25 CST 2018`. That date matches the firmware name `Z380M_V5.3.20_08092018`.
- The retained tree comes from `Kernel_V4_7_0.zip` / `V380M_V4.7.0.tar.gz`, archive-dated 2017-01-05. It is about 19 months and one major firmware line older than the binary.

String evidence (exact counts in the sources file):

| Retained source claims | Running binary |
|---|---|
| `bma255_i2c_probe` creates `/sys/android_gsensor` with `value/state/gs_cali/resetcali/atd_caligs/power` (`bmc156_acc.c:2986–2994`), plus error text `alp.D : attr gsensor dev_attr_*  fail` | `android_gsensor` **0**, `resetcali` **0**, `atd_caligs` **0**, that error text **0**. This explains the "source/live discrepancy": the code is not in this build. |
| No startup calibration work | Binary-only `mxt_wq` and `alp.D : start sw_cali delay workqueue!!`, located between the probe's batch-registration and create-attribute errors. Also `get cali_sw fail/success`, `Load/Use Defalut Calibration Data` at KERN_ERR, and `/persist/gs_cali.ini`. Probe schedules a **delayed calibration-loading work item that is not in our source**. |
| `CONFIG_CUSTOM_KERNEL_SENSORHUB=y` in the retained defconfig (not proof of the build) | Hub branch confirmed from the binary itself: `BMA255_SCP_SetPowerMode`, `gsensor_irq_handler`, `[Gsensor] … Power on bma255 error %d!` (hub `get_data` only, source line 2671), `Out of index!`, `SCP_sensorHub_req_send fail`. The non-hub `set_delay` error `Set delay parameter error` is **absent**. |

`/proc/config.gz` is absent on the device and the image has no `IKCFG_ST`, so this string evidence is the best build-configuration evidence available. It is still not a function-by-function decompilation. The `accel.c` attribute names match the binary (`accactive accenablenodata accdelay accbatch accflush accdevnum`), but their show/store bodies cannot be proved from this source either.

**Consequence:** "kzalloc'd common context plus probe" is a property of V4.7.0 source. In the binary, probe also starts at least one asynchronous calibration work item. Its effect on hub or cached state, and when it runs, cannot be derived from any retained source. The lead's premise, that exact original init is known, does not hold.

## 2. The SENSORHUB data path needs MD32, and the Alpine startup never boots it

Using the retained hub branch as the best available model, since the binary strings show that branch is compiled:

- `bmc156_acc_enable_nodata` → `BMA255_SCP_SetPowerMode` → `SCP_sensorHub_req_send` → `md32_ipi_send` (`bmc156_acc.c:543–582, 2585–2604`; `SCP_sensorHub.c:766–830`; `md32_ipi.c:85–130`).
- `bmc156_acc_get_data`, called by the common poll work, **only** issues a hub `GET_DATA` in this build (`2668–2694`). There is no AP-side I2C sample on the `m_acc_input` path.
- MD32 boots only when something writes `md32_boot` (`md32_helper.c:645–671`, loading `/etc/firmware/md32_{d,p}.bin`), or on `PM_POST_HIBERNATION`. Stock Android does this write itself: `write /sys/class/misc/md32/md32_boot 1` (saved stock init inventory, `private/live/root-inventory-details.txt:1269`). Android's dmesg also shows live `SCP_sensorHub_req_send` traffic. `scripts/recovery-init.sh`, `recovery-sysinit.sh` and the goodix overlay have no md32/gsensor/accel writer. The bootstrap symlinks `/etc/firmware/md32_*.bin` into the root, so the firmware is *available*, but nothing loads it.

What a "bounded" `accactive=1 … 0` would do on this boot under that model, if MD32 is not running (`sw_rstn==0`):
1. `enable_nodata(1)`: `SetPowerMode(true)` sets the enable map bit and `gsensor_scp_en_status=true` **before** sending. The IPI returns ERROR, so `sensor_power` stays false. `acc_real_enable` retries (`accel.c:179–187`). On the retry the status already equals the request, so nothing is sent, the call returns 0, and `sensor_power = enable_status = true` **with no hardware change** (cpsopmode still reports suspend).
2. The poll timer starts at the unknown current delay (200 only if nothing changed it). Each poll's `GET_DATA` fails, logging `get acc data fails!!` and `md32_ipi_send: MD32 not enabled`. **Zero samples, by construction.**
3. `accactive=0`: `enable_nodata(0)` with `sensor_power==true` sends a disable. ERROR returns, so `sensor_power` **stays true**. The final state differs from the baseline: cached `sensor_power` true against hardware in suspend, and `enable_status` false. Later `ReadSensorData`/`CompassReadData`/`get_data` paths branch on that cached flag. The activation is not reversible, even in the retained model.

If MD32 is running for an unknown reason, `md32_ipi_send(…, wait=1)` busy-waits on `HOST_TO_MD32_REG` while holding `md32_ipi_mutex` (`md32_ipi.c:120–125`). Hub delay, batch and internal subscribers (step counter, face-down and shake are configured) cannot be read. A wedged firmware would turn the "restore" write into a hang inside `cancel_work_sync`. This is also outside any provable baseline.

Booting MD32 to make the path work is **not** a reversible bounded step. It starts a co-processor for the rest of the boot. On `SCP_INIT_DONE`, `gsensor_irq_work` sends cust data and then **`BMA255_CUST_ACTION_RESET_CALI`** to the hub (`bmc156_acc.c:2129–2191`), which is a calibration action. It also enables the other hub sensors' lifecycle. This is excluded.

## 3. What the lead *does* establish (keep, but it is not enough)

- Userspace exclusivity is plausible and auditable. No sensor service, Android framework or udev daemon runs; `mdev -s` only creates nodes; the GUI is explicit Goodix. Evdev open has no sensor hook (`accel.c:562–594`), so even a stray evdev reader changes nothing. With a process and package audit, this could support "no userspace writer since boot".
- Hardware `cpsopmode` 2 before and after the passive read is consistent with init putting the chip in suspend. As instructed, it is not a software baseline.

Neither point covers kernel-autonomous writers in the binary (the `mxt_wq` calibration work, hub-notify work, suspend/resume callbacks with `PM_AUTOSLEEP=y`). Neither repairs the data path, which depends on MD32.

## 4. Smallest missing observable/contract

In priority order. The first is the gate, and none of these is an activation.

1. **Is MD32 running on this boot?** The passive way is the kernel log and `/proc/interrupts`: no driver callback, no sensor operation.
   - In `dmesg`, look for `md32_ipi_send: MD32 not enabled`, `[MD32]` and `[sensorHub]` lines, and the binary-only `alp.D : get cali_sw fail/success` (KERN_ERR, so recorded unless the ring buffer has wrapped).
   - In `/proc/interrupts`, look at the MD32/IPC line count.
   - Avoid reading `md32_boot` itself. In source its show function is a pure `readl`, but this binary is not proven to match source.
   - **If MD32 is not running (the expected result):** the stock `m_acc_input` path cannot deliver samples on Alpine without booting the hub. Active accelerometer work should stop and be documented as "requires a qualified MD32/hub lifecycle", which is out of scope today. A getter does not fix this.
2. **Exact-version source** for firmware 5.3.20.0 (Aug 2018), covering `bmc156_acc.c`, `accel.c`, `SCP_sensorHub.c` and `md32_*`. Without it, no show/store body can be relied on, including the `mxt_wq` calibration work. I found no public download in one search ([GSMArena Z380M](https://www.gsmarena.com/asus_zenpad_8_0_z380m-8474.php) and similar pages only confirm the device). The firmware listing ([firmwarefile.com](https://firmwarefile.com/?p=56604)) names `V5.3.20_08092018`, which matches the binary date. ASUS's support "source code" section for Z380M is the place to check. Do not substitute the P024/Z380KL kernels ([postmarketOS P024](https://wiki.postmarketos.org/wiki/Asus_ZenPad_8_(asus-p024))); that is different hardware.
3. Only if 1 shows MD32 running *and* 2 is obtained would it be worth asking for truthful getters for `is_active_data`, `is_active_nodata`, `is_polling_run` and delay, plus the hub `gsensor_scp_en_map`/`status`. The kernel ABI exposes none of these, so this would need a kernel change, which is out of scope.

## Instruction to the parent

- Do not activate. Keep native portrait, no rotation marker, and the passive `observe-stock-accelerometer.py` as the only sensor tool.
- Optional next live step, metadata only: a bounded `dmesg` grep for `md32|MD32|sensorHub|Gsensor|ACCELEROMETER|cali_sw` and the `/proc/interrupts` MD32 line. Record the result in an evidence receipt. No other reads.
- Record in MEMORY: the running kernel is a 2018 SENSORHUB build that differs from V4.7.0 source (no `android_gsensor`; extra `mxt_wq` sw_cali work). The accelerometer data path needs MD32, which Alpine does not boot. Auto-rotation from the stock sensor stack is blocked on a hub lifecycle that is not in scope.
