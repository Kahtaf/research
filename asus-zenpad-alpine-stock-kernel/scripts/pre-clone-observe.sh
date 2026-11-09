set -eu
grep '^frame:' /run/asus-goodix/bridge.log | tail -12 || true
apk add --no-cache tzdata
cp /usr/share/zoneinfo/America/Toronto /etc/localtime
printf 'America/Toronto\n' > /etc/timezone
date
stat -c '%s' /mnt/alpine-sd/2026-11-08-asus-alpine/alpine-root.ext4.partial
