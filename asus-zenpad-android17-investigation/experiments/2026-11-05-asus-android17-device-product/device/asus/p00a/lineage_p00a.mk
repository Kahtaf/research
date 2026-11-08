# SPDX-License-Identifier: Apache-2.0
$(call inherit-product, device/asus/p00a/device.mk)
$(call inherit-product, vendor/lineage/config/common_mini_tablet_wifionly.mk)

PRODUCT_NAME := lineage_p00a
PRODUCT_DEVICE := p00a
PRODUCT_BRAND := asus
PRODUCT_MANUFACTURER := asus
PRODUCT_MODEL := ASUS ZenPad 8.0 Z380M
PRODUCT_RELEASE_NAME := P00A
TARGET_OTA_ASSERT_DEVICE := P00A_2
