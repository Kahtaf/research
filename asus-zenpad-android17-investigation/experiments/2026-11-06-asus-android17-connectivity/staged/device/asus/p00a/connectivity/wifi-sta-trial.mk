# Deferred integration: do not inherit for a kernel lacking WMT/STP/WLAN.
# Also include BoardConfig-connectivity.mk from BoardConfig.mk.
PRODUCT_PACKAGES += wpa_supplicant P00aWifiBringupOverlay
PRODUCT_VENDOR_PROPERTIES += wifi.interface=wlan0
PRODUCT_COPY_FILES += \
    device/asus/p00a/connectivity/configs/wpa_supplicant_overlay.conf:$(TARGET_COPY_OUT_VENDOR)/etc/wifi/wpa_supplicant_overlay.conf
# wpa_supplicant installs its AIDL v5 VINTF fragment and, with the BoardConfig
# switch above, its disabled/lazy-start service. Parent full product must already
# include the Wi-Fi framework/APEX + wificond + IP provisioning stack.
# Exclude IWifi vendor service/manifest entries; the fallback HAL returns NOT_SUPPORTED.
# No AP/P2P/NAN/RTT/offload feature XMLs are introduced.
