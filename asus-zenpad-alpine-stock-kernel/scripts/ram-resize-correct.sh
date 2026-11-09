R=/data/local/tmp/asus-alpine-ram
[ "$(ls -A "$R" | wc -l)" = 0 ]
# Android mount stacked a second empty tmpfs instead of remounting; remove only that top mount.
umount "$R"
[ -x "$R/bin/busybox" ]
chroot "$R" /usr/bin/python3 - <<'PY'
import ctypes, os
before=os.stat('/').st_dev
libc=ctypes.CDLL(None,use_errno=True)
rc=libc.mount(b'asus-alpine-ram',b'/',b'tmpfs',32,b'size=536870912,mode=0700')
assert rc==0,(rc,ctypes.get_errno())
assert os.stat('/').st_dev==before
v=os.statvfs('/'); print('RAM_ROOT_BYTES',v.f_blocks*v.f_frsize)
assert v.f_blocks*v.f_frsize==536870912
PY
