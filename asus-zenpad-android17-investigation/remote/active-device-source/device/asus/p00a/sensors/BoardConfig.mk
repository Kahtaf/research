# Include after existing DEVICE_MANIFEST_FILE assignments in future BoardConfig.
P00A_ACCEL_BOARD_PATH := device/asus/p00a/sensors
DEVICE_MANIFEST_FILE += $(P00A_ACCEL_BOARD_PATH)/manifest.xml
BOARD_VENDOR_SEPOLICY_DIRS += $(P00A_ACCEL_BOARD_PATH)/sepolicy
