#!/bin/sh
# SPDX-License-Identifier: GPL-3.0-only
export PATH=/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin HOME=/root TERM=linux
umask 077
mkdir -p /run/asus-alpine /run/sshd /dev/input /dev/socket
# X sockets and browser scratch files must not survive an unclean SD-root boot.
mount -t tmpfs -o size=128m,mode=1777 asus-alpine-tmp /tmp || exit 1
ip link set lo up
exec >>/run/asus-alpine/sysinit.log 2>&1
echo "ALPINE_PID1=$(cat /proc/1/comm) release=$(cat /etc/alpine-release) kernel=$(uname -rm)"
# Find nodes from this exact kernel, with no assumed dynamic major numbers.
node_from_class() {
  for class in /sys/class/*; do
    d=$class/$1
    [ -r "$d/dev" ] || continue
    mm=$(cat "$d/dev")
    [ -e "/dev/$1" ] || mknod "/dev/$1" c "${mm%:*}" "${mm#*:}"
    [ -c "/dev/$1" ] || return 1
    return
  done
  return 1
}
if [ -f /etc/asus-alpine/enable-cold-wifi ]; then
# wmtdetect exists before wmt_loader initializes the remaining built-in stack.
if [ ! -e /dev/__properties__ ] && node_from_class wmtdetect && [ ! -e /run/asus-alpine/wmt-loader.started ]; then
  touch /run/asus-alpine/wmt-loader.started
  timeout -k 2 15 strace --kill-on-exit -f -X raw -e trace=ioctl -o /run/asus-alpine/wmt-loader.trace /vendor/bin/wmt_loader
  loader_rc=$?
  echo "WMT_LOADER_EXIT=$loader_rc"
  printf '%s\n' "$loader_rc" > /run/asus-alpine/wmt-loader.status
  # The loader's exit status reflects a missing property_set service, not init.
  # Its own ready=yes write is also unconditional after a failed module-init.
  # Accept only the exact successful ioctl AND registered kernel class.
  if python3 /etc/asus-alpine/validate-wmt-loader.py /run/asus-alpine/wmt-loader.trace; then
    for node in stpwmt wmtWifi; do node_from_class "$node" || { echo "MISSING_NODE=$node"; exit 1; }; done
    # libc maps the property area only at startup, so publish it before launcher.
    python3 /etc/asus-alpine/wmt-property-area.py --ready yes --output /dev/__properties__ || exit 1
    chown 1000:1000 /dev/stpwmt
    chmod 660 /dev/stpwmt
    # The stock launcher runs as Android system uid/gid1000, without Android init.
    grep -q '^asus-wmt:' /etc/passwd || echo 'asus-wmt:x:1000:1000:Stock WMT:/nonexistent:/bin/sh' >> /etc/passwd
    grep -q '^asus-wmt:' /etc/group || echo 'asus-wmt:x:1000:' >> /etc/group
    /bin/busybox su -s /bin/sh asus-wmt -c 'exec /vendor/bin/wmt_launcher -p /vendor/firmware/' >> /run/asus-alpine/wmt-launcher.log 2>&1 &
    echo $! > /run/asus-alpine/wmt-launcher.pid
    sleep 1
    timeout -k 2 15 sh -c 'printf 1 > /dev/wmtWifi'
    for attempt in 1 2 3 4 5; do [ -d /sys/class/net/wlan0 ] && break; sleep 1; done
    if [ -d /sys/class/net/wlan0 ]; then
      timeout -k 2 10 wpa_supplicant -B -Dnl80211 -iwlan0 -c/etc/asus-alpine/wpa_supplicant.conf -P/run/asus-alpine/wpa.pid >> /run/asus-alpine/wpa.log 2>&1
      associated=0
      for attempt in 1 2 3 4 5 6 7 8 9 10 11 12 13 14 15; do
        if wpa_cli -iwlan0 status | grep -q '^wpa_state=COMPLETED'; then associated=1; break; fi
        sleep 1
      done
      if [ "$associated" = 1 ]; then
        timeout -k 2 20 udhcpc -n -t 3 -T 4 -p /run/asus-alpine/udhcpc.pid -i wlan0 -s /etc/asus-alpine/udhcpc
        echo "NATIVE_DHCP_EXIT=$?"
        ip -4 addr show wlan0
      else
        echo 'WPA_ASSOCIATION_NOT_COMPLETE; inspect RAM wpa.log'
      fi
    fi
  fi
else
  echo 'WMT_INIT_SKIPPED property area exists, missing wmtdetect, or attempted already'
fi
else
  echo 'COLD_WIFI_GATED_OFF: manual experiment enable marker absent'
fi
# State is optional; only the marked SD directory is allowed to become writable.
persistence=0
if [ -f /etc/asus-alpine/enable-persistence ]; then
  python3 /etc/asus-alpine/state.py prepare || { echo 'SD_STATE_PREPARATION_FAILED; serial rescue remains available'; exit 1; }
  persistence=1
fi
# Hydration above precedes key generation, preserving the known SSH identity.
if [ -s /root/.ssh/authorized_keys ]; then
  [ -s /etc/ssh/ssh_host_ed25519_key ] || timeout -k 2 15 ssh-keygen -q -t ed25519 -N '' -f /etc/ssh/ssh_host_ed25519_key
  if [ "$persistence" = 1 ]; then
    python3 /etc/asus-alpine/state.py save-host-key || { echo 'SD_HOST_KEY_SAVE_FAILED'; exit 1; }
  fi
  cat > /etc/asus-alpine/sshd_config <<'CONFIG'
Port 2222
ListenAddress 0.0.0.0
HostKey /etc/ssh/ssh_host_ed25519_key
PasswordAuthentication no
KbdInteractiveAuthentication no
PermitRootLogin prohibit-password
PidFile /run/asus-alpine/sshd.pid
PrintMotd no
Subsystem sftp internal-sftp
CONFIG
  /usr/sbin/sshd -e -f /etc/asus-alpine/sshd_config
  echo "SSHD_START_EXIT=$?"
fi
if [ "$persistence" = 1 ]; then
  python3 /etc/asus-alpine/state.py start-dashboard || echo 'SD_DASHBOARD_START_FAILED; inspect RAM log'
fi
if [ "$persistence" = 1 ] && [ -f /etc/asus-alpine/enable-gui ]; then
  /etc/asus-alpine/start-desktop || echo 'DESKTOP_START_FAILED; SSH and serial remain available'
fi
echo 'ALPINE_RAM_SYSINIT_FINISHED; USB serial shell is available' 
