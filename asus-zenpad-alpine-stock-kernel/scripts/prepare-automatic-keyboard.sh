set -eu
apk add --simulate onboard at-spi2-core dbus
python3 - <<'PY'
import os
s=os.statvfs('/');assert s.f_bavail*s.f_frsize>200*1024*1024
PY
apk add --no-cache onboard at-spi2-core dbus
python3 - <<'PY'
import gi
gi.require_version('Atspi','2.0')
from gi.repository import Atspi
print('ATSPI_TYPELIB_IMPORT_PASS')
PY
command -v onboard
command -v dbus-run-session
