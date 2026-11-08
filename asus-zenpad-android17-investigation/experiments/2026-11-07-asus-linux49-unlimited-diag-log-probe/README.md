# Controlled test of retained userspace log suppression

Question: were the apparent syscall stops caused by the Linux 4.9 /dev/kmsg ten-message burst limit?

Status: packaging a single logging-only candidate. Same kernel gzip/raw Image, entire reporter ramdisk/helper and hardware DT; only both boot argument strings gain `printk.devkmsg=on` (plus necessary container lengths/hash). No driver, timer, watchdog or thermal changes. No normal Android partition changes.

The helper UUID is deliberately reused to keep this controlled experiment byte-identical. It is not independent freshness evidence: require exact new full p10 readback, one acknowledged entry from a verified stock boot, a verified different returned stock boot, and a complete new console. Compare records after message ten and actual returns. See evidence/packaging-receipt.json and logging-premise.json.

Parent must verify default PLAN, then install once and trial under the current nearby Power authorization. Missing output remains unknown. No block opens or storage writes are performed by the helper.
