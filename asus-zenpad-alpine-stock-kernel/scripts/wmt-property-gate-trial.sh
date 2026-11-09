R=/data/local/tmp/asus-alpine-ram
C=$R/opt/android
[ "$(stat -f -c %T "$R")" = tmpfs ]
[ ! -e "$C/sys/devices" ]
for node in stpwmt wmtdetect wmtWifi; do [ ! -e "$C/dev/$node" ]; done
cleanup_probe() {
 set +e
 for entry in /proc/[0-9]*; do
  exe=$(readlink "$entry/exe" 2>/dev/null)
  [ "$exe" != "$C/system/vendor/bin/wmt_launcher" ] || kill -KILL "${entry##*/}"
 done
}
trap cleanup_probe EXIT
chroot "$R" /usr/bin/strace --help | grep -- --kill-on-exit
for value in no yes; do
 cp "/data/local/tmp/asus-wmt-ready-$value.bin" "$C/dev/__properties__"
 chown 0:0 "$C/dev/__properties__"
 chmod 444 "$C/dev/__properties__"
 set +e
 chroot "$R" /usr/bin/timeout -k 1 3 /usr/bin/strace --kill-on-exit -f -o "/tmp/wmt-property-$value.trace" /usr/sbin/chroot /opt/android /system/vendor/bin/wmt_launcher >"$R/tmp/wmt-property-$value.log" 2>&1
 rc=$?
 set -e
 echo "PROPERTY_PROBE_$value EXIT=$rc"
 cleanup_probe
 set -e
 cp "$R/tmp/wmt-property-$value.trace" "/data/local/tmp/asus-wmt-property-$value.trace"
 chown shell:shell "/data/local/tmp/asus-wmt-property-$value.trace"
 chmod 600 "/data/local/tmp/asus-wmt-property-$value.trace"
done
chroot "$R" /usr/bin/python3 - <<'PY'
from pathlib import Path
no=Path('/tmp/wmt-property-no.trace').read_text(); yes=Path('/tmp/wmt-property-yes.trace').read_text()
assert '"/dev/__properties__", O_RDONLY' in no and '"/dev/__properties__", O_RDONLY' in yes
assert '"/dev/stpwmt"' not in no
lines=[line for line in yes.splitlines() if 'openat(' in line and '"/dev/stpwmt"' in line]
assert lines and all('ENOENT' in line for line in lines),lines
print('PROPERTY_GATE_CONTROL_PASS no_stpwmt_open')
print('PROPERTY_GATE_POSITIVE_PASS missing_stpwmt_opens',len(lines))
PY
