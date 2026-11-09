#!/bin/sh
# SPDX-License-Identifier: MIT
# Build a separate JWM candidate; never installs packages or replaces /usr/bin/jwm.
set -eu

spike=$(CDPATH= cd -- "$(dirname -- "$0")/.." && pwd)
archive=$spike/evidence/jwm-reflow/jwm-2.4.6.tar.xz
patchfile=$spike/overlay/goodix/jwm-workarea.patch
expected=b5871ec28317594b3fa22b83ed5524cc911d498c455eaab3ae68def195dd802d

[ "$(uname -s)" = Linux ] && [ "$(uname -m)" = aarch64 ] || {
    echo 'This recipe targets native Alpine aarch64.' >&2
    exit 2
}
[ -r /etc/alpine-release ] || { echo 'Alpine release file missing' >&2; exit 2; }
case $(cat /etc/alpine-release) in
    3.24.*) ;;
    *) echo 'Review dependencies before building outside Alpine 3.24.' >&2; exit 2 ;;
esac

deps='build-base pkgconf patch xz gettext gettext-dev libjpeg-turbo-dev libpng-dev librsvg-dev libx11-dev libxext-dev libxft-dev libxinerama-dev libxmu-dev libxpm-dev libxrender-dev pango-dev'
for package in $deps; do
    if ! apk info -e "$package" >/dev/null 2>&1; then
        echo "Missing build prerequisites. Review: apk add --simulate --virtual .asus-jwm-build $deps" >&2
        echo "Then explicitly install if appropriate: apk add --virtual .asus-jwm-build $deps" >&2
        exit 2
    fi
done
command -v python3 >/dev/null
printf '%s  %s\n' "$expected" "$archive" | sha256sum -c -
build=$(mktemp -d /var/tmp/asus-jwm-build.XXXXXX)
echo "BUILD_DIRECTORY=$build"
tar -xJf "$archive" -C "$build"
cd "$build/jwm-2.4.6"
patch --batch --fuzz=0 -p1 < "$patchfile"

# Keep Alpine's optional features; stage the candidate without make install.
python3 - "$build" <<'PY'
import os
from pathlib import Path
import signal
import subprocess
import sys

build = Path(sys.argv[1])
command = '''native=$(cc -dumpmachine)
./configure --build="$native" --host="$native" \
 --prefix=/usr/local --sysconfdir=/etc --mandir=/usr/local/share/man \
 --localstatedir=/var --disable-rpath && exec make -j2'''
with (build / 'build.log').open('wb') as log:
    child = subprocess.Popen(['sh', '-ec', command], cwd=build / 'jwm-2.4.6',
                             stdout=log, stderr=subprocess.STDOUT,
                             start_new_session=True)
    try:
        result = child.wait(timeout=120)
    except BaseException as error:
        os.killpg(child.pid, signal.SIGTERM)
        try:
            child.wait(timeout=5)
        except subprocess.TimeoutExpired:
            os.killpg(child.pid, signal.SIGKILL)
            child.wait(timeout=5)
        if isinstance(error, subprocess.TimeoutExpired):
            print('Build exceeded 120 seconds; inspect ' + str(build / 'build.log'), file=sys.stderr)
            sys.exit(124)
        raise
if result:
    print('Build failed; inspect ' + str(build / 'build.log'), file=sys.stderr)
sys.exit(result)
PY

for feature in USE_ICONS USE_JPEG ENABLE_NLS USE_PANGO USE_PNG USE_SHAPE USE_RSVG USE_XBM USE_XFT USE_XINERAMA USE_XPM USE_XRENDER; do
    if ! grep -q "^#define $feature 1" config.h; then
        echo "Required feature $feature missing; inspect $build/build.log" >&2
        exit 1
    fi
done
install -m 755 src/jwm "$build/asus-jwm"
cp LICENSE "$build/LICENSE.jwm"
cp "$patchfile" "$build/jwm-workarea.patch"
sha256sum "$build/asus-jwm"
echo "CANDIDATE=$build/asus-jwm"
echo 'No installation performed. Preserve /usr/bin/jwm; review and test candidate first.'
