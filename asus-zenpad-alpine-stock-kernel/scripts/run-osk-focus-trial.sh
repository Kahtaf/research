set -eu
export DISPLAY=:0 XAUTHORITY=/run/asus-goodix/Xauthority
dbus-run-session -- python3 /run/asus-goodix/osk-focus-trial.py --directory /tmp/asus-osk-trial
