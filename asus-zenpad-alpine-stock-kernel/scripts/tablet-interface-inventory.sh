set -eu
printf 'DRM_DEVICES\n'
for node in /sys/class/drm/*; do [ ! -e "$node" ] || basename "$node"; done
printf 'IIO_DEVICES\n'
for node in /sys/bus/iio/devices/*; do [ ! -e "$node" ] || basename "$node"; done
printf 'ACCELEROMETER_INTERFACES\n'
for node in /sys/class/misc/m_acc_misc /sys/class/misc/gsensor; do
 [ ! -d "$node" ] || ls "$node"
done
if [ -r /sys/class/misc/m_acc_misc/accdevnum ]; then
 n=$(cat /sys/class/misc/m_acc_misc/accdevnum)
 case "$n" in ''|*[!0-9]*) ;; *) cat "/sys/class/input/event$n/device/name";; esac
fi
printf 'VISIBLE_X_WINDOWS\n'
export DISPLAY=:0 XAUTHORITY=/run/asus-goodix/Xauthority
xdotool search --onlyvisible --name . getwindowname
