set -eu
[ "$(getprop ro.serialno)" = DEVICE_SERIAL_REDACTED ]
[ "$(getprop ro.product.device)" = P00A_2 ]
[ "$(getprop ro.build.version.sdk)" = 24 ]
[ "$(getprop ro.build.fingerprint)" = asus/WW_P00A/P00A_2:7.0/NRD90M/WW_P00A-V5.3.20-20180809:user/release-keys ]
[ "$(getprop sys.boot_completed)" = 1 ]
[ "$(getenforce)" = Enforcing ]
[ -r /proc/driver/camera_info ]
printf 'ASUS_SENSOR_NAMES_BEGIN\n'
cat /proc/driver/camera_info
cat /proc/driver/camera_info
printf 'ASUS_SENSOR_NAMES_END\n'
