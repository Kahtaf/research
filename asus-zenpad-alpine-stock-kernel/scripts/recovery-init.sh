#!/bin/busybox sh
# SPDX-License-Identifier: GPL-3.0-only
# Legacy gadget/no-devtmpfs startup adapted from kaantcp/z380m-alpine,
# Copyright (C) 2026 kaantcp; https://github.com/kaantcp/z380m-alpine
# This capsule has no raw partition writer, BCB handler or installer trigger.
export PATH=/bin:/sbin HOME=/root TERM=linux
B=/bin/busybox
$B --install -s /bin
mount -t proc proc /proc
mount -t sysfs sysfs /sys
mount -t tmpfs -o mode=0755 tmpfs /dev
mount -t tmpfs -o size=16m,mode=0755 tmpfs /run
mkdir -p /dev/pts /dev/input /mnt/sd /newroot /run/asus-alpine
mknod -m 600 /dev/console c 5 1
mknod -m 666 /dev/null c 1 3
mknod -m 666 /dev/zero c 1 5
mknod -m 666 /dev/random c 1 8
mknod -m 666 /dev/urandom c 1 9
mknod -m 666 /dev/tty c 5 0
mknod -m 666 /dev/ptmx c 5 2
mount -t devpts -o mode=0620,ptmxmode=0666 devpts /dev/pts
mdev -s 2>/run/asus-alpine/mdev.log
# mdev default permissions override the initial mknod modes; Bionic uid1000
# needs randomness, and ordinary userspace needs the standard public nodes.
chmod 666 /dev/null /dev/zero /dev/random /dev/urandom /dev/tty /dev/ptmx
DEVDIR=/dev
PROCDIR=/proc
LOG=/run/asus-alpine/bootstrap.log
TTY=
log() {
  echo "$("$B" cut -d. -f1 "$PROCDIR/uptime") $*" >> "$LOG"
  echo "$*" > "$DEVDIR/console" 2>/dev/null
}
sysnode() {
  [ -r "$1/dev" ] || return 1
  mm=$(cat "$1/dev") || return 1
  [ -e "$2" ] || mknod -m 600 "$2" "$3" "${mm%:*}" "${mm#*:}"
}
rescue() {
  log "RESCUE: $*; internal storage was not modified"
  if [ -n "$TTY" ]; then
    while true; do
      "$B" setsid "$B" sh -c '"$2" cat "$1"; exec "$2" sh -i' rescue "$LOG" "$B" <"$DEVDIR/$TTY" >"$DEVDIR/$TTY" 2>&1
      "$B" sleep 1
    done
  fi
  while true; do "$B" setsid "$B" sh -i <"$DEVDIR/console" >"$DEVDIR/console" 2>&1; "$B" sleep 1; done
}
log "ASUS Alpine RAM capsule, $(uname -rm); no partition writes"
G=/sys/class/android_usb/android0
if [ -d "$G/f_acm" ]; then
  echo 0 > "$G/enable"
  echo 0E8D > "$G/idVendor"
  echo 2007 > "$G/idProduct"
  echo MediaTek > "$G/iManufacturer"
  echo ASUS-Alpine-RAM > "$G/iProduct"
  echo asus-alpine-ram > "$G/iSerial"
  echo 1 > "$G/f_acm/instances"
  echo acm > "$G/functions"
  echo 02 > "$G/bDeviceClass"
  echo 1 > "$G/enable"
  for attempt in 1 2 3 4 5; do
    for node in /sys/class/tty/ttyGS*; do
      [ -r "$node/dev" ] || continue
      TTY=${node##*/}
      sysnode "$node" "/dev/$TTY" c && break
    done
    [ -z "$TTY" ] || break
    sleep 1
  done
fi
log "legacy ACM tty=${TTY:-unavailable}"
# The only accepted root source is the actual removable SD partition.
for attempt in 1 2 3 4 5 6 7 8 9 10; do
  [ -r /sys/class/block/mmcblk1p1/dev ] && break
  sleep 1
done
[ "$(cat /sys/class/block/mmcblk1/device/type 2>/dev/null)" = SD ] || rescue 'mmcblk1 is not an SD card'
sysnode /sys/class/block/mmcblk1p1 /dev/asus-alpine-sd b || rescue 'SD partition node unavailable'
mount -t vfat -o ro,nosuid,nodev,noexec,uid=0,gid=0,fmask=0177,dmask=0077 /dev/asus-alpine-sd /mnt/sd || rescue 'cannot mount SD read-only'
D=/mnt/sd/2026-11-08-asus-alpine
marker=
read marker < "$D/ALPINE.ID" || rescue 'SD marker unreadable'
[ "$marker" = asus-alpine-stock-kernel-v1 ] || rescue 'wrong SD marker'
if [ -e "$D/ROOT.EXT4.ENABLE" ] || [ -L "$D/ROOT.EXT4.ENABLE" ]; then
  [ -f "$D/ROOT.EXT4.ENABLE" ] && [ ! -L "$D/ROOT.EXT4.ENABLE" ] || rescue 'SD root enable marker is not a regular file'
  [ "$(cat "$D/ROOT.EXT4.ENABLE")" = asus-alpine-ext4-root-v1 ] || rescue 'invalid SD root enable marker'
  [ -f "$D/PERSISTENCE.ENABLE" ] && [ ! -L "$D/PERSISTENCE.ENABLE" ] || rescue 'SD root requires the persistence marker'
  [ "$(cat "$D/PERSISTENCE.ENABLE")" = asus-alpine-state-v1 ] || rescue 'SD root persistence marker differs'
  IMAGE=$D/alpine-root.ext4
  [ -f "$IMAGE" ] && [ ! -L "$IMAGE" ] || rescue 'SD root image is not a regular file'
  [ "$(stat -c %s "$IMAGE")" = 2147483648 ] || rescue 'SD root image is not exactly 2GiB'
  magic=$(dd if="$IMAGE" bs=1 skip=1080 count=2 2>/dev/null | od -An -tx1 | tr -d ' \n')
  [ "$magic" = 53ef ] || rescue 'SD root image ext4 superblock magic differs'
  # The card remains a protected data mount; only the loop filesystem executes.
  mount -t vfat -o remount,rw,nosuid,nodev,noexec,uid=0,gid=0,fmask=0177,dmask=0077 /dev/asus-alpine-sd /mnt/sd || rescue 'cannot reopen SD root storage writable'
  matches=0
  while read source target type options rest; do
    [ "$target" = /mnt/sd ] || continue
    matches=$((matches+1))
    [ "$source" = /dev/asus-alpine-sd ] && [ "$type" = vfat ] || rescue 'SD root mount source or type differs'
    for required in rw nosuid nodev noexec fmask=0177 dmask=0077; do
      case ",$options," in *",$required,"*) ;; *) rescue "SD root mount lacks $required";; esac
    done
  done < /proc/mounts
  [ "$matches" = 1 ] || rescue 'SD root mount count differs'
  [ "$(stat -c '%u:%g' /mnt/sd)" = 0:0 ] || rescue 'SD root storage owner differs'
  LOOPSYS=
  for candidate in /sys/class/block/loop[0-9]*; do
    [ -r "$candidate/dev" ] || continue
    if [ -e "$candidate/loop/backing_file" ]; then
      backing=$(cat "$candidate/loop/backing_file") || rescue 'cannot inspect loop backing file'
      [ -z "$backing" ] || continue
    fi
    LOOPSYS=$candidate
    break
  done
  [ -n "$LOOPSYS" ] || rescue 'no unused kernel loop device'
  [ ! -e /dev/asus-alpine-root-loop ] || rescue 'SD root loop node already exists'
  sysnode "$LOOPSYS" /dev/asus-alpine-root-loop b || rescue 'SD root loop node creation failed'
  [ -b /dev/asus-alpine-root-loop ] || rescue 'SD root loop node is not a block device'
  losetup /dev/asus-alpine-root-loop "$IMAGE" || rescue 'SD root loop attachment failed'
  if ! mount -t ext4 -o rw,noatime /dev/asus-alpine-root-loop /newroot; then
    losetup -d /dev/asus-alpine-root-loop
    rescue 'SD root ext4 mount failed; no RAM fallback'
  fi
  root_matches=0
  while read source target type options rest; do
    [ "$target" = /newroot ] || continue
    root_matches=$((root_matches+1))
    [ "$source" = /dev/asus-alpine-root-loop ] && [ "$type" = ext4 ] || rescue 'SD root mount source or type differs'
    for required in rw noatime; do
      case ",$options," in *",$required,"*) ;; *) rescue "SD root mount lacks $required";; esac
    done
  done < /proc/mounts
  [ "$root_matches" = 1 ] || rescue 'SD root mount count differs'
  echo SD-loop > /run/asus-alpine/root-mode
  printf '%s\n' "${LOOPSYS##*/}" > /run/asus-alpine/root-loop-device
  log "root mode SD-loop, ${LOOPSYS##*/}; writable image in the marked SD directory"
else
  ARCHIVE=$D/alpine-3.24.4-ram-rootfs.tar.gz
  expected=
  read expected rest < "$ARCHIVE.sha256" || rescue 'root archive checksum unreadable'
  case "$expected" in ''|*[!0-9a-f]*) rescue 'invalid root archive checksum';; esac
  [ "${#expected}" = 64 ] || rescue 'invalid root archive digest length'
  actual=$(sha256sum "$ARCHIVE")
  [ "${actual%% *}" = "$expected" ] || rescue 'root archive checksum mismatch'
  mount -t tmpfs -o size=768m,mode=0755 asus-alpine-root /newroot || rescue 'RAM root mount failed'
  tar -xzf "$ARCHIVE" -C /newroot || rescue 'root extraction failed'
  echo RAM > /run/asus-alpine/root-mode
  log 'root mode RAM; verified archive extracted to bounded tmpfs'
fi
marker=
read marker < /newroot/etc/asus-alpine-ram-release || rescue 'root marker unreadable'
[ "$marker" = asus-alpine-stock-kernel-v1 ] || rescue 'wrong root marker'
[ -x /newroot/bin/busybox ] && [ -x /newroot/sbin/init ] || rescue 'missing Alpine busybox/init'
mkdir -p /newroot/system /newroot/run /newroot/dev /newroot/proc /newroot/sys /newroot/mnt/alpine-sd /newroot/etc/asus-alpine /newroot/data/nvram/APCFG/APRDEB
# Exact stock SYSTEM geometry, not a write target or a donor root partition.
[ "$(cat /sys/class/block/mmcblk0p25/start 2>/dev/null)" = 1072424 ] || rescue 'SYSTEM start differs'
[ "$(cat /sys/class/block/mmcblk0p25/size 2>/dev/null)" = 7331840 ] || rescue 'SYSTEM size differs'
sysnode /sys/class/block/mmcblk0p25 /dev/asus-stock-system b || rescue 'SYSTEM node unavailable'
mount -t ext4 -o ro,noload /dev/asus-stock-system /newroot/system || rescue 'stock SYSTEM read-only mount failed'
[ -x /newroot/system/vendor/bin/wmt_loader ] && [ -x /newroot/system/vendor/bin/wmt_launcher ] || rescue 'stock WMT binaries absent'
# Runtime prerequisites are exposed only inside the selected Linux root.
[ -e /newroot/vendor ] || ln -s /system/vendor /newroot/vendor
mkdir -p /newroot/etc/firmware
for file in /newroot/system/etc/firmware/* /newroot/system/vendor/firmware/*; do
  [ -e "$file" ] || continue
  name=${file##*/}
  [ -e "/newroot/etc/firmware/$name" ] || ln -s "${file#/newroot}" "/newroot/etc/firmware/$name"
done
for name in WIFI WIFI_CUSTOM; do
  [ -f "$D/private/$name" ] || rescue "private calibration $name absent"
  cp "$D/private/$name" "/newroot/data/nvram/APCFG/APRDEB/$name" || rescue 'calibration copy failed'
  chmod 400 "/newroot/data/nvram/APCFG/APRDEB/$name"
done
[ -f "$D/private/wpa_supplicant.conf" ] || rescue 'private station profile absent'
cp "$D/private/wpa_supplicant.conf" /newroot/etc/asus-alpine/wpa_supplicant.conf
chmod 600 /newroot/etc/asus-alpine/wpa_supplicant.conf
if [ -f "$D/private/authorized_keys" ]; then
  mkdir -p /newroot/root/.ssh
  cp "$D/private/authorized_keys" /newroot/root/.ssh/authorized_keys
  chmod 700 /newroot/root/.ssh
  chmod 600 /newroot/root/.ssh/authorized_keys
fi
# A persistent image must not retain a previous boot's sidecar enable decisions.
rm -f /newroot/etc/asus-alpine/enable-cold-wifi /newroot/etc/asus-alpine/enable-persistence /newroot/etc/asus-alpine/enable-gui
if [ -f "$D/COLD-WIFI.ENABLE" ]; then
  read enable < "$D/COLD-WIFI.ENABLE"
  [ "$enable" = asus-alpine-stock-wmt-v1 ] || rescue 'invalid cold-WiFi enable marker'
  touch /newroot/etc/asus-alpine/enable-cold-wifi
fi
if [ -f "$D/PERSISTENCE.ENABLE" ]; then
  read enable < "$D/PERSISTENCE.ENABLE"
  [ "$enable" = asus-alpine-state-v1 ] || rescue 'invalid SD persistence enable marker'
  touch /newroot/etc/asus-alpine/enable-persistence
fi
if [ -f "$D/GUI.ENABLE" ]; then
  read enable < "$D/GUI.ENABLE"
  [ "$enable" = asus-alpine-desktop-v1 ] || rescue 'invalid desktop enable marker'
  [ -f /newroot/etc/asus-alpine/enable-persistence ] || rescue 'desktop requires persistent dashboard state'
  touch /newroot/etc/asus-alpine/enable-gui
fi
cp /capsule/start-desktop /newroot/etc/asus-alpine/start-desktop
chmod 755 /newroot/etc/asus-alpine/start-desktop
cp /capsule/state.py /newroot/etc/asus-alpine/state.py
cp /capsule/sysinit /newroot/etc/asus-alpine/sysinit
cp /capsule/serial-login /newroot/etc/asus-alpine/serial-login
cp /capsule/udhcpc /newroot/etc/asus-alpine/udhcpc
cp /capsule/wmt-property-area.py /newroot/etc/asus-alpine/wmt-property-area.py
cp /capsule/validate-wmt-loader.py /newroot/etc/asus-alpine/validate-wmt-loader.py
chmod 755 /newroot/etc/asus-alpine/sysinit /newroot/etc/asus-alpine/serial-login /newroot/etc/asus-alpine/udhcpc
printf '::sysinit:/etc/asus-alpine/sysinit\n' > /newroot/etc/inittab
if [ -n "$TTY" ]; then
  printf '%s::respawn:/etc/asus-alpine/serial-login\n' "$TTY" >> /newroot/etc/inittab
else
  printf '::respawn:/bin/sh\n' >> /newroot/etc/inittab
fi
printf '::shutdown:/bin/sync\n::shutdown:/bin/umount -a -r\n' >> /newroot/etc/inittab
# Runtime mounts/logs remain RAM; SD-loop mode writes only its owned image.
log 'root verified; moving mounts and switching to Alpine init'
for name in dev sys run; do
  "$B" mount --move "/$name" "/newroot/$name" || rescue "move $name failed"
  case "$name" in
    dev) DEVDIR=/newroot/dev;;
    run) LOG=/newroot/run/asus-alpine/bootstrap.log;;
  esac
done
"$B" mount --move /mnt/sd /newroot/mnt/alpine-sd || rescue 'move SD failed'
"$B" mount --move /proc /newroot/proc || rescue 'move proc failed'
PROCDIR=/newroot/proc
exec "$B" switch_root /newroot /sbin/init
# A returned switch_root must leave PID1 alive; avoid any reboot/recovery fallback.
while true; do "$B" sleep 60; done
