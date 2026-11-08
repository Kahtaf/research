# SPDX-License-Identifier: Apache-2.0
$(call inherit-product, $(SRC_TARGET_DIR)/product/core_64_bit.mk)
$(call inherit-product, $(SRC_TARGET_DIR)/product/full_base.mk)
$(call inherit-product, frameworks/native/build/tablet-7in-xhdpi-2048-dalvik-heap.mk)

PRODUCT_SHIPPING_API_LEVEL := 23
$(call inherit-product, device/asus/p00a/firstboot/firstboot-services.mk)
PRODUCT_CHARACTERISTICS := tablet
PRODUCT_AAPT_CONFIG := normal tvdpi hdpi xhdpi
PRODUCT_AAPT_PREF_CONFIG := tvdpi
PRODUCT_LOCALES := en_US
PRODUCT_MAX_PAGE_SIZE_SUPPORTED := 4096
# Existing host's public ADB trust only, staged outside the source repository.
# Source-relative symlink resolves to the external public key; no key in source.
PRODUCT_ADB_KEYS := device/asus/p00a/prebuilt/debug-adb-public-key

$(call soong_config_set_bool,libion,legacy_impl,true)
$(call soong_config_set_bool,p00a,legacy_graphics,true)

PRODUCT_PACKAGES += \
    init \
    init_first_stage \
    com.android.adbd \
    fstab.mt8163_first_stage \
    android.hardware.health-service.asus-p00a \
    android.hardware.lights-service.asus-p00a \
    libp00a_legacy_memory \
    libutilscallstack \
    android.hardware.graphics.composer@2.1-service \
    android.hardware.graphics.allocator@2.0-service \
    android.hardware.graphics.allocator@2.0-impl \
    android.hardware.graphics.mapper@2.0-impl

PRODUCT_SYSTEM_PROPERTIES += \
    ro.bpf.allow_legacy_kernel=true \
    ro.adb.secure=1 \
    persist.sys.usb.config=adb \
    ro.config.low_ram=true \
    ro.config.per_app_memcg=false \
    ro.lmk.use_minfree_levels=false \
    ro.lmk.use_new_strategy=true \
    ro.sf.lcd_density=213 \
    ro.hwui.renderer=skiagl \
    debug.renderengine.backend=skiaglthreaded

PRODUCT_VENDOR_PROPERTIES += ro.hardware.egl=mali ro.hardware.gralloc=mt8163

PRODUCT_COPY_FILES += \
    device/asus/p00a/rootdir/fstab.mt8163:$(TARGET_COPY_OUT_VENDOR)/etc/fstab.mt8163 \
    device/asus/p00a/rootdir/init.mt8163.rc:$(TARGET_COPY_OUT_VENDOR)/etc/init/hw/init.mt8163.rc \
    device/asus/p00a/rootdir/init.mt8163.usb.rc:$(TARGET_COPY_OUT_VENDOR)/etc/init/hw/init.mt8163.usb.rc \
    device/asus/p00a/rootdir/ueventd.rc:$(TARGET_COPY_OUT_VENDOR)/etc/ueventd.rc

# Static live GPT: product/system_ext/vendor share the system filesystem.
PRODUCT_USE_DYNAMIC_PARTITIONS := false
PRODUCT_BUILD_BOOT_IMAGE := true
PRODUCT_BUILD_RAMDISK_IMAGE := true
PRODUCT_BUILD_INIT_BOOT_IMAGE := false
PRODUCT_BUILD_SYSTEM_IMAGE := true
PRODUCT_BUILD_RECOVERY_IMAGE := false
PRODUCT_BUILD_VENDOR_IMAGE := false
PRODUCT_BUILD_PRODUCT_IMAGE := false
PRODUCT_BUILD_SYSTEM_EXT_IMAGE := false
PRODUCT_BUILD_USERDATA_IMAGE := false
PRODUCT_BUILD_VBMETA_IMAGE := false

$(call inherit-product, vendor/asus/p00a/p00a-graphics-vendor.mk)
$(call inherit-product, device/asus/p00a/connectivity/connectivity-base.mk)
$(call inherit-product, vendor/gapps/asus-p00a-google.mk)

# Kernel 4.9 has PSI but no MEMCG. Android 17 lmkd uses PSI directly; there is
# no ro.lmk.use_psi switch in this source. Do not inherit a memcg-based Go profile.
# The 2 GiB tablet heap profile above caps normal app growth at 192 MiB.
# USB currently supports authenticated ADB only. Health is telemetry-only.
# Connectivity base is firmware/passive preflight only; radio activation is
# deferred until the missing kernel transport and vendor ABI are integrated.
# Camera/audio, remaining policy and actual Google build/runtime checks remain.

$(call inherit-product, device/asus/p00a/connectivity/wifi-sta-trial.mk)
$(call inherit-product, device/asus/p00a/radio/radio.mk)
$(call inherit-product, device/asus/p00a/radio/bluetooth.mk)

$(call inherit-product, device/asus/p00a/input/input-mapping.mk)

$(call inherit-product, device/asus/p00a/sensors/sensors.mk)

# Experimental retrofit contract; preserves the SDK37 framework matrices.
PRODUCT_PACKAGES += p00a_experimental_legacy_fcm3.xml
