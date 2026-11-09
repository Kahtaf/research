R=/data/local/tmp/asus-alpine-ram
C=$R/opt/android
mknod -m 666 "$C/dev/null" c 1 3
mknod -m 666 "$C/dev/zero" c 1 5
mknod -m 666 "$C/dev/random" c 1 8
mknod -m 666 "$C/dev/urandom" c 1 9
set +e
chroot "$R" /usr/bin/timeout 3 /usr/bin/strace -f -o /tmp/bionic-with-random.trace /usr/sbin/chroot /opt/android /system/vendor/bin/wmt_launcher -h
echo "BIONIC_RANDOM_EXIT=$?"
tail -30 "$R/tmp/bionic-with-random.trace"
cat "$R/tmp/sshd-bounded.log"
