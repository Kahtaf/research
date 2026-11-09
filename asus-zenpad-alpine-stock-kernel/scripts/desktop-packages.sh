R=/data/local/tmp/asus-alpine-ram
[ "$(stat -f -c %T "$R")" = tmpfs ]
chroot "$R" /usr/bin/env -i HOME=/root PATH=/usr/sbin:/usr/bin:/sbin:/bin /bin/sh -ec '
timeout 45 apk add --no-cache xorg-server xf86-video-fbdev xf86-input-evdev xkbcomp xkeyboard-config font-dejavu jwm xterm netsurf xdotool xinput xwd
apk info -v netsurf xorg-server
'
