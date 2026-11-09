set -eu
grep -nE 'DBUS|bus_name|object_path|Visible|def Show|def Hide|def Toggle' /usr/lib/python*/site-packages/Onboard/OnboardGtk.py | tail -28
gsettings range org.onboard.window docking-edge
gsettings range org.onboard.auto-show reposition-method-docked
gsettings range org.onboard layout
df -h / /tmp
