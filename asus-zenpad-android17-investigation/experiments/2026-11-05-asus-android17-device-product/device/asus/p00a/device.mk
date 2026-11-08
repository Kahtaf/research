# SPDX-License-Identifier: Apache-2.0
# Genuine userspace module bring-up; hardware HAL integration is still pending.
$(call inherit-product, $(SRC_TARGET_DIR)/product/core_64_bit.mk)
$(call inherit-product, $(SRC_TARGET_DIR)/product/core_minimal.mk)

# Stock ro.product.first_api_level is 23; vendor base currently runs SDK 24.
PRODUCT_SHIPPING_API_LEVEL := 23
PRODUCT_CHARACTERISTICS := tablet
PRODUCT_AAPT_CONFIG := normal tvdpi hdpi xhdpi
PRODUCT_AAPT_PREF_CONFIG := tvdpi
PRODUCT_LOCALES := en_US
PRODUCT_MAX_PAGE_SIZE_SUPPORTED := 4096
PRODUCT_PACKAGES += init com.android.adbd

$(call soong_config_set_bool,libion,legacy_impl,true)
$(call soong_config_set_bool,p00a,legacy_graphics,true)
$(call inherit-product, vendor/asus/p00a/p00a-graphics-vendor.mk)
PRODUCT_PACKAGES += libp00a_legacy_memory

# MTK wrappers, actual ramdisk/fstab, HALs and recovery have not been validated.
# This stage must not emit images that could be mistaken for a flashable ROM.
PRODUCT_BUILD_BOOT_IMAGE := false
PRODUCT_BUILD_RECOVERY_IMAGE := false
PRODUCT_BUILD_SYSTEM_IMAGE := false
PRODUCT_BUILD_VENDOR_IMAGE := false
PRODUCT_BUILD_PRODUCT_IMAGE := false
PRODUCT_BUILD_SYSTEM_EXT_IMAGE := false
PRODUCT_BUILD_USERDATA_IMAGE := false
PRODUCT_BUILD_VBMETA_IMAGE := false
