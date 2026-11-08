# ASUS recovery control transport

Question: can a narrowly scoped, auditable tool install the reviewed stock-kernel
recovery control and restore the exact original recovery partition?

Status: **offline implementation and fake-transport validation only**. No ADB,
root-helper execution, USB access, device operation, VM operation, or candidate
build was performed. This does not establish flash readiness, LK runtime
acceptance, or physical restoration. Parent owns candidate review and the
supervised hardware decision.

Important outputs:

- `source/recovery_control.py`: default PLAN ONLY, fixed install/restore interface.
- `source/manifest.schema.json` and `source/manifest.UNAPPROVED.template.json`:
  candidate contract; the template deliberately fails validation.
- `REVIEW-REPORT.md`: tested behavior, limits, and remaining parent review points.
- `evidence/offline-tests.{json,txt}`: actual offline results and simulated block
  write attempt sets. Test images are synthetic, nonbootable mutations, deleted
  with their temporary test directories; no diagnostic candidate was reviewed.
- `evidence/local-input-verification.json`: actual local stock/helper hashes.
- `evidence/runs/*/{state,plan}.json`: local-only verification/plan outputs.

All commands below run from this spike. Python 3.10+ standard library suffices.
No `adb` process is launched unless both `--execute` and `--supervised` are
provided, and the local input checks pass.

```sh
cd /OWNER_HOME/Documents/workspace/ideas/2026-11-06-asus-recovery-control-transport
PYTHONDONTWRITEBYTECODE=1 python3 source/recovery_control.py verify-local
PYTHONDONTWRITEBYTECODE=1 python3 tests/test_recovery_control.py
python3 source/recovery_control.py restore
python3 source/recovery_control.py install --manifest evidence/reviewed-control.json --reviewed-manifest-sha256 REVIEWED_64_HEX_SHA256
```

The last command requires a real parent-reviewed manifest; the placeholder is
not executable. Default plans validate only local inputs and describe future
operations. They do not query device presence or assert current partition state.

The future interface, **not executed here**, adds `--execute --supervised` to
install or restore. For example, after parent review and physical presence:

```sh
python3 source/recovery_control.py install --manifest evidence/reviewed-control.json --reviewed-manifest-sha256 REVIEWED_64_HEX_SHA256 --execute --supervised
python3 source/recovery_control.py restore --execute --supervised
```

Run restore after the parent/user manually returns to healthy stock Android,
regardless of the diagnostic result. Restore requires no candidate manifest.
The tool never reboots, selects Recovery/Normal Boot, or writes a BCB request.
A successful install readback only supplies evidence for the parent's decision.

## Fixed scope and inverse

Only `/dev/block/mmcblk0p10`, with by-name alias
`/dev/block/platform/mtk-msdc.0/11230000.MSDC0/by-name/recovery`, can be a block
write destination. The guards require partition 10, start sector 160184,
32696 sectors of 512 bytes, 16740352 total bytes, and major/minor 179:10. The
canonical node, alias and device-node number must agree. There is no CLI target,
serial, partition, offset, arbitrary command, or root-binary override.

Both fixed private backups are read without modification:

```text
../2026-11-05-asus-boot-access-audit/artifacts/device-backup/initial/recovery.bin
../2026-11-05-asus-boot-access-audit/artifacts/device-backup/verify/recovery.bin
SHA256 902b2f06a01cca574b4aa374e67c4e7f8f0ed53f6e6a55017b6d96351f0f1f20
```

The existing `../2026-11-05-asus-root-hardware-validation/scripts/root_shell.py`
is invoked unchanged for every privileged operation. This tool pins both its
source and its binary, retaining its exact serial/product/SDK/fingerprint,
UID-0 and Enforcing-restoration checks. It additionally requires boot completion,
serial properties, healthy Enforcing Android and the fixed recovery geometry.
The root helper's existing `/data/local/tmp/asus-mtk-su64` staging is preserved.

Our staging stays under `/data/local/tmp/asus-recovery-control-transport`:
root-owned 0711 parent/session directories, root-only 0700 vault, shell-owned
0700 inbox, fixed filenames. Staged vault inputs become root-owned 0400 and
are pulled back through the private inbox and byte-compared before use. Every
privileged operation rechecks the geometry and directory identity. Shell source
contains only fixed constants and an internally generated hex status token;
manifest paths, review text and image bytes never enter shell source.

Every write is a bounded `dd`, 512 × 32696 bytes, to the fixed node, followed by
`sync` and a full partition read/pull/hash. Android 7's saved toybox lacks
`sha256sum`; all hashes are calculated locally. No boot, system, security,
para/BCB, metadata or userdata **block** write is available. Temporary staging
uses the expressly authorized `/data/local/tmp` filesystem location.

A known failed install gets at most one stock inverse after fresh stock-Android
health checks. If stock already matches, it records verified-already-restored
without another block write. A failed inverse gets no automatic retry. Missing
status, timeout, failed ADB transport, or failed helper completion ends the run
without further transport calls, cleanup, reboot or a restoration claim.

Session directories use distinct fixed `install` and `restore` names. An existing
session is refused, never deleted/reused blindly. A stopped install leaves its
evidence intact while a separately invoked restore can use the restore session.
A stale restore session requires parent inspection before another attempt; this
tool provides no force-clean option. Normal verified completion removes only its
fixed temporary files/session. Failed runs may leave staging. The local advisory
lock prevents concurrent invocations on this host; the parent must exclude other
hosts/tools and external recovery mutations during a session.

## Manifest fields the parent must populate

Copy the unapproved template into this spike's `evidence/` and retain its exact
`schema_version`, `profile`, and `target`. The schema is machine-readable; the
Python validator additionally checks actual bytes and disallows duplicate keys.

- `candidate.path`: local relative path from the manifest to the reviewed bounded
  image (it may point into the diagnostic spike). No image is modified.
- `candidate.bytes`, `candidate.sha256`: exact bounded file length and SHA256.
- `candidate.header_page_sha256`: SHA256 of the first 2048 bytes.
- `candidate.wrapped_kernel_sha256`: retain
  `b0e5d48bf2889b418dda0fc867f70e42e27a0aeb0a0a3d37539d9a7435430880`.
  The tool independently compares every wrapped kernel/DTB byte to stock.
- `padding.kind`: `constant-byte`. `padding.byte`: explicitly reviewed integer
  0–255. `padding.full_partition_sha256`: SHA256 of the bounded image followed by
  that byte repeated to exactly 16740352 bytes. Zero in the template is not an
  approved padding decision.
- `review.reviewer`, `review.reference`: reviewer identity and durable reference
  to the actual source/image review. `review.marker`: exact unique runtime marker.
- `review.bounded_return_seconds`: reviewed diagnostic deadline, 1–600 seconds.
  This is review metadata; the transport tool does not implement or observe a
  reboot timer. Parent allows LK warning time and its separately chosen margin.
- Only after review, set `review.approved`,
  `review.ram_only_no_persistent_mounts_or_writes`, and
  `review.manual_recovery_and_normal_boot` to `true`.
- Independently hash the finalized manifest and pass that hash through
  `--reviewed-manifest-sha256`. Changing any field requires a new review/hash.

The accepted profile is deliberately narrow: legacy `ANDROID!`, 2048-byte pages,
stock kernel length/addresses/tags/second address/legacy fields, no second or DT
payload, exact stock MTK-wrapped kernel, well-sized `RECOVERY` wrapper, changed
ramdisk, and file ending at the aligned ramdisk boundary without a trailer.
Name/cmdline/header ID and ramdisk behavior remain covered by the parent's
review and whole-image/header hashes. This validator does **not** decompress or
certify init, validate the boot-header ID algorithm, or infer safe behavior from
an attestation. If the diagnostic output uses another layout or a full-partition
file, parent must reconcile that profile explicitly; do not weaken guards or
silently truncate the diagnostic artifact.

## State and continuation

Each invocation writes a private, new `evidence/runs/<UTC>-<random>/` directory.
`state.json` is updated before write dispatch and records outcomes, hashes,
restoration evidence and cleanup status. Execution also records each exact
argv, shell script, stdout/stderr and process status in `command-NNN.json`, plus
staged inputs/readbacks. No execution binaries/readbacks were generated here.
Preserve these private artifacts; a dispatched command without completion is
uncertain evidence, not proof it did or did not write.

Exit 0 means a valid offline plan/local check, or a successful requested execution
with verified cleanup. Exit 2 includes a failed install even when its inverse
succeeded, a guard refusal, unknown transport, failed restore, or cleanup failure.
`write_dispatches` is conservative intent before invoking the root operation;
it is not proof `dd` started. Fake test `writes` records actual simulated `dd`
attempts. Only a completed full hash check sets `restore_verified`.
`manual_recovery_permitted` can become true only in a future successful install
run with full readback and verified health/cleanup; it does not authorize the
parent to skip candidate/presence review.

Continue with the review points in `REVIEW-REPORT.md`, then prepare the manifest
from the diagnostic agent's completed control. Do not poll or modify its work.
No goal status, VM build, root helper, existing backup or other spike was changed.
