#!/bin/bash
# Called only by the lock-owning Python supervisor; foreground and incremental.
set -eo pipefail
kit=${1:?Pinned kit path required}
[[ "$kit" == /srv/android/asus-reviewed-build-kit/r7 ]]
[[ "${REVIEWED_BUILD_LOCK_FD:-}" =~ ^[0-9]+$ ]]
# Prove this is the inherited lock, then verify it still holds the same inode.
python3 -B "$kit/scripts/check_launch.py" "$kit"
record=/srv/android/asus-device-product/logs/full-build-r7
cd /srv/android/lineage24
unset WITH_ADB_INSECURE SELINUX_IGNORE_NEVERALLOWS SOONG_ALLOW_MISSING_DEPENDENCIES ALLOW_MISSING_DEPENDENCIES
# Preserve actual compiler/linker command lines for the final provenance guard.
export NINJA_ARGS="-v"
source build/envsetup.sh
lunch lineage_p00a-trunk_staging-userdebug
build/soong/soong_ui.bash --dumpvars-mode --vars='TARGET_BUILD_VARIANT TARGET_DEVICE TARGET_ARCH TARGET_KERNEL_SOURCE PLATFORM_SDK_VERSION PLATFORM_VERSION_LAST_STABLE PRODUCT_SHIPPING_API_LEVEL PRODUCT_OUT PRODUCT_BUILD_BOOT_IMAGE PRODUCT_BUILD_RAMDISK_IMAGE PRODUCT_BUILD_INIT_BOOT_IMAGE PRODUCT_BUILD_RECOVERY_IMAGE PRODUCT_BUILD_SYSTEM_IMAGE PRODUCT_BUILD_VENDOR_IMAGE PRODUCT_BUILD_PRODUCT_IMAGE PRODUCT_BUILD_SYSTEM_EXT_IMAGE PRODUCT_BUILD_USERDATA_IMAGE PRODUCT_BUILD_VBMETA_IMAGE BOARD_BOOTIMAGE_PARTITION_SIZE BOARD_SYSTEMIMAGE_PARTITION_SIZE TARGET_COPY_OUT_VENDOR TARGET_COPY_OUT_PRODUCT TARGET_COPY_OUT_SYSTEM_EXT PRODUCT_SYSTEM_PROPERTIES PRODUCT_SYSTEM_EXT_PROPERTIES PRODUCT_VENDOR_PROPERTIES PRODUCT_NOT_DEBUGGABLE_IN_USERDEBUG PRODUCT_ADB_KEYS PRODUCT_PACKAGES BOARD_VNDK_VERSION PRODUCT_PRODUCT_VNDK_VERSION SOONG_CONFIG_p00a_legacy_graphics SOONG_CONFIG_libion_legacy_impl BOARD_KERNEL_CMDLINE BOARD_MKBOOTIMG_ARGS SELINUX_IGNORE_NEVERALLOWS BOARD_SEPOLICY_DIRS BOARD_VENDOR_SEPOLICY_DIRS BOARD_ODM_SEPOLICY_DIRS SYSTEM_EXT_PUBLIC_SEPOLICY_DIRS SYSTEM_EXT_PRIVATE_SEPOLICY_DIRS PRODUCT_PUBLIC_SEPOLICY_DIRS PRODUCT_PRIVATE_SEPOLICY_DIRS BOARD_SYSTEM_EXT_SEPOLICY_PREBUILT_DIRS BOARD_PRODUCT_SEPOLICY_PREBUILT_DIRS SEPOLICY_FREEZE_TEST_EXTRA_DIRS SEPOLICY_FREEZE_TEST_EXTRA_PREBUILT_DIRS DEVICE_MANIFEST_FILE DEVICE_FRAMEWORK_MANIFEST_FILE PRODUCT_MANIFEST_FILES SYSTEM_EXT_MANIFEST_FILES SYSTEM_EXT_HWSERVICE_FILES ODM_MANIFEST_FILES' > "$record.vars"
python3 -B "$kit/scripts/verify_full_images.py" vars "$record.vars"
python3 -B "$kit/scripts/verify_config_paths.py" "$record.vars" "$kit" "$kit/attempt/product-config-paths.json"
# Never repeat cleaning. The prior deployed product transition has its own receipt.
[[ -s /srv/android/asus-device-product/logs/full-product-installclean.complete ]]
m -j8 host_init_verifier simg2img e2fsck debugfs checkvintf apexd_host deapexer fsck.erofs secilc checkfc property_info_checker sepolicy_test sepolicy_neverallows android.hardware.health-service.asus-p00a services adb_root com.android.adbd p00a-wmt libbtcal libbt-vendor-p00a libbluetooth_mtk_p00a android.hardware.bluetooth@1.1-service.p00a wpa_supplicant wificond netbpfload netd bpfloader vold
for script in device/asus/p00a/rootdir/init.mt8163.rc device/asus/p00a/rootdir/init.mt8163.usb.rc device/asus/p00a/health/health.rc device/asus/p00a/connectivity/configs/init.p00a-connectivity.rc device/asus/p00a/radio/init.p00a-radio.rc device/asus/p00a/radio/bluetooth-p00a.rc system/connectivity/wificond/wificond.rc device/asus/p00a/sensors/init.p00a-accelerometer.rc hardware/interfaces/sensors/1.0/default/ACCOUNT_REDACTED; do
    out/host/linux-x86/bin/host_init_verifier "$script"
done
m -j8 bootimage systemimage
python3 -B "$kit/scripts/verify_full_images.py" images "$record.vars" "$record.images.json" "$kit/attempt/integration.json"
python3 -B "$kit/scripts/validate_completed_product.py" "$kit"
