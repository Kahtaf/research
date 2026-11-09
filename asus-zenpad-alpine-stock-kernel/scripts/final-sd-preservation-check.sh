set -eu
chmod 755 /usr/local/bin/asus-alpine-boot-selection
/usr/local/bin/asus-alpine-boot-selection
sha256sum /mnt/alpine-sd/2026-11-08-asus-alpine/private/stock-recovery.img
export DISPLAY=:0 XAUTHORITY=/run/asus-goodix/Xauthority
xwd -root -silent -out /tmp/final-sd-desktop.xwd
sync
