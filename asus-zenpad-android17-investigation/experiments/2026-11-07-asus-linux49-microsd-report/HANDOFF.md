# microSD PID1 report — parent handoff

Built offline; no physical boot, SD enumeration, persistence or reboot has been verified. This is a separate candidate. Earlier images, frozen sources, transports, device sessions and the independent AOSP build were untouched. Parent alone decides deployment; this packet contains no deployment writer or transport changes.

Candidate: `artifacts/candidate.img`, 8,044,544 bytes, SHA-256:
`505707610e035ea3b1b7364e5ad75ce1cf2396eca9b64e378c3b90150df6853d`.

Zero-padded p10: 16,740,352 bytes, SHA-256:
`78005304291706fe2ad2affa185467c89464dc2f3216f97d572a29a1e058afa9`.
It remains at `/srv/android/asus-linux49-microsd-report-20261107/artifacts/candidate.p10.raw` on the existing builder.

The input BMC kernel remains SHA-256 `e9cde06e85e752aec0433ea37fa926c31b4f7a72cd55453762ec6870e5bb5bf1`. The compressed Image stream and decompressed Image are unchanged. Baseline header command line, wrappers and LK relocation approach are retained; component lengths, Android image ID and chosen initrd bounds reflect the new ramdisk. Its gzip payload is 321,705 bytes at `0x44000000..0x4404e8a9`, with the 512-byte wrapper stripped by the existing LK approach. Only the baseline three chosen properties change. Existing packaging assertions passed. No kernel, configuration or platform compilation occurred.

Parent card preparation:

1. Identify the user's spare removable card in the Mac/card reader. Use its existing VFAT/FAT32 first partition; do not format, partition, repair or change unrelated files for this probe. If the existing filesystem/layout is incompatible, stop and report that fact. This variant has no exFAT/ext4/superfloppy fallback.
2. At that partition's root, place the supplied `card-preparation/PROBE.ID`. It is exactly 37 ASCII bytes: `dbbb6afb-dd70-4c35-961e-9c977d7164a8` followed by one LF byte (`0a`), without BOM, CR, spaces or additional lines. Fresh run UUID: `dbbb6afb-dd70-4c35-961e-9c977d7164a8`. If `PROBE.ID` already exists, resolve the name conflict explicitly; do not overwrite unrelated content.
3. Confirm `PROBE.TXT` does not exist. The probe creates that one fresh 8.3 filename exclusively and never overwrites it. Resolve any existing file explicitly before trial; leave unrelated files alone. Safely eject/unmount the card, then insert it before the supervised trial. Do not hot-swap it while the probe runs.

The static PID1 captures its actual uname and requires PID 1. It mounts proc/sysfs and a private 64 KiB tmpfs `/dev` with nosuid/noexec but deliberately without nodev. There is no devtmpfs, broad device population or USB gadget setup. It polls for at most 40 discovery attempts / a 10-second monotonic window. Blocking kernel operations remain subject to the lifecycle limitations below.

Only `mmcblk1p1` is eligible. Its canonical sysfs path must be the direct child of canonical `mmcblk1`; that disk must be under `/sys/devices`, report `removable=1` and card type `SD`, and the partition number must be 1. Disk and partition must report MMC major 179, nonzero minors with partition minor = parent minor + 1. Independent `/sys/dev/block/major:minor` links must resolve to those same canonical objects. Checks repeat before the initial mount, before writable remount, and before report creation. The only block node created is that verified partition's device number. No mmcblk0 node, whole-disk node, internal alias, internal filesystem mount or userspace internal-eMMC content access is present. Actual slot enumeration/removable metadata remain unverified; a mismatch fails closed with no fallback.

The sole VFAT mount starts read-only, nosuid/nodev/noexec, with `errors=remount-ro`. Its root must report the bound device and FAT filesystem type. `PROBE.ID` is opened relative to that root with nofollow; it must be a single-link regular file of the exact length and exact bytes through EOF. A missing/wrong marker or a card-binding failure before remount never enables a writable mount or creates a report. A failed binding recheck after remount stops before report creation, but the remount may already have changed FAT metadata. After a match, the existing mount is remounted writable, preserving that same filesystem object and root descriptor. A fresh `PROBE.TXT` is created using O_EXCL and O_NOFOLLOW relative to that root. Its type/device/initial size are checked, writes handle short I/O with at most 64 attempts, final size is checked, then file fsync, close, directory fsync and ordinary clean unmount are attempted.

Mount/remount or I/O errors have no alternate device/filesystem/repair route. A refused writable remount produces no report. After writable remount, failure may leave filesystem metadata changes or an empty/partial/complete `PROBE.TXT`; nothing is deleted or retried under another name. Failed fsync/close/unmount, write protection, removal, a dirty card or a kernel hang can prevent reliable persistence. The report does not certify that later fsync, unmount or reboot succeeded. The unchanged kernel initializes hardware and runs its normal drivers and reboot path; there is no broad claim of no hardware/internal writes.

The complete report has exactly these ordered fields, each newline-terminated:

- `run_id=dbbb6afb-dd70-4c35-961e-9c977d7164a8`
- `pid1=1`
- `sysname=` actual uname sysname
- `release=` actual uname release
- `version=` actual uname version
- `machine=` actual uname machine
- `status=pid1_uname_observed`

For this pinned kernel, expected physical values are `Linux`, `4.9.337-asus-p00a-experimental-g717bb3c9e13c-dirty`, `#1 SMP PREEMPT Fri Nov 6 21:17:56 UTC 2026`, and `aarch64`. The program records what uname actually returns rather than inserting these expectations. It omits nodename, domainname, identifiers and timestamps. No sample production report was created by this build.

Lifecycle retains the baseline 60-second PID1 deadline including setup and a SIGALRM normal `RB_AUTOBOOT` attempt. Successful or failed report setup does not extend it. A returning watchdog reboot parks PID1 so interrupted writes cannot resume; a returning ordinary reboot leaves PID1 alive. Pre-PID1 failure, an uninterruptible syscall, kernel hang or failed reboot may require manual Power. The timer starts in PID1, not at recovery-menu entry. Parent retains its supervised 15–20-second Power/Normal Boot fallback and must verify healthy stock Android return; nominal Power timing under Linux 4.9 is unproven.

Physical acceptance: parent binds the new image and full-p10 digests into its own authorized deployment procedure, with its required preservation/readback. After the supervised trial and healthy stock return, retrieve the card safely and inspect it without repair. Accept boot proof only from a newly created, complete `PROBE.TXT` matching this fresh run and the actual expected uname values. Its presence on the retrieved card proves this kernel reached static PID1 and persisted that observed report in that trial. It does not prove full Android, hardware readiness, clean unmount or automatic reboot. Absence/partial data is inconclusive among boot failure, SD detection failure, marker/mount refusal and I/O failure; do not broaden access or activate firmware on that result.

Validation was deliberately limited to three focused host mock groups (wrong card/marker and bounded discovery; successful short-I/O report and exclusive refusal; zero-write/repeated EINTR bounds), one actual serial static ARM64 compile, and a simple actual image layout/static-ELF check. The mock uname is explicitly `FIXTURE-*`, never physical evidence. An initial mock bookkeeping error was corrected before the ARM64 compile; see `evidence/fixture-correction.txt`. No broad suites, reviews, source/provenance sweep, child agents, device/card access or other process inspection ran. `SOURCE.diff` gives the delta; `evidence/build-log.json` and `evidence/manifest.json` record the build. Continue with parent card preparation and a separately authorized physical trial, not another build/review cycle.
