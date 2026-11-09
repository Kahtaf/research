# Optional microSD service state — prepared offline

Status: implemented and format-checked; no tablet or network operation by this task. Parent has independently proved the earlier RAM capsule's Alpine PID1, stock Wi-Fi and LAN SSH. This new persistence integration still needs the parent to run its real SD test and then verify another boot.

The exact opt-in file is `/2026-11-08-asus-alpine/PERSISTENCE.ENABLE`, containing `asus-alpine-state-v1` followed by newline. The normal `ALPINE.ID` marker is also mandatory. Missing persistence marker leaves the SD read-only and keeps the original temporary SSH behavior. An invalid marker fails into the existing serial rescue before handover.

## Implementation

- `recovery-init.sh` initially mounts the actual SD partition read-only with nosuid/nodev/noexec, root uid/gid, fmask0177 and dmask0077. This makes regular state files mode0600 and directories0700. It copies a validated opt-in marker and the helper into RAM. The post-mdev public-node chmod and loopback setup fixes are retained.
- `recovery-state.py prepare` requires that RAM gate, rechecks SD card type, actual mmcblk1p1 major/minor, the mounted vfat source, backing device and both exact markers. It accepts an already-correct writable mount; otherwise, before any service is using state, it unmounts and reopens the same `/dev/asus-alpine-sd` with the protected writable options. A failed rw mount attempts read-only restoration and stops. It never probes or mounts another partition.
- Only the new folder's `service-data` directory is bound onto `/var/lib/asus-dashboard`. Existing mismatched bind mounts or unexpected filesystem objects are rejected. No old rescue or installer folder is read or executed.
- Before key generation, an existing `private/ssh_host_ed25519_key` and `.pub` are validated as one unencrypted Ed25519 pair and copied into RAM with private-key mode0600. A partial or mismatched stored pair fails closed, rather than replacing the known identity. Stored keys never overwrite a differing RAM key.
- After generation, `save-host-key` exclusively creates absent SD key files, verifies SHA256 against RAM and syncs. Existing different files are refused, not overwritten. Private material is neither printed nor placed into the software archive/image.
- `start-dashboard` launches the existing RAM `/usr/local/bin/asus-dashboard.py`, with its fixed loopback127.0.0.1:8080 listener. stdin is `/dev/null`, logs and PID are RAM under `/run/asus-alpine`. A live existing PID is accepted only when its executable and exact Python/script argv match; the helper never kills an unknown process. No GUI starts here.

`recovery-sysinit.sh` runs the three phases in order: prepare before key generation; save key before sshd; dashboard after sshd. A requested state preparation/key failure stops that sysinit path and leaves the existing USB serial rescue available. Dashboard failure is logged without taking SSH away. The immutable root remains tmpfs, SYSTEM remains ro,noload, logs remain RAM. Only filesystem state in the marked dated SD folder becomes writable; there are no BCB/raw-partition writes or reboot paths.

For a current-boot parent test, install the helper into RAM at `/etc/asus-alpine/state.py`, create RAM `/etc/asus-alpine/enable-persistence` and the exact SD opt-in marker, then run `python3 /etc/asus-alpine/state.py prepare`, `save-host-key` (only after a valid RAM host key exists), and `start-dashboard`. The helper rejects preexisting service binds if the SD mount options are not already protected. The parent can supply a clean mount before this test; do not unmount a live service's state opportunistically.

## Validation and output

Python compilation, shell syntax and the capsule builder's image/MTK/newc/kernel checks passed. Helper `--help` runs without touching host mounts. No simulated filesystem suite or synthetic claim of persistence was added.

- Image SHA256: `f3e574cf499fc903883ba7f5850aa02fdb87642a56af9d32627b39ccf44a2748`.
- Full image16,740,352 bytes; used8,417,280 bytes.
- Wrapped kernel SHA256 remains `b0e5d48bf2889b418dda0fc867f70e42e27a0aeb0a0a3d37539d9a7435430880`, byte-identical to original BOOT and RECOVERY.
- Helper SHA256: `0a944c1e6f06b34783f687ec12e785ea2ab269e1b108ce571b63d4f4147b2b20`.
- Manifest: `artifacts/recovery-capsule/manifest.json`; build receipt: `evidence/recovery-state-build.json`.

Physical acceptance still requires protected mount options and actual device/inode checks, stable host-key identity, dashboard writes that survive a process restart, then the same key/database after a fresh boot. File preparation and a green image parser do not prove these outcomes.
