#!/bin/sh
# SPDX-License-Identifier: GPL-3.0-only
set -eu
[ -x /usr/local/bin/asus-goodix-desktop ]
command -v firefox-esr >/dev/null
[ ! -S /tmp/.X11-unix/X0 ] || { echo 'Display already exists; inspect its controller'; exit 1; }
mkdir -p /run/asus-goodix
if [ -s /run/asus-goodix/desktop.pid ]; then
    old=$(cat /run/asus-goodix/desktop.pid)
    [ ! -r "/proc/$old/cmdline" ] || { echo 'Previous desktop PID still exists; inspect it'; exit 1; }
    rm /run/asus-goodix/desktop.pid
fi
if [ -r /sys/class/leds/lcd-backlight/brightness ] && [ "$(cat /sys/class/leds/lcd-backlight/brightness)" -eq 0 ]; then
    # This stock LED store can apply brightness despite a short-write status.
    printf '100\n' > /sys/class/leds/lcd-backlight/brightness || true
    [ "$(cat /sys/class/leds/lcd-backlight/brightness)" -gt 0 ]
fi
setsid env ASUS_BROWSER=firefox-esr ASUS_DASHBOARD_URL=http://127.0.0.1:8080/ /usr/local/bin/asus-goodix-desktop 0 </dev/null > /run/asus-goodix/desktop.log 2>&1 &
for attempt in $(seq 1 30); do
 [ ! -s /run/asus-goodix/desktop.pid ] || break
 sleep .1
done
p=$(cat /run/asus-goodix/desktop.pid)
kill -0 "$p"
echo GUI_START_DISPATCHED
