set -eu
deps='build-base pkgconf patch xz gettext gettext-dev libjpeg-turbo-dev libpng-dev librsvg-dev libx11-dev libxext-dev libxft-dev libxinerama-dev libxmu-dev libxpm-dev libxrender-dev pango-dev'
apk add --simulate --virtual .asus-jwm-build $deps
python3 - <<'PY'
import os
s=os.statvfs('/');assert s.f_bavail*s.f_frsize>750*1024*1024
PY
apk add --no-cache --virtual .asus-jwm-build $deps
df -h /
mkdir -p /var/tmp/asus-jwm-input/scripts /var/tmp/asus-jwm-input/evidence/jwm-reflow /var/tmp/asus-jwm-input/overlay/goodix
