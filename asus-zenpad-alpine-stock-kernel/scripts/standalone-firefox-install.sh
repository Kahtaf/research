set -eu
apk add --no-cache firefox-esr
firefox-esr --version
df -h /
mkdir -p /dev/shm /run/user/0
chmod 1777 /dev/shm
chmod 700 /run/user/0
mount -t tmpfs -o size=192m,mode=1777 tmpfs /dev/shm
