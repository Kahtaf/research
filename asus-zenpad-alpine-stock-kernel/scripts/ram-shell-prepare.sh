R=/data/local/tmp/asus-alpine-ram
[ ! -e "$R" ] || { echo 'RAM root already exists; inspect rather than overwrite'; exit 21; }
mkdir -m 700 "$R"
mount -t tmpfs -o size=384m,mode=0700 asus-alpine-ram "$R"
tar -xzf /data/local/tmp/asus-alpine-3.24.4.tar.gz -C "$R"
mkdir -p "$R/proc" "$R/dev" "$R/tmp" "$R/run"
mknod -m 666 "$R/dev/null" c 1 3
mknod -m 666 "$R/dev/zero" c 1 5
mknod -m 666 "$R/dev/random" c 1 8
mknod -m 666 "$R/dev/urandom" c 1 9
mount -t proc proc "$R/proc"
printf 'nameserver 1.1.1.1\nnameserver 9.9.9.9\n' > "$R/etc/resolv.conf"
printf 'https://dl-cdn.alpinelinux.org/alpine/v3.24/main\nhttps://dl-cdn.alpinelinux.org/alpine/v3.24/community\n' > "$R/etc/apk/repositories"
chroot "$R" /usr/bin/env -i HOME=/root PATH=/usr/sbin:/usr/bin:/sbin:/bin /bin/sh -ec '
echo EXPERIMENT_01_ALPINE_RAM
cat /etc/alpine-release
uname -rm
id
/sbin/apk --version
/bin/busybox ip addr show wlan0
/bin/busybox timeout 15 /bin/busybox wget -O /tmp/alpine-mirror.txt https://dl-cdn.alpinelinux.org/alpine/MIRRORS.txt
head -3 /tmp/alpine-mirror.txt
'
