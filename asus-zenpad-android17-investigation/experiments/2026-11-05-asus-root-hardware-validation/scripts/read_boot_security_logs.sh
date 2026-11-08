#!/system/bin/sh
# Read only: no security-driver ioctls or register writes.
id
printf '\nBOOT_LOG_SECURITY_LINES\n'
if [ -r /proc/last_kmsg ]; then
  grep -i -E 'SEC_POLICY|sec_boot|boot_chk_|lock state|seccfg|SEC_INIT|verified boot|seclib|HACC|SEJ' /proc/last_kmsg | head -160 || true
fi
printf '\nCURRENT_DMESG_SECURITY_LINES\n'
dmesg | grep -i -E 'seccfg|sec_boot|sec_init|hacc|sej|secro' | head -100 || true
printf '\nSECURITY_DRIVER_NODES\n'
cat /proc/devices | grep -i -E 'sec|hacc|sej' || true
ls -l /dev/sec /dev/sec* /sys/class/sec* /proc/sec* 2>/dev/null || true
printf '\nBOOTPROF\n'
head -80 /proc/bootprof 2>/dev/null || true
