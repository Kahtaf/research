R=/data/local/tmp/asus-alpine-ram
[ "$(stat -f -c %T "$R")" = tmpfs ]
chroot "$R" /usr/bin/env -i HOME=/root PATH=/usr/sbin:/usr/bin:/sbin:/bin /bin/sh -ec 'timeout 30 apk add --no-cache xauth xsetroot xset'
cp /data/local/tmp/asus-goodix-touchbridge "$R/usr/local/bin/z380m-touchbridge"
cp /data/local/tmp/asus-goodix-bin/asus-goodix-desktop /data/local/tmp/asus-goodix-bin/goodix-preflight.py "$R/usr/local/bin/"
cp -R /data/local/tmp/asus-goodix-etc/* "$R/etc/"
chmod 755 "$R/usr/local/bin/"*
mount -t sysfs sysfs "$R/sys"
mkdir -p "$R/dev/input"
for spec in graphics/fb0 misc/uinput; do
 numbers=$(cat "/sys/class/$spec/dev")
 name=${spec##*/}
 mknod "$R/dev/$name" c "${numbers%:*}" "${numbers#*:}"
done
for entry in /sys/class/input/event*; do
 [ "$(cat "$entry/device/name")" = goodix-touchscreen ] || continue
 numbers=$(cat "$entry/dev")
 mknod "$R/dev/input/${entry##*/}" c "${numbers%:*}" "${numbers#*:}"
done
chroot "$R" /usr/bin/python3 /usr/local/bin/goodix-preflight.py
chroot "$R" /usr/local/bin/z380m-touchbridge probe -i /dev/input/event11 -t 1
cat /proc/meminfo | head -4
getprop init.svc.surfaceflinger
getprop init.svc.zygote
getprop init.svc.zygote_secondary
