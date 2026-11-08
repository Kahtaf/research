# Companion to radio.mk after strict 32-bit ELF and runtime gates pass.
# The HIDL bridge's source target is supplied by the connectivity spike.
PRODUCT_PACKAGES += android.hardware.bluetooth@1.1-service.p00a libbt-vendor-p00a libbluetooth_mtk_p00a libbtcal
PRODUCT_SYSTEM_PROPERTIES += ro.bt.bdaddr_path=/data/vendor/bluetooth/p00a/bdaddr
PRODUCT_COPY_FILES += device/asus/p00a/radio/bluetooth-p00a.rc:$(TARGET_COPY_OUT_VENDOR)/etc/init/bluetooth-p00a.rc
DEVICE_MANIFEST_FILE += device/asus/p00a/radio/manifest-bluetooth.xml
# No default BDADDR, old bluetooth.default.so, broad libnvram replacement,
# or generic service.nvram_init property is installed.
