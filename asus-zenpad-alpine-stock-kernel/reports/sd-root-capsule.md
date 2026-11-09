# microSD ext4-loop root capsule

Status: physically booted and verified. Installed recovery image SHA256 is `097ea7b81f4c3e847d5aec34834b404b70db7db945031be9082946b922f08a6c`,16740352bytes. The kernel is byte-identical to original BOOT and recovery; wrapped-kernel SHA256 remains `b0e5d48bf2889b418dda0fc867f70e42e27a0aeb0a0a3d37539d9a7435430880`. See CHECKPOINT.md and evidence/sd-system-repeatboot-receipt.json for live results; the builder manifest describes an offline artifact, while deployment is recorded separately.

## Selection and storage contract

The capsule discovers actual mmcblk1p1 major/minor numbers, requires parent type SD and initially mounts it ro,nosuid,nodev,noexec,uid0,gid0,fmask0177,dmask0077. It accepts only the fixed dated folder `/2026-11-08-asus-alpine` with `ALPINE.ID=asus-alpine-stock-kernel-v1`.

Without `ROOT.EXT4.ENABLE`, it verifies the retained archive digest and extracts to bounded768MiB tmpfs. SD root requires regular nonsymlink markers `ROOT.EXT4.ENABLE=asus-alpine-ext4-root-v1` and `PERSISTENCE.ENABLE=asus-alpine-state-v1`. Its sole root file is regular, nonsymlink `alpine-root.ext4`, exactly2,147,483,648bytes, with ext4 magic53ef at byte1080. An enabled but invalid root enters USB rescue; it never silently falls back to the older archive.

The same outer SD mount reopens rw while retaining protected flags and masks. A free loop is selected from actual sysfs entries, attached only to this owned file and mounted ext4 rw,noatime. The capsule verifies mount source/options and the Linux root marker before moving runtime mounts and switching root. SYSTEM geometry is pinned and mounted ro,noload. No partition formatter or raw writer is included in startup.

The old-kernel ext4 feature allowlist is exactly:

`has_journal extent huge_file flex_bg uninit_bg dir_nlink extra_isize sparse_super large_file filetype resize_inode dir_index ext_attr`

Actual3.18 read/write mounting, complete OS/profile population, unmount, loop detach and e2fsck passed before enablement. Modern64bit, metadata_csum and orphan_file features were not enabled. No SD repartitioning occurred.

## Runtime integration and evidence

Runtime dev/proc/sys/run mounts move to the selected root; /tmp is a bounded128MiB tmpfs so stale X sockets do not survive an unclean boot. mdev public node permissions are corrected after scanning. The capsule copies its current startup helpers each boot and clears old enable decisions before reconstructing them from the SD sidecars.

Exact original calibration/profile/public authorized key are copied from protected sidecars; these copies are private within the persistent root. The state helper binds only its service-data directory, restores the stable host key and starts the loopback dashboard. `GUI.ENABLE=asus-alpine-desktop-v1` optionally starts the persistent Goodix/Xorg/JWM/Firefox desktop after state preparation. Wi-Fi initialization has its own explicit marker and verified stock WMT readiness contract.

The first SD boot and two later ordinary default Linux boots passed. Root-mode logs say SD-loop and actual loop backing is the fixed owned file. OS file/SQLite transaction, dashboard data and stable SSH identity survived the stock-Android round trip and subsequent Linux reboot. The owner's browser profile remained intact; closed history quick_check passed. Current free capacity is about1.2GiB. See OPERATING.md for access, stock selection and explicit archive fallback.

Keyboard placement/focus, multitouch gestures, automatic rotation and media remain separate usability work; successful SD boot does not qualify them.
