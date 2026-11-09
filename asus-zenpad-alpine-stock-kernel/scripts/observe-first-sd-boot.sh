echo SD_BOOT_AUDIT_BEGIN
cat /proc/sys/kernel/random/boot_id
cat /etc/asus-alpine-ram-release
uname -rm
cat /run/asus-alpine/root-mode
cat /run/asus-alpine/bootstrap.log /run/asus-alpine/sysinit.log
ip -o -4 addr show wlan0
cat /run/asus-goodix/desktop.log
cat /run/asus-goodix/browser-windows.txt
echo SD_BOOT_AUDIT_END
