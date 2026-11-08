#!/bin/bash
# Run on the builder only after the reviewed full candidate is deployed.
set -eo pipefail
root=/srv/android/asus-device-product
revision=${1:?Supply a unique full-build revision, for example r1}
[[ "$revision" =~ ^r[0-9]+$ ]] || exit 2
record="$root/logs/full-build-$revision"
mkdir -p "$root/logs"
exec 9>"$root/logs/full-product-build.lock"
flock -n 9 || { echo 'Another full-product supervisor holds the lock'; exit 2; }
[[ -s "$root/logs/graphics-build-complete" ]]
[[ -s "$root/logs/full-product-deployed.json" ]]
[[ -s "$root/debug-adb-public-key" ]]
[[ ! -e "$record.started" ]] || { echo 'Preserve this previous build revision'; exit 2; }
for command in soong_ui soong_build ckati; do
    if pgrep -x "$command" >/dev/null; then
        echo "A source build is already running: $command"
        exit 2
    fi
done
date -u --iso-8601=seconds > "$record.started"
finish() {
    result=$?
    trap - EXIT
    printf '%s\n' "$result" > "$record.exit-code"
    date -u --iso-8601=seconds > "$record.finished"
    exit "$result"
}
trap finish EXIT
cd /srv/android/lineage24
key_link=device/asus/p00a/prebuilt/debug-adb-public-key
if [[ ! -L "$key_link" ]]; then
    [[ ! -e "$key_link" ]]
    ln -s "$root/debug-adb-public-key" "$key_link"
fi
[[ "$(readlink "$key_link")" == "$root/debug-adb-public-key" ]]
unset WITH_ADB_INSECURE
source build/envsetup.sh
lunch lineage_p00a-trunk_staging-userdebug
build/soong/soong_ui.bash --dumpvars-mode --vars='TARGET_BUILD_VARIANT TARGET_DEVICE TARGET_ARCH TARGET_KERNEL_SOURCE PLATFORM_SDK_VERSION PLATFORM_VERSION_LAST_STABLE PRODUCT_SHIPPING_API_LEVEL PRODUCT_OUT PRODUCT_BUILD_BOOT_IMAGE PRODUCT_BUILD_RAMDISK_IMAGE PRODUCT_BUILD_INIT_BOOT_IMAGE PRODUCT_BUILD_RECOVERY_IMAGE PRODUCT_BUILD_SYSTEM_IMAGE PRODUCT_BUILD_VENDOR_IMAGE PRODUCT_BUILD_PRODUCT_IMAGE PRODUCT_BUILD_SYSTEM_EXT_IMAGE PRODUCT_BUILD_USERDATA_IMAGE PRODUCT_BUILD_VBMETA_IMAGE BOARD_BOOTIMAGE_PARTITION_SIZE BOARD_SYSTEMIMAGE_PARTITION_SIZE TARGET_COPY_OUT_VENDOR TARGET_COPY_OUT_PRODUCT TARGET_COPY_OUT_SYSTEM_EXT PRODUCT_SYSTEM_PROPERTIES PRODUCT_SYSTEM_EXT_PROPERTIES PRODUCT_VENDOR_PROPERTIES PRODUCT_NOT_DEBUGGABLE_IN_USERDEBUG PRODUCT_ADB_KEYS PRODUCT_PACKAGES BOARD_VNDK_VERSION PRODUCT_PRODUCT_VNDK_VERSION SOONG_CONFIG_p00a_legacy_graphics SOONG_CONFIG_libion_legacy_impl BOARD_KERNEL_CMDLINE BOARD_MKBOOTIMG_ARGS' > "$record.vars"
python3 "$root/verify_full_images.py" vars "$record.vars"
# Discard old installed vendor/core copies after the product transition.
# The platform's installclean preserves compilation intermediates.
clean_marker="$root/logs/full-product-installclean.complete"
if [[ ! -e "$clean_marker" ]]; then
    m installclean
    printf "%s %s\n" "$revision" "$(date -u --iso-8601=seconds)" > "$clean_marker.tmp"
    mv "$clean_marker.tmp" "$clean_marker"
fi
m -j8 host_init_verifier android.hardware.health-service.asus-p00a services
for script in device/asus/p00a/rootdir/init.mt8163.rc device/asus/p00a/rootdir/init.mt8163.usb.rc device/asus/p00a/health/health.rc device/asus/p00a/connectivity/configs/init.p00a-connectivity.rc; do
    out/host/linux-x86/bin/host_init_verifier "$script"
done
m -j8 bootimage systemimage
python3 "$root/verify_full_images.py" images "$record.vars" "$record.images.json"
date -u --iso-8601=seconds > "$record.complete"
