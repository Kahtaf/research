R=/data/local/tmp/asus-alpine-ram
[ "$(stat -f -c %T "$R")" = tmpfs ]
mkdir -p "$R/root/.ssh" "$R/run/sshd" "$R/dev/pts"
chmod 700 "$R/root/.ssh"
cp /data/local/tmp/asus-alpine-trial-key.pub "$R/root/.ssh/authorized_keys"
chmod 600 "$R/root/.ssh/authorized_keys"
# A new devpts instance belongs to the RAM environment, not Android's /dev.
mount -t devpts -o newinstance,ptmxmode=0666,mode=0620 devpts "$R/dev/pts"
ln -s pts/ptmx "$R/dev/ptmx"
chroot "$R" /usr/bin/ssh-keygen -A
cat > "$R/etc/ssh/sshd_config" <<'CONFIG'
Port 2222
ListenAddress 0.0.0.0
HostKey /etc/ssh/ssh_host_ed25519_key
PasswordAuthentication no
KbdInteractiveAuthentication no
PermitRootLogin prohibit-password
UsePAM no
PidFile /run/sshd.pid
PrintMotd no
Subsystem sftp internal-sftp
CONFIG
# The service expires automatically; no boot persistence is installed.
chroot "$R" /bin/sh -ec '/usr/bin/timeout 600 /usr/sbin/sshd -D -e </dev/null >/tmp/sshd.log 2>&1 & echo $! >/run/sshd-timeout.pid'
cat "$R/run/sshd-timeout.pid"
ip -4 addr show wlan0
ip rule show
