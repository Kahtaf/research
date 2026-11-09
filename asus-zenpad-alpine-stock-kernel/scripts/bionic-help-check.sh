R=/data/local/tmp/asus-alpine-ram
C=$R/opt/android
[ ! -e "$C" ]
mkdir -p "$C/dev" "$C/tmp"
tar -xf /data/local/tmp/asus-alpine-stock-deps.tar -C "$C"
ln -s /system/vendor "$C/vendor"
set +e
timeout 3 chroot "$C" /system/vendor/bin/wmt_launcher -h
rc=$?
echo "BIONIC_HELP_EXIT=$rc"
