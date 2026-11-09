set -eu
sleep 8
export DISPLAY=:0 XAUTHORITY=/run/asus-goodix/Xauthority
cat /run/asus-goodix/desktop.log
cat /run/asus-goodix/browser-windows.txt 2>/dev/null || true
tail -10 /run/asus-goodix/browser.log
xinput list
xwd -root -silent -out /tmp/standalone-desktop.xwd
printf 'REAL_TOUCH_EVENTS='; grep -c 'touch' /run/asus-goodix/bridge.log || true
cat /run/asus-alpine/sd-root-build.json
stat -c 'IMAGE_BYTES=%s ALLOCATED_512B_BLOCKS=%b' /mnt/alpine-sd/2026-11-08-asus-alpine/alpine-root.ext4.partial
