set -eu
export DISPLAY=:0 XAUTHORITY=/run/asus-goodix/Xauthority
cat /tmp/asus-osk-integration/state.json
cat /run/asus-goodix/desktop.log
tail -18 /run/asus-goodix/onboard.log
tail -10 /run/asus-goodix/browser.log
tail -8 /run/asus-goodix/jwm.log
xdotool search --onlyvisible --class firefox getwindowname
xwd -root -silent -out /tmp/asus-osk-integration/screen.xwd
