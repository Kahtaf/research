R=/data/local/tmp/asus-alpine-ram
chroot "$R" /usr/bin/env -i HOME=/root PATH=/usr/sbin:/usr/bin:/sbin:/bin /bin/sh -ec '
timeout -k 2 40 apk add --no-cache openrc busybox-openrc busybox-mdev-openrc mdev-conf
printf "asus-alpine-stock-kernel-v1\nAlpine 3.24.4 aarch64; RAM experiment\n" > /etc/asus-alpine-release
sed -i "/^UsePAM /d" /etc/ssh/sshd_config
ls -l /sbin/init /etc/inittab
'
