set -eu
python3 /etc/asus-alpine/state.py save-host-key
python3 /etc/asus-alpine/state.py start-dashboard
curl -fsS --max-time 3 http://127.0.0.1:8080/health
printf '\n'
stat -c '%d:%i mode=%a owner=%u:%g' /var/lib/asus-dashboard /mnt/alpine-sd/2026-11-08-asus-alpine/service-data /mnt/alpine-sd/2026-11-08-asus-alpine/private/ssh_host_ed25519_key
cat /proc/mounts | grep -E '/mnt/alpine-sd|/var/lib/asus-dashboard'
sync
