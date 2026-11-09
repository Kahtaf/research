#!/bin/sh
# SPDX-License-Identifier: GPL-3.0-only
export PATH=/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin HOME=/root TERM=linux
stty 115200 raw -echo clocal -hupcl 2>/dev/null || true
printf '\r\nASUS Alpine RAM root; no internal installation\r\n'
cat /run/asus-alpine/bootstrap.log /run/asus-alpine/sysinit.log
printf '\r\nUse sh commands; stock SYSTEM and SD remain read-only.\r\n'
stty sane 2>/dev/null || true
exec /bin/sh -i
