# Parent integration and exact target build

These commands are a handoff, not executed actions. The full-build Astra owner
alone may mutate/build the active VM kernel/platform. First review the 11-file
patch and LOCKS-AND-CALLERS. Preserve current images and all previous spikes.

Kernel chain:

1. `717bb3c9e13ce573cfdd2dda856debd27a0fa17f`.
2. Battery-gauge `0001-asus-p00a-measured-battery.patch`.
3. Main-battery-SOC `0002-asus-p00a-checked-main-battery-soc.patch`.
4. This spike's `0003-asus-p00a-checked-charging-integration.patch`.

The two prerequisite patches are frozen in source with hashes in
`evidence/patch-manifest.json`. This new kernel patch is separate from the SOC
spike's Android hardware/interfaces patch numbered 0003; both are needed in
their respective repositories. Retain that spike's Android Health and framework
startup/error patches and device service integration.

Local reproduction, entirely within this spike:

```sh
python3 scripts/check_host.py
python3 scripts/verify_source.py
```

`verify_source.py` builds a fresh owned subset, sequentially applies all three
kernel patches with strict whitespace checks and compares exact source hashes.
It is not a complete Linux source tree or a substitute for ARM64 linking.
`make_patch.py` regenerates a deterministic diff from the frozen after-SOC
subset and staged overlay; no timestamps enter the patch.

On the parent's case-sensitive Linux tree, after reviewing other owners' edits:

```sh
python3 scripts/apply_kernel.py /srv/android/asus-android17/kernel-bpf-fd
python3 scripts/apply_kernel.py /srv/android/asus-android17/kernel-bpf-fd --apply
```

The default only checks. The helper verifies base ancestry, exact overlapping
file hashes and unchanged DT/model guards. Partial application or overlapping
changes require a reviewed rebase, not `--reject`, forced copying or bypassing
the manifest. Already-applied exact results are idempotent.

Use a new output; do not rebuild over the known candidate. Run these commands
under the existing build owner, with its normal log capture and exit markers:

```sh
set -eu
kernel_src=/srv/android/asus-android17/kernel-bpf-fd
charge_out=/srv/android/asus-android17/build-checked-charging-r1
test ! -e "$charge_out"
mkdir "$charge_out"
cp /srv/android/asus-android17/build-bpf-fd/.config "$charge_out/.config"
"$kernel_src/scripts/config" --file "$charge_out/.config" \
    --enable ASUS_P00A_BQ25896 \
    --enable ASUS_P00A_BATTERY_DIAGNOSTIC \
    --enable ASUS_P00A_MAIN_BATTERY_SOC \
    --disable MTK_MULTI_BAT_PROFILE_SUPPORT \
    --disable MTK_BATTERY_LIFETIME_DATA_SUPPORT
make -C "$kernel_src" O="$charge_out" ARCH=arm64 \
    CROSS_COMPILE=aarch64-linux-gnu- HOSTCC=gcc HOSTCXX=g++ olddefconfig
python3 - "$charge_out/.config" <<'PY'
import pathlib, sys
s = pathlib.Path(sys.argv[1]).read_text()
for name in ('ASUS_P00A_BQ25896','ASUS_P00A_BATTERY_DIAGNOSTIC',
             'ASUS_P00A_MAIN_BATTERY_SOC','MTK_SMART_BATTERY','MTK_PMIC','OF'):
    assert 'CONFIG_'+name+'=y' in s, name
for name in ('MTK_MULTI_BAT_PROFILE_SUPPORT','MTK_BATTERY_LIFETIME_DATA_SUPPORT',
             'POWER_EXT','MTK_INTERNAL_CHARGER_SUPPORT','MTK_BQ24296_SUPPORT',
             'MTK_BQ25601_SUPPORT'):
    assert 'CONFIG_'+name+'=y' not in s, name
PY
make -C "$kernel_src" O="$charge_out" ARCH=arm64 \
    CROSS_COMPILE=aarch64-linux-gnu- HOSTCC=gcc HOSTCXX=g++ -j8 \
    drivers/misc/mediatek/power/mt8163/asus_p00a/bq25896.o \
    drivers/misc/mediatek/power/mt8163/asus_p00a/battery_diag.o \
    drivers/misc/mediatek/power/mt8163/pmic_mt6323.o \
    drivers/power/supply/mediatek/battery/battery_meter.o \
    drivers/power/supply/mediatek/battery/battery_common.o
make -C "$kernel_src" O="$charge_out" ARCH=arm64 \
    CROSS_COMPILE=aarch64-linux-gnu- HOSTCC=gcc HOSTCXX=g++ -j8 Image.gz-dtb
sha256sum "$charge_out/.config" "$charge_out/arch/arm64/boot/Image.gz-dtb"
```

Inspect linked symbols for `asus_p00a_charge_publish`, `asus_p00a_charge_request`,
`asus_p00a_charge_source_changed`, `asus_p00a_bc12_type` and the existing
`Charger_Detect_Init/Release`; resolve compile/link or configuration findings
before claiming readiness. Verify the USB PHY supplies the expected strong
implementation, not just the generic weak placeholder. Preserve the original
board/battery NTC routes, all profile/Qmax numbers and cover/OTG routing.

Inspect the actual compiled DTB, not only source: `asus,allow-battery-charging`
must remain absent. No enable-property patch is supplied. Record source,
resolved config, compiler, patch, Image and DTB hashes. Parent then rebuilds
Health/library/framework/full images through its own runner, using a newly
versioned kernel artifact. This task does not own that deployment.
