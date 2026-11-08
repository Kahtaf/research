# SPDX-License-Identifier: Apache-2.0
ifneq ($(strip $(WITH_ADB_INSECURE)),)
$(error P00A bring-up requires authenticated ADB; unset WITH_ADB_INSECURE)
endif
# Release-map and Lineage check_product queries precede variant selection.
# Neither query can build; enforce eng rejection for actual configuration.
ifneq ($(CALLED_PRE_PRODUCT_CONFIG),true)
ifneq ($(CALLED_FROM_SETUP):$(DUMP_MANY_VARS),true:TARGET_DEVICE)
ifeq ($(TARGET_BUILD_VARIANT),eng)
$(error Use lineage_p00a-trunk_staging-userdebug; eng disables Lineage ADB authentication)
endif
endif
endif

$(call inherit-product, device/asus/p00a/device.mk)
$(call inherit-product, vendor/lineage/config/common_full_tablet_wifionly.mk)

# Keep userdebug diagnostics without Lineage's otherwise coupled insecure-ADB
# opt-in. ro.adb.secure remains 1; adbd drops privileges until authorized adb root.
PRODUCT_NOT_DEBUGGABLE_IN_USERDEBUG :=

PRODUCT_NAME := lineage_p00a
PRODUCT_DEVICE := p00a
PRODUCT_BRAND := asus
PRODUCT_MANUFACTURER := asus
PRODUCT_MODEL := ASUS ZenPad 8.0 Z380M
PRODUCT_RELEASE_NAME := P00A
TARGET_OTA_ASSERT_DEVICE := P00A_2
