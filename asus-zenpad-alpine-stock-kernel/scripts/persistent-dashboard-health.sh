set -eu
cat /run/asus-alpine/dashboard.pid
cat /run/asus-alpine/dashboard.log
curl -fsS --retry 3 --retry-connrefused --retry-delay 1 --max-time 4 http://127.0.0.1:8080/health
printf '\n'
stat -c '%d:%i mode=%a owner=%u:%g' /var/lib/asus-dashboard /mnt/alpine-sd/2026-11-08-asus-alpine/service-data /mnt/alpine-sd/2026-11-08-asus-alpine/private/ssh_host_ed25519_key
cat /proc/mounts | grep -E '/mnt/alpine-sd|/var/lib/asus-dashboard|/system'
