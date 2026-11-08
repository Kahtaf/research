# Android 17 userspace startup on Linux 4.9

Question: Can the actual compiled SDK 37 libc/linker and command-line userspace
start and fork on the port's generic 4.9 kernel before trying the ASUS hardware?

Status: Passed. All three commands exited 0: actual Android 17 toybox startup,
uname on 4.9, and libc random-state initialization plus fork. All 18 captured
files verify locally. The first fixture failed because its minimal kernel
omitted madvise; the corrected fixture enables only CONFIG_ADVISE_SYSCALLS,
which the physical ASUS candidate already enables. This is a startup
compatibility check, not an Android framework boot or hardware validation.

Inputs: The completed ASUS Android 17 core build with legacy libc compatibility,
and the previously built generic ARM64 4.9 FD kernel. No kernel source changes.

Outputs: Actual executable/library hashes, boot log and command exit statuses.
The emulator has no disks, networking or physical USB devices. Fixture entropy
comes from the host for this disposable guest's startup; no device secrets or
personal files are included. No flashing is available in these scripts.

Continuation: Fix actual startup failures, then return to the device-product
spike to finish full-system/HAL integration and ASUS boot-image packaging.
