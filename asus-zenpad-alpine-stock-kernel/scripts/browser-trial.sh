R=/data/local/tmp/asus-alpine-ram
[ "$(stat -f -c %T "$R")" = tmpfs ]
[ "$(getprop init.svc.surfaceflinger)" = running ]
[ "$(getprop init.svc.zygote)" = running ]
secondary=$(getprop init.svc.zygote_secondary)
chroot "$R" /usr/bin/timeout 35 /usr/bin/python3 /usr/local/bin/asus-dashboard.py >"$R/tmp/dashboard-server.log" 2>&1 &
dashboard_pid=$!
restore_display() {
 set +e
 kill "$dashboard_pid" 2>/dev/null
 start surfaceflinger
 start zygote
 [ "$secondary" != running ] || start zygote_secondary
}
trap restore_display EXIT
trap 'exit 130' INT
trap 'exit 143' TERM
[ "$secondary" != running ] || stop zygote_secondary
stop zygote
stop surfaceflinger
sleep 1
timeout 35 chroot "$R" /usr/bin/env -i HOME=/root ASUS_DASHBOARD_URL=http://127.0.0.1:8080 PATH=/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin /usr/local/bin/asus-goodix-desktop 20
