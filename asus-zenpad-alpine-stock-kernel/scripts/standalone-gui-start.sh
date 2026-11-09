set -eu
chmod 755 /usr/local/bin/asus-goodix-* /usr/local/bin/goodix-*.py
[ ! -S /tmp/.X11-unix/X0 ]
mkdir -p /run/asus-goodix
if [ -r /sys/class/leds/lcd-backlight/brightness ]; then
 current=$(cat /sys/class/leds/lcd-backlight/brightness)
 if [ "$current" -eq 0 ]; then
  printf '100\n' > /sys/class/leds/lcd-backlight/brightness || true
  [ "$(cat /sys/class/leds/lcd-backlight/brightness)" -gt 0 ]
 fi
fi
ASUS_BROWSER=firefox-esr ASUS_DASHBOARD_URL=http://127.0.0.1:8080/ setsid /usr/local/bin/asus-goodix-desktop 0 </dev/null > /run/asus-goodix/desktop.log 2>&1 &
p=$!
printf '%s\n' "$p" > /run/asus-goodix/desktop.pid
sleep 3
kill -0 "$p"
echo STANDALONE_GUI_RUNNING
