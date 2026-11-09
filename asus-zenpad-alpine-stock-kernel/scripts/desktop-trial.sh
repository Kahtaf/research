R=/data/local/tmp/asus-alpine-ram
[ "$(stat -f -c %T "$R")" = tmpfs ]
[ "$(getprop init.svc.surfaceflinger)" = running ]
[ "$(getprop init.svc.zygote)" = running ]
secondary=$(getprop init.svc.zygote_secondary)
restore_display() {
 set +e
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
timeout 35 chroot "$R" /usr/bin/env -i HOME=/root PATH=/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin /usr/local/bin/asus-goodix-desktop 20
