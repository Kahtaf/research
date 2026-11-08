# Parent/build-owner handoff

These are instructions, not executed VM/build/device operations. Do this only
after the graphics owner releases live-source/build ownership. Preserve other
agents' changes and retain the known kernel/config/image as separate artifacts.

## Apply order

1. Start with physical kernel revision
   `717bb3c9e13ce573cfdd2dda856debd27a0fa17f` on the case-sensitive Linux builder.
2. Apply the unchanged prerequisite from
   `2026-11-06-asus-android17-battery-gauge/patches/0001-asus-p00a-measured-battery.patch`.
   Its own `scripts/apply.py` performs its original revision/hash preflight.
3. From a copied version of **this** spike, run:

   ```sh
   python3 scripts/apply_kernel.py /srv/android/asus-android17/kernel-bpf-fd
   python3 scripts/apply_kernel.py /srv/android/asus-android17/kernel-bpf-fd --apply
   ```

   The default is read-only. It rejects a missing prerequisite, overlapping
   edits, changed charging policy, changed main DT or changed measurement routes.
   Already-applied exact results are idempotent. All ten changed/new kernel
   files must match `evidence/patch-manifest.json`. Other owners' overlapping
   defconfig/DT/Kconfig changes require an explicit reviewed merge/rebase; do
   not force the patch or copy the overlay over a live tree.
4. Apply `patches/0003-android17-health-checked-snapshot.patch` in
   `/srv/android/lineage24/hardware/interfaces`, based on
   `a0221f11248a924532444fc7de85d41998b9fe1e`.
5. Apply `patches/0004-android17-battery-startup-errors.patch` in
   `/srv/android/lineage24/frameworks/base`, based on
   `696a5773fa284f53429dbb6c3e5dcc96bf5bd0b3`.
6. Merge the complete `integration/device/asus/p00a/health/` directory into the
   parent's reviewed full product. No candidate/full file was edited here.

For each platform repository, run `git apply --check --whitespace=error-all`
before `git apply --whitespace=error-all`. Inspect conflicts against its current
owner's work. The strict local replay covers those pinned source versions,
not arbitrary subsequent revisions.

## Kernel configuration and build

Keep the inherited BPF/configfs/PSI/zram and all other platform settings. The
required changes to an existing output `.config` are:

- `CONFIG_ASUS_P00A_MAIN_BATTERY_SOC=y` — new.
- `CONFIG_ASUS_P00A_BATTERY_DIAGNOSTIC=y` — retain the prerequisite measurements.
- `CONFIG_MTK_MULTI_BAT_PROFILE_SUPPORT=n` — no ASUS alternate-pack ID model.
- `CONFIG_MTK_BATTERY_LIFETIME_DATA_SUPPORT=n` — no ASUS aging tables.

Keep `CONFIG_ASUS_P00A_BQ25896=y`, `CONFIG_MTK_SMART_BATTERY=y`, `CONFIG_MTK_PMIC=y`
and `CONFIG_OF=y`. The existing board header selects `SOC_BY_SW_FG`. Do not
activate POWER_EXT, CUST_CAPACITY_OCV2CV_TRANSFORM, a hardware/cover gauge or
charger mode. The SOC code fails compilation for unsupported model combinations.

Changing defconfig alone does not change an existing configured output. Use a
fresh output, following the previous build's known toolchain:

```sh
kernel_src=/srv/android/asus-android17/kernel-bpf-fd
soc_out=/srv/android/asus-android17/build-main-battery-soc-r1
test ! -e "$soc_out"
mkdir "$soc_out"
cp /srv/android/asus-android17/build-bpf-fd/.config "$soc_out/.config"
"$kernel_src/scripts/config" --file "$soc_out/.config" \
    --enable ASUS_P00A_BATTERY_DIAGNOSTIC \
    --disable MTK_MULTI_BAT_PROFILE_SUPPORT \
    --disable MTK_BATTERY_LIFETIME_DATA_SUPPORT \
    --enable ASUS_P00A_MAIN_BATTERY_SOC
make -C "$kernel_src" O="$soc_out" ARCH=arm64 \
    CROSS_COMPILE=aarch64-linux-gnu- HOSTCC=gcc HOSTCXX=g++ olddefconfig
grep -E 'CONFIG_(ASUS_P00A_MAIN_BATTERY_SOC|ASUS_P00A_BATTERY_DIAGNOSTIC|MTK_MULTI_BAT_PROFILE_SUPPORT|MTK_BATTERY_LIFETIME_DATA_SUPPORT)' "$soc_out/.config"
make -C "$kernel_src" O="$soc_out" ARCH=arm64 \
    CROSS_COMPILE=aarch64-linux-gnu- HOSTCC=gcc HOSTCXX=g++ -j8 Image.gz-dtb
```

Verify the resolved flags before the full build. Rebuild/link `battery_meter.o`
(including `asus_p00a_soc.inc`), `battery_common.o`, `battery_diag.o`,
`pmic_mt6323.o`, and `mtk_ts_battery.o`. Capture real build status, logs, compiler,
config and final image/DTB hashes. A host harness is not object/link validation.

The compiled DT must retain channels VBAT=6, VSYS=7, charger=4, battery NTC=5,
`swchr_power_path=1`, the 16.9k/30k/1.8V battery NTC network, all four 104-pair
profiles, and the eight original Qmax values. **Keep
`asus,allow-battery-charging` absent. No charge limits are changed by this series.**

## Health merge and Android build

Copy all five files plus the header in the staged Health directory:
`Health.cpp`, `BatterySnapshot.cpp`, `BatterySnapshot.h`, `Android.bp`, `health.rc`,
`health.xml`. The service/module/manifest names stay the same. Android.bp adds
`BatterySnapshot.cpp` to the existing service target. Retain the full product's
existing package inclusion and SELinux/ueventd policy; verify the system health
service can read the main battery nodes. No extra sysfs writer is needed.

Merge all components together:

- `Health::getHealthInfo` remains **final**. A new protected, status-returning
  `ReadBatterySnapshot` hook lets the device reject invalid mandatory readings.
  Generic products keep the default successful hook.
- Existing callback registration, death handling and valid callbacks remain
  active. The standard `update()` error path propagates STATUS_UNKNOWN and
  skips only failed aggregate delivery. No callback is replaced with a no-op.
- `HalHealthLoop` retries failed aggregates instead of its previous fatal CHECK.
- Device main waits for actual initialized SOC before registering IHealth.
  All battery paths, even unsupported optional fields, are pinned to `battery`.
- The framework registration update catches `ServiceSpecificException` as the
  normal scheduled update already does. BatteryService waits for its first
  valid sample rather than proceeding with null after its old one-second wait.
  This also covers a failure between preflight and initial callback.

Build `android.hardware.health-service.asus-p00a`, its changed
`libhealth_aidl_impl`, and the changed framework services (`services` /
`services.jar`) in the parent's selected Android 17 full-product environment.
Then rebuild the full images through the parent-owned runner with the new
kernel artifact. Inspect the installed service, manifest and framework jar;
building only the HAL omits the startup-race fixes. The standalone device source
cannot compile against the unpatched Health header.

A permanently invalid battery intentionally withholds normal startup; it is
not represented as absent, Charging, 50%, or 100%. Later faults retain the last
framework-delivered sample while the HAL reports errors in calls/dumps/logs;
the framework receives a new sample when the real model recovers. This is the
platform's error/callback contract, not a fault-status field in HealthInfo.
Current/counter/full-charge individual getters remain unavailable; optional
aggregate numeric defaults must not be interpreted as measured current or
validated full-charge capacity.

There is no proprietary pad daemon, private calibration upload, charging opt-in
or device installation in this handoff. Compilation and controlled runtime
validation are still required before claiming a working persistent tablet.
