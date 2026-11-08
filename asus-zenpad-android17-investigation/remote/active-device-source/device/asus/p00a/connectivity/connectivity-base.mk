# Safe to inherit after the current build: firmware + passive preflight only.
P00A_CONNECTIVITY_PATH := device/asus/p00a/connectivity
PRODUCT_PACKAGES += p00a-connectivity-check
PRODUCT_COPY_FILES += \
    $(P00A_CONNECTIVITY_PATH)/firmware/WIFI_RAM_CODE_8163:$(TARGET_COPY_OUT_VENDOR)/firmware/WIFI_RAM_CODE_8163 \
    $(P00A_CONNECTIVITY_PATH)/firmware/WMT_SOC.cfg:$(TARGET_COPY_OUT_VENDOR)/firmware/WMT_SOC.cfg \
    $(P00A_CONNECTIVITY_PATH)/firmware/ROMv2_lm_patch_1_0_hdr.bin:$(TARGET_COPY_OUT_VENDOR)/firmware/ROMv2_lm_patch_1_0_hdr.bin \
    $(P00A_CONNECTIVITY_PATH)/firmware/ROMv2_lm_patch_1_1_hdr.bin:$(TARGET_COPY_OUT_VENDOR)/firmware/ROMv2_lm_patch_1_1_hdr.bin \
    $(P00A_CONNECTIVITY_PATH)/configs/init.p00a-connectivity.rc:$(TARGET_COPY_OUT_VENDOR)/etc/init/init.p00a-connectivity.rc
# Merge configs/ueventd.connectivity.rc.fragment into the parent's EXISTING
# ueventd input. A .fragment file under /vendor/etc is not automatically read.
