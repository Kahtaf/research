# Minimal RAM USB probe host observer

Question: can macOS retain a fresh, media-level read-only 65,536-byte USB report
and validate the narrow stock kernel → minimal PID1 → tmpfs → legacy USB path?

Status: **offline implementation and synthetic tests only**. No actual ioreg,
diskutil, raw device, mount, unmount, sudo, device write, or physical trial was
performed while creating this spike. No physical success or Android return is
claimed. Tests mock the host and raw reader; their positive cases are fixtures.

Important outputs:

- `scripts/observe.py`: default `PLAN_ONLY`; opt-in live observer.
- `evidence/host-acceptance.json`: frozen source report contract copied from
  `../2026-11-06-asus-minimal-ram-usb-probe/evidence/host-acceptance.json`.
- `tests/test_observe.py` and `evidence/offline-tests.log`: synthetic acceptance,
  refusal, stale-baseline and changed-identity tests.
- `evidence/observer-before-volume.py` and its SHA256 pin: preserved observer
  before the explicitly requested mounted-report alternative.
- `PARENT-ACCEPTANCE-ADJUSTMENT.md`: parent's explicit trial acceptance change
  concerning automatic host mounts. The frozen upstream handoff is unchanged.

## Parent continuation

This script grants no install or recovery-entry authorization. Parent must first
bind the exact installed candidate/readback to the already reviewed trial, retain
the supervised Power/Normal Boot fallback, and have the user beside Power.

From this folder, first inspect the safe default:

```sh
python3 scripts/observe.py
```

Only for the separately authorized live trial, the immediate-arm mode runs
**before manual recovery entry**. Choose a new evidence directory per attempt:

```sh
python3 scripts/observe.py --observe --seconds 55 --output evidence/trial-001
```

Wait for `ARMED: baseline serial absent`, then perform manual entry under the
parent's existing procedure. The 55-second host timer includes baseline and
starts before entry, so it cannot extend a 60-second fallback window measured
from entry. The script exits as soon as it has evidence, or inconclusively on a
failure/deadline. Parent continues supervising the separate normal-return/Power
fallback window; an early observer exit does not prove or replace Android return.
The device's PID1 timer cannot cover a pre-PID1 kernel hang.

When human poweroff/unplug/boot-menu preparation might take longer, use the
separate bounded baseline flow instead. First capture serial absence while stock
is still available, before the final manual entry:

```sh
python3 scripts/observe.py --baseline-only --output evidence/baseline-001
```

After the parent/user confirms Recovery entry, start observation immediately
using that exact receipt and a new output directory:

```sh
python3 scripts/observe.py --observe --seconds 55 \
  --baseline-receipt evidence/baseline-001/baseline-receipt.json \
  --output evidence/trial-001
```

The receipt is valid for at most 180 monotonic seconds, belongs to this user,
must be a single-link mode0600 regular file, pins the exact absent-serial snapshot
SHA256, and requires the same hostname/boot-epoch fingerprint. Consuming it
renames it once to `baseline-receipt.consumed.json`; failed validation also spends
the receipt. A device already enumerated when this later observer starts is
acceptable only with this fresh baseline receipt. No post-entry baseline is
invented. The host bound begins when `--observe` starts: parent must launch it
promptly after entry confirmation and maintain its independent fallback deadline
from actual entry. The script cannot recover an unobserved entry timestamp.

## Explicit read-only volume report alternative

The parent found that this non-admin caller cannot read raw disk nodes. Raw
mode still refuses permission denial and never falls back automatically. Parent
separately authorized this explicit alternative for the exact identified probe:

```sh
python3 scripts/observe.py --observe --report-via-volume --seconds 55 \
  --baseline-receipt evidence/baseline-001/baseline-receipt.json \
  --output evidence/trial-volume-001
```

This retains every fresh USB/interface/media read-only/size/identity requirement.
Only after those checks, if the exact identified disk has no mount point, it may
run `/usr/sbin/diskutil mount readOnly /dev/diskN` on that disk. An existing mount
is used only if the actual filesystem proves read-only. The exact disk is queried
again before access; it must report label `RAMPROBE` and a mountpoint beneath
`/Volumes` with no empty, dot or parent components. The reader opens every path
component with `O_DIRECTORY|O_NOFOLLOW`, requires a distinct mounted filesystem
and actual `fstatvfs` `ST_RDONLY`, then opens only literal `REPORT.TXT` relative to
that held root descriptor using `O_RDONLY|O_NOFOLLOW`. It requires a single-link
regular file of 1–1024 bytes on that root's device, unchanged descriptor metadata,
read-only filesystem flags before/after, and the exact seven report fields.
The reader is a child process bounded by the same deadline. Diskutil's exact
device/mountpoint/label and both registry IDs are checked again afterward.

Success is `POSITIVE_PID1_REPORT_VIA_READONLY_VOLUME`, with
`raw_FAT_verified=false`. It retains actual REPORT.TXT, descriptor/filesystem
facts and the mount command's actual result (or records that an existing mount
was used). It does not read raw sectors, hash the full medium, scan directory
contents, verify FAT allocation/no-extra-files, or claim a clean filesystem.
It remains sufficient for the parent's narrow actual minimal-PID1 report
discriminator. There is no sudo, unmount, repair, write test, arbitrary file
argument, arbitrary disk argument or system automount-policy change.

Live commands are limited to `/usr/sbin/ioreg -a -l -w 0 -p IOService`,
the receipt-only host boot query `/usr/sbin/sysctl -n kern.boottime`,
`/usr/sbin/diskutil info -plist /dev/diskN` for the freshly identified exact medium,
and a bounded child process opening its `/dev/rdiskN` with
`O_RDONLY|O_NOFOLLOW|O_CLOEXEC`. It reads exactly 65,536 bytes and requires a raw
character-device descriptor. Raw mode does not mount, unmount, repair, test a write,
change Disk Arbitration, or request sudo. Permission denial is inconclusive;
do not escalate automatically. The explicit volume alternative adds only the
exact read-only mount described above. Every child command shares the host deadline;
the raw child is killed on timeout. Local evidence writes/finalization can take
additional time and do not authorize delaying the physical fallback.

Acceptance requires:

1. No matching serial at the live baseline, followed by exactly one USB device
   with serial `b8bfa53e-4142-4ec8-b603-8f25cb617e2e` and a stable registry ID.
2. Exactly one interface, class/subclass/protocol `8/6/80` (mass storage, SCSI,
   bulk-only); exactly one whole IOMedia beneath it, exact 65,536-byte size and
   explicit `Writable=false`. Filesystem read-only flags cannot substitute for
   this media-level fact. Unrecognized/missing IOKit properties refuse access.
3. Matching whole-device diskutil identity and capacity, with no contradictory
   writable-media flag. The BSD node is selected only from that IOKit subtree;
   there is no arbitrary disk argument or scanning raw disks.
4. Identical USB and media registry IDs directly before/after the raw read,
   and matching diskutil evidence before/after.
5. In raw mode, the exact production FAT12 geometry, `RAMPROBE` label, sole read-only
   `REPORT.TXT`, matching FAT copies/allocation, zero unused data and root entries,
   and exactly the seven frozen field names and values without duplicates.
   The explicit volume alternative instead uses the narrower mounted-report
   acceptance and distinct result status described above.

`result.json` is positive only after those checks; it means only the minimal
PID1 discriminator. It cannot authenticate the public serial/run ID, establish
the installed image binding, prove Android 17/security, attest all historical
host mount attempts, or prove healthy Android returned. Parent must retain
install/readback evidence and actually observe healthy stock Android separately.

The script retains baseline/latest-poll/pre-read/post-read IOKit plists, two
diskutil plists, raw media, actual REPORT.TXT and the result. The latest poll
overwrites only this trial's previous latest poll, keeping disk use bounded.
IOService plists contain host inventory; evidence stays local in the trial folder.
Created output directories are mode0700 and all runtime evidence files are
mode0600, including full registry snapshots. Terminal output contains only the
probe result/identity and receipt location, never the full host inventory.

macOS registry layouts vary. This implementation deliberately has no fallback
guessing when class names/ancestry/media write protection cannot be established.
If that happens, preserve the inconclusive evidence for offline review. Do not
work around it by reading a guessed disk. A current failed snapshot may precede
complete USB enumeration; polling can continue within the same bound without
reading a disk until all identity/media checks pass.

Offline verification:

```sh
python3 -m unittest discover -s tests -v
```

No live `--observe` invocation was used during implementation.

## Parent Mac interface-descriptor correction

Actual host inventory repeats descriptor fields on mass-storage driver nubs. The collector now excludes only `IOUSBMassStorageInterfaceNub`/`IOUSBMassStorageDriverNub` from the interface count and requires the sole descriptor to belong to an actual `IOUSBHostInterface`/`IOUSBInterface`. Unknown and duplicate interfaces still refuse. All 28 methods pass for this profile. Current script SHA256 is `776f9f90c748187cbc3e55935a2c8c51a10ae5790500e39d7b22437c08ad16e5`; earlier pins and failed intermediate QA remain historical evidence. See `evidence/interface-fix-pins.json`. This was a host metadata preflight, not a probe boot.
