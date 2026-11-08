# Include from the future device product only after parent review.
P00A_ACCEL_PATH := $(call my-dir)
PRODUCT_PACKAGES += \
    sensors.mt8163 \
    android.hardware.sensors@1.0-service:64 \
    android.hardware.sensors@1.0-impl:64
PRODUCT_VENDOR_PROPERTIES += ro.hardware.sensors=mt8163
PRODUCT_COPY_FILES += \
    frameworks/native/data/etc/android.hardware.sensor.accelerometer.xml:$(TARGET_COPY_OUT_VENDOR)/etc/permissions/android.hardware.sensor.accelerometer.xml
