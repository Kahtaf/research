set -eu
[ "$(cat /mnt/alpine-sd/2026-11-08-asus-alpine/ALPINE.ID)" = asus-alpine-stock-kernel-v1 ]
python3 - <<'PY'
import ctypes,os
p='/mnt/alpine-sd';before=os.stat(p).st_dev
libc=ctypes.CDLL(None,use_errno=True)
assert libc.mount(b'/dev/asus-alpine-sd',p.encode(),b'vfat',32,None)==0,ctypes.get_errno()
assert os.stat(p).st_dev==before and not os.statvfs(p).f_flag & os.ST_RDONLY
PY
[ ! -e /mnt/alpine-sd/2026-11-08-asus-alpine/PERSISTENCE.ENABLE ]
printf 'asus-alpine-state-v1\n' > /mnt/alpine-sd/2026-11-08-asus-alpine/PERSISTENCE.ENABLE
touch /etc/asus-alpine/enable-persistence
python3 /etc/asus-alpine/state.py prepare
python3 /etc/asus-alpine/state.py save-host-key
python3 /etc/asus-alpine/state.py start-dashboard
curl -fsS --max-time 3 http://127.0.0.1:8080/health
printf '\n'
stat -c '%d:%i mode=%a owner=%u:%g' /var/lib/asus-dashboard /mnt/alpine-sd/2026-11-08-asus-alpine/service-data /mnt/alpine-sd/2026-11-08-asus-alpine/private/ssh_host_ed25519_key
cat /proc/mounts | grep -E '/mnt/alpine-sd|/var/lib/asus-dashboard'
sync
