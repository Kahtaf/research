# Private first-boot DATA preparation

Question: can the experimental internal DATA image preserve this tablet's radio
calibration and this Mac's authenticated ADB access without uploading private
factory records to the builder?

Status: the actual local sparse DATA image is prepared. Both complete factory
radio containers and the Mac's public ADB key were read back byte-for-byte;
ownership, modes and SELinux labels match the intended paths. Read-only e2fsck
exited zero. No target writes or physical radio activation occurred. The original
VM image remains untouched. Actual physical operation is unproved.

`private/` is local, mode 0700 and ignored. It holds the working DATA filesystem,
selected preserved calibration, the Mac's public ADB key, and detailed receipts.
Never upload its contents to the builder or give them to a delegated worker.
No private ADB key is read or copied.

Actual image: `private/firstboot-data.raw`, 11,331,268,096 bytes, SHA256
`cf433efa509f09814bff0877368f0c1b811b7615eefd3cd2a02f58b57995131b`.
Its final 1 MiB chunk table is in `private/prepared-data-manifest.json`.
Authenticated ADB port 5555 and the product's Wi-Fi radio opt-in are prepared
using the exact legacy property files that SDK37 init imports. Bluetooth opt-in
is absent. Connecting to the user's network may still require the Android UI.

The first debugfs invocation rejected Python's `0o` octal syntax for inode modes.
Its output and intermediate image state were retained. The explicit mode-only
correction used debugfs's accepted leading-zero octal syntax, then all resulting
file bytes, inode metadata and labels were checked on the actual image. No new
filesystem features were enabled.

Continuation: use this modified DATA identity and chunk table in the final
five-role manifest, then copy its nonzero chunks directly to the installation
card. Do not use the pristine DATA hash for the modified image and do not upload
private DATA or calibration to the VM. Final SYSTEM/BOOT admission and physical
kernel/recovery operation remain separate prerequisites.
