# microSD frontend for the ASUS rescue writer

Question: can the existing protected RSC1 writer consume a separate removable
microSD bundle without USB data, while preserving its target guards and full
readback/acceptance exchange?

Status: implemented and statically compiled for AArch64; focused host fixtures
passed. Not integrated into a rescue container and not physically tested. No
Android17 images, card capacity, runtime policy, device timing or install
admission is claimed. The current stock-only two-role manifest cannot enter the
normal install path. The Linux 4.9 SD-report probe is separate and was not changed.

Important outputs:

- `artifacts/sd_frontend.aarch64`: actual static ELF64 AArch64 executable,
  775,680 bytes; SHA256
  `b8cad792e6f178292ec6e604217dbbc392acbe1d91b18f222f14dd4e2c9ab745`.
- `source/sd_frontend.c`: bounded local socket client, PLAN by default.
- `source/bundle.py`: streaming host chunk producer, PLAN by default.
- `source/rescue.c`, `source/sd_mount.h`, `daemon.patch`: narrow daemon delta.
- `INTEGRATION.md`: exact fixed paths, service definitions and policy additions.
- `PROTOCOL.md`: retained wire exchange and failure behavior.
- `evidence/build.json`, `evidence/artifact.json`: actual compile, fixtures,
  ELF program headers and source/artifact hashes.

`baseline/` preserves the supplied rescue/common sources and supplied protocol
notes. `source/{common.h,sha256.h,client.py,manifest.py,host.py}` are unchanged
copies of the starting implementation. The Python client/host are reference
sources, not frontend dependencies; the historical host has dependencies outside
this spike and is not an entry point here. All original spike files are untouched.

## Operation

Run `/sbin/rescue-sd` as init-launched UID2000, `u:r:shell:s0`, enforcing.
There are no user-supplied paths, block-device operations, ADB, USB, network,
mount, format, repair, partition, reboot or automatic retry operations in it.
Default PLAN reads the daemon status, fixed RAM manifest, fixed SD bundle and
reconstructed raw hashes. It sends no reconcile/write requests and writes no card
report. It prints the exact trigger required by this daemon run.

Normal install requires a parent-admitted five-role RAM manifest, selecting
roles **2, 4, 3** (SYSTEM, DATA, BOOT). This frontend does not determine Android
version or admit images. Explicit `--rollback-system` or `--rollback-boot` selects
only role 0 or 1; it never chains rollback roles automatically. Optional
`--inverse-from=N` is only valid with explicit rollback and the daemon's actual
uncertain image N. BOOT prerequisites remain enforced by the daemon. A normal
partial install that is uncertain at DATA/BOOT cannot restart from SYSTEM through
this frontend; stop for a separately deliberate reconciliation decision.

`--execute` additionally requires this exact ordinary card file, with final LF:

```
/mnt/rescue-sd/asus-rescue/execute.trigger
EXECUTE ASUSR002 <actual-manifest-sha256> <current-daemon-run-nonce> install:2,4,3
```

The two hex fields are actual status values, not supplied constants. Rollback
selection text is `rollback:0:inverse:-1` (or the chosen role/inverse). The binary
prints the exact required line. A daemon restart invalidates old triggers. Stage
the trigger deliberately during the **same running daemon session**, e.g. through
the parent's separately established Wi-Fi shell. A trigger prepared before a new
boot is intentionally insufficient. Do not alter the trigger after an uncertain
attempt to force a retry.

Before execute, `/rescue.recovery.sha256` must hold the parent's actual expected
full recovery partition hash in immutable root-owned RAM. The frontend obtains
all actual p10 readback chunks over RSC1 and checks that whole hash before image
reconciliation. It never takes a recovery pin or manifest authority from SD.

The card mount contract is fixed to `mmcblk1p1`, dev 179:33, partition 1 of
`mmcblk1`, dev 179:32. Sysfs must independently report removable=1, device type SD,
different canonical disk/device paths from mmcblk0, matching dev/class links and
in-bounds partition start/length. The only accepted mount is the whole vfat root
at `/mnt/rescue-sd`, rw,nodev,nosuid,noexec with source
`/dev/block/mmcblk1p1`. Symlink paths and alternate/internal storage sources fail.
If physical enumeration differs, this source revision refuses it; parent physical
identification must precede any specific code change. It discovers no alternatives.

All major179 mounts still fail except that one independently verified mount.
Duplicate SD/bind mounts, internal eMMC mounts, shadow mounts and other major179
partitions fail. Existing eMMC descriptor, label, geometry, CID/GPT, holders,
recovery, prerequisite, chunk readback and full readback guards are retained.

The fixed bundle contains `manifest.sha256` (64 lowercase hex plus LF), optional
`execute.trigger`, and only the selected `role-N` directories. Each directory
contains only six-digit names such as `000000.raw`, exact raw chunks <=1MiB.
Missing files synthesize zero bytes **only** if the expected manifest chunk hash
matches the actual all-zero hash at its exact length. Present files also require
exact length and digest. Complete reconstructed raw hashes are checked before
reconciliation; each chunk is rechecked when streamed, even for target skips.
The production DATA tail is **355840 bytes**, not rounded or trimmed.

The pre-created sibling `/mnt/rescue-sd/asus-rescue-report/` receives a new
exclusive `attempt.txt` only during execute. Its first durable entry is UNKNOWN,
bound to manifest/run/selection; subsequent entries record observed full readback
and final acknowledgments. The file is evidence, never authority to retry.
Existing attempt.txt stops another execute. Any source, transport, target,
acknowledgment or report publication failure stops the sequence immediately.
Already acknowledged roles are recorded; no later role follows a failed/unknown
one. Only successful live return reports COMPLETE. No historical file recreates
that live decision, and successful completion never reboots automatically.

## Host bundle production

Prepare a new ordinary host workspace with `admitted.manifest` and
`raw/role-2.raw`, `raw/role-4.raw`, `raw/role-3.raw` supplied by the parent.

```
python3 -B source/bundle.py /absolute/owned/bundle-workspace
python3 -B source/bundle.py /absolute/owned/bundle-workspace --execute
```

PLAN reads only the small manifest and reports selected roles, logical output,
required nonzero source payload and an explicitly conditional FAT allocation
estimate. It does not read/copy/hash real raw images. Execute creates a new
`card/` tree, streams and verifies every raw chunk and whole raw hash, omits only
verified zeros, then publishes manifest.sha256 last. Failed partial output is not
resumed. It creates no execution trigger or install admission. Explicit
`--rollback-role 0`/`1` builds one separate rollback bundle, not a mixed-role card.
No card/device is accessed by this tool. Stage the contents of `card/` later using
the parent's physical/card workflow, preserving this exact shape. Do not add the
host workspace or raw files inside the bundle.

An 8GB card is not promised to fit installation plus rollback. Both tools report
selected-bundle source bytes; filesystem metadata, actual cluster allocation,
trigger and report space are extra. No real SYSTEM/DATA images were read or
bundled in this implementation task.

## Verification and continuation

One isolated remote prefix was created through the existing fixed helper:
`/srv/android/asus-microsd-frontend-20261107-impl1`. Work was serial, one CPU,
512MiB address-space limit, bounded small compiles. No external platform tree,
probe tree, running build/cache/log/lock or kernel input was accessed. The build
script records exact commands. It is an exclusive one-shot script; do not rerun
it against the existing prefix. A new explicit owned suffix is needed for future
work, not a shared build directory.

Focused fixtures checked: five-role admission/order versus the stock pair;
exact DATA-tail omission, nonzero-missing/symlink/short failure; independently
identified SD versus mounted internal eMMC; chunk producer full/hash verification;
full target digest plus final acknowledgment; lost final ack stays UNKNOWN with
zero completed roles. The changed daemon translation unit also compiled with
warnings treated as errors. No exhaustive sweep, new review, child agent or
platform/kernel build was run. ARM64 execution on the actual Linux4.9 kernel was
not tested.

Continue with parent-owned image admissions and container integration in
`INTEGRATION.md`. Remaining gates are physical SD enumeration/mount identity,
same-namespace runtime behavior, actual SELinux/DAC service/socket access,
static-libc execution on the target kernel, storage/timing qualification, capacity
from the admitted bundle, durable card reports, and the daemon's existing full
identity/recovery/readback guards. No readiness flags should be toggled here.
