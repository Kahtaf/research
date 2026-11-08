# Opt-in STA trial only, AFTER WMT + wlan0 exist. This is a BoardConfig include,
# not a product-makefile include. Requires a Linux Android17 build by parent.
BOARD_WLAN_DEVICE := wlan0
WPA_SUPPLICANT_VERSION := VER_0_8_X
BOARD_WPA_SUPPLICANT_DRIVER := NL80211
BOARD_WPA_SUPPLICANT_PRIVATE_LIB := lib_driver_cmd_p00a
WIFI_HIDL_UNIFIED_SUPPLICANT_SERVICE_RC_ENTRY := true
# Despite the historical HIDL variable name this selects the current AIDL rc.
# Do not request libwifi-hal-mediatek or lib_driver_cmd_mt66xx: neither exists
# in the audited platform. Do not declare android.hardware.wifi.IWifi.
