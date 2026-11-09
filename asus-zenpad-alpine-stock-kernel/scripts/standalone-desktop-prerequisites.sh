set -eu
apk search -x svkbd
apk add --no-cache svkbd e2fsprogs e2fsprogs-extra
mkdir -p /etc/asus-goodix
[ ! -L /tmp/firefox-smoke ]
rm -rf /tmp/firefox-smoke
command -v svkbd-mobile-intl || apk info -L svkbd | head -20
busybox --list | grep -x losetup
df -h /
