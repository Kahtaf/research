R=/data/local/tmp/asus-alpine-ram
[ "$(stat -f -c %T "$R")" = tmpfs ]
chroot "$R" /usr/bin/env -i HOME=/root PATH=/usr/sbin:/usr/bin:/sbin:/bin /bin/sh -ec '
timeout 45 apk add --no-cache openssh python3 curl iw wpa_supplicant strace
python3 -c "import ssl,sqlite3,platform; print(platform.machine()); print(ssl.OPENSSL_VERSION); print(sqlite3.sqlite_version)"
curl -fsS --max-time 10 https://alpinelinux.org/ -o /tmp/alpine-home.html
wc -c /tmp/alpine-home.html
uname -r
'
