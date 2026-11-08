# Offline implementation handoff

The stock-kernel diagnostic report repair is compiled, checked against the actual
binary policy, reproduced byte-for-byte, and staged as a new immutable candidate.
The independent OS rescue transport is a tested offline prototype, **not yet a
working recovery image**. Its Linux socket/block adapter, UID2000 proxy and
new-domain policy integration remain implementation work. The supplied ARM64
rescue executable deliberately exits 78; do not install it as a rescue service.
Full-OS flashing is not ready on the strength of these host tests.

All changes are inside this spike. No ADB/device/root commands, VM/cloud actions,
builds on a VM, goal operations, uploads, or subagents were used. Local compilation,
local ordinary-file formatting, saved-binary inspection and bounded AOSP source
fetches were used. Existing diagnostic/transport scripts, approved manifests,
images and backups were not edited. Original boot/recovery pairs were rehashed.

## Updated task decisions

The latest parent record is `internal-data-migration-decision-20261106.json`:
internal storage, nothing on ASUS needs preserving, no microSD, clean p26 ext4
once backup/rescue/image review is complete. Full original userdata backup and
hardware-backed old-FDE decryption are **not prerequisites**. No format was done.
The earlier external-scratch plan was read but is superseded for this task.

Current-stock raw SYSTEM streaming is owned by
`../2026-11-06-asus-stock-system-stream-backup`. Its implementation report was
read; no duplicate current-stock backup tool or upload was added here. That
agent's 36 host tests are not a completed real backup. This spike's manifest
leaves original SYSTEM SHA256 unresolved until the parent's actual COMPLETE,
READY/manifest and independent durable readback evidence exist.

## What the parent trial proved

The v3 image `f8c950819af579946071465e969e8eff454b6f8422d5eb19b3adb9bcd382da90`
ran the changed recovery ramdisk under stock 3.18 despite Red State. Authenticated
ADB/report endpoint appeared as `0123456789ABCDEF`, product `p00a_diagnostic`,
model `P00A_RAM_diagnostic`; stock is `DEVICE_SERIAL_REDACTED`. Report failed open errno13.
User confirmed no physical action before the automatic return. Last-kmsg records
deadline start 2.465837 and recovery reboot/restarting at 131.254692. Stock SDK24
returned boot-complete/Enforcing; on-demand root worked. Full original p10 hash
was already restored by stock, so the parent correctly performed no second block
write. This is neither a 4.9 boot nor proof of normal BOOT acceptance.

The saved log's initial failed head-c capture was unrelated to the diagnostic;
the bounded dd capture supplied the usable last-kmsg evidence.

## Report failure and narrow repair

`source/audit_binaries.py` checks the exact stock init bytes, not just an AOSP
analogy. At 0x41d0bc init's service-child path loads 0x3f (octal 077), calls umask
through 0x4c1b58, then the wrapper reaches Linux AArch64 syscall166 at 0x4cc300.
Thus collector `open(...,0644)` produces root-owned **0600**. UID2000 cannot read
it even when TE allows read. This is a deterministic DAC defect sufficient to
explain errno13 without an AVC. Actual target stat/label were not captured, so
this is not a claim that every possible runtime failure was independently ruled out.

The second, independently observed defect is init's denied `relabelto shell_exec`
for `/system/bin/sh`. That path is a separate regular executable in the CPIO, not
a symlink to the root helper. `/sbin/ueventd` alone is `../init`; basename dispatch
in the saved init reference selects ueventd and does not repair another service's
umask. The policy evaluator shows adbd executing a rootfs file stays **adbd**,
whereas executing shell_exec transitions to **shell**. Checking only
`allow shell tmpfs:file read` missed both the DAC failure and the actual exec path.

New helper behavior:

- Collector creates an exclusive no-follow pending file at mode0600 in the 1MiB
  RAM tmpfs. It finishes the bounded report, explicitly fchmods **0444**, then
  atomically renames it to `/tmp/diagnostic.txt`. Publication failures return74.
- `-c report` requires UID2000 and actual `u:r:shell:s0`, prints that endpoint
  evidence, and returns74 on open/read/output failure; bounded truncation returns75.
  Unsupported commands remain64; wrong UID/domain returns77. No shell is supplied.
- Before launching the unchanged stock adbd, the existing enforcing/FunctionFS
  guard now also requires the endpoint's actual `security.selinux` label to be
  shell_exec. A failed restorecon prevents ADB launch instead of silently retaining
  adbd's domain. The independent 120-second normal-reboot service still runs.
- The exact policy delta is only init→shell_exec:file relabelto, shell→tmpfs dir
  read/search and file read, and adbd's fixed rootfs execute_no_trans for its guard.
  The old adbd→tmpfs grants were removed. No permissive domains, block-write grants,
  DAC override, root shell, or persistent mount were added.
- This candidate is intentionally **stock-kernel/legacy-USB only**. It removes
  unused configfs setup/grants from this stock control. The optional configfs UDC
  report read may still record an unavailable/denied item; it is not needed for
  report transport. A future 4.9 ramdisk needs separate reviewed configfs integration;
  this work does not claim to have fixed or booted the old 4.9 image.

`evidence/diagnostic-final.json` contains real libsepol evaluations including TE,
MLS constraints and RBAC, with granted constraint expressions, process transitions,
validatetrans checks, file relabel-from/to, shell_exec/rootfs filesystem association,
ancestor search, report creation/rename/setattr, and forbidden writes. No new types
or permissive bits were added to the diagnostic policy. `source/verify.py` also
reproduces 0644+umask077→0600 on the host filesystem and explicit0444 publication.
This does not execute Linux SELinux or switch the host to UID2000.

## Exact new diagnostic artifact

Use **artifacts/candidate-final**, never the intermediate candidate-v1/v2 names.

- `UNTESTED-stock-control.img`: 8,654,848 bytes;
  SHA256 `7d74dfcaf4b2793453906799d721bfd95a401c564f6698b1c646e18bee918ea5`.
- Zero padded to the complete 16,740,352-byte p10:
  SHA256 `6c6a3f534646ed30257c21c7d91be65ea1b8844ef6aa2d0bd3c11545f62db925`.
- Wrapped stock kernel/DTB unchanged:
  `b0e5d48bf2889b418dda0fc867f70e42e27a0aeb0a0a3d37539d9a7435430880`.
- Helper static ARM64 ELF:
  `912f0a1f6d9540bb6f13109243ed808d2e0a6f790674de64c07071e3c72e4129`.
- Derived policy:
  `9decae09c93b9083f7e9aeed61d44ec1eb6c467fcc443169c05a9058ac0d5a31`.

`manifest.json` records CPIO entries/modes/hashes, stock wrappers/header addresses,
public RSA hash and source/tool identities. Only the existing authorized **public**
ADB key was read; its identity comment was stripped. `artifacts/inputs/adbkey.pub`
is that public-only reproducibility input. No private key was read/copied.
Stock init/adbd binaries and contexts files remain byte-identical. No signature
validity is claimed. `transport.UNAPPROVED.json` is a new filled geometry/hash
contract for parent review; its approval attestations intentionally remain false.
The old approved transport manifests were preserved.

`artifacts/reproduction-final/reproduction.json` records a fresh compile/generate
with byte-identical helper, image, policy and unarmed rescue ELF. ASan/UBSan fake
syscall tests passed with denied report open/read, finite success, infinite-source
bounds, output/publish failures, wrong UID/domain, bad label, and deadline failures.
No emulator is installed in the inspected local PATH; no target or emulator ran.

## Observer correction

`source/observer.py` is a new copy/reimplementation; the old observer and its
missed-serial evidence stay unchanged. Default is PLAN_ONLY. A parent-supplied
fresh stock pin must contain stock serial/fingerprint/device, observed stock
product/model and physical `adb devices -l` USB topology. Missing USB topology,
wrong product/state, duplicates or multiple plausible devices are refused.
Diagnostic serial alone never selects a device. Commands address the exact
`transport_id` with `-t`, and the report must contain the stock hardware serial in
kernel cmdline as well as the new marker, UID/domain and END_DIAGNOSTIC.
The observer records stock return even when report retrieval failed. It never
claims recovery restored from Android boot completion. If this host ADB backend
cannot supply a stable USB topology, parent must implement an OS USB-location
adapter; do not replace the guard with “pick the only 012345 device.”

Example pin fields (values must be captured, not copied from a fabricated sample):
`stock_serial`, `stock_fingerprint`, `stock_device`, `stock_product`, `stock_model`,
`usb`. Use `--pin FILE --out NEWDIR` for plan, and only parent adds `--observe`.

## Separate OS rescue prototype and its limits

`source/rescue.py`, `rescue_gate.c`, and `protocol.py` implement the reviewable
controller, fixed native bounds gate and binary framing. No ADB/network/device
adapter is supplied. The supplied backend exists only in tests, with byte-backed
sparse simulated partitions at the **real production geometry**. BOOT fixture
uses the actual local original bytes; SYSTEM/p26 large tests use synthetic bytes.
These are logical full-size tests, not writes of gigabytes to the host/device.

The intended recovery service uses stock authenticated production adbd and a fixed
UID2000 proxy. A new root domain accepts only a Unix socket peer verified by Linux
SO_PEERCRED=2000 and SO_PEERSEC=shell; those values cannot come from request JSON.
No TCP listener, shell RPC, alternate executable or wire-supplied block path exists.
The separate init/policy/file-context templates in `source/staged-rescue` are
**not compiled or installed**. They deliberately avoid broad stock recovery domain
privileges. The ARM64 `rescue-UNARMED` executable is a compilation artifact with
exit78 only, not a daemon. Kernel socket credentials, actual proxy, syscalls,
mount/holder/node checks and policy labels must be implemented/integrated before
this design becomes an independent recovery channel.

The code already enforces/tests the functional contract:

1. PLAN_ONLY does no backend I/O. Execution uses a separately hash-pinned, strict,
   bounded manifest with explicit approved geometry/images, eMMC CID, GPT identity,
   dedicated recovery full hash, verified BOOT/SYSTEM/recovery backup receipts and
   parent runtime gates. Template is unapproved and lacks SYSTEM/candidate/CID hashes.
2. Only fixed operations exist: restore BOOT/SYSTEM, install SYSTEM then BOOT last,
   separately reviewed provision p26, and separately reviewed four-byte p20 footer
   magic invalidation. Readback is limited to BOOT/SYSTEM/recovery and reviewed
   userdata/metadata. There is **no recovery write** operation while rescue is active.
3. Each write rechecks identity, alias/opened node identity, exact geometry,
   unmounted/no-holders status and intact recovery. Linux adapter must bind these
   checks to the same O_NOFOLLOW block FD with fstat and BLKGETSIZE64; path checks
   alone are insufficient. GPT and eMMC identity reads are read-only.
4. Frames are at most1MiB, strictly sequential, exact-size and hashed against
   parent-reviewed chunk hashes **before** writing. No sparse skip/don't-care,
   arbitrary offset, ioctl/discard RPC or truncation is accepted. Complete raw
   image/padding is part of the reviewed hash. Manifest whole hashes and chunk
   maps must be produced from the same reviewed image.
5. Flush and complete partition SHA256 readback are required before success.
   Already-original restore does zero writes. Transport/read/write/flush/journal
   loss freezes the session; no retry, cleanup, reboot or automatic inverse follows.
   A mismatch is failure, never a successful restore. Parent must assess the old
   writer before deliberately starting a new inverse session.
6. Recovery readback streams carry offset, size and chunk digest. Stream completion
   explicitly does not claim durable destination verification. Backup-agent READY
   and independent reread evidence are the source for backup approval, not a boolean
   invented by this prototype. The backup agent's32MiB chunks can be re-read to make
   this transport's1MiB chunk map without another device backup or a full Mac copy.

Exact targets: p9 BOOT start127488/sectors32696/16,740,352 bytes; p25 SYSTEM
start1072424/sectors7331840/3,753,902,080 bytes; p10 recovery start160184/sectors32696.
All major179, minor=partition, sector512. No LK/preloader/security/GPT/BCB/para,
cache, persist, calibration or whole-disk writer is present. Future partial writes
cannot be made power-loss atomic; keeping independently bootable p10 is essential.

A dedicated OS rescue must **not inherit the diagnostic's 120-second reboot**.
SYSTEM transfer can exceed it; rebooting during/after an uncertain write destroys
recoverability. Keep it available under physical supervision and never reboot on
transport loss. The diagnostic remains separately bounded at120seconds.

## Clean internal data and stock rollback

p26 is fixed start8404264, sectors22131383, 11,331,268,096 bytes, 179:26. New Android17
uses plain internal ext4 without FBE/FDE in this temporary legacy shipping-API23
profile. This is not an encryption-equivalent final security claim. Both installed
fstabs must replace /data with `staged-rescue/fstab.internal-data.in`; no old FDE,
formattable, resize, checkpoint or metadata mount fallback. Keep the real late-mount
and firstboot service sequence. APEX backing is real ext4, not assumed tmpfs.

`source/data_plan.py` stages a fixed host-image recipe: block4096, inode256,
root0:0/mode0755, no reserved percentage, explicit legacy features only,
no discard, eager inode/journal initialization. p26 contains 2,766,422 filesystem
blocks plus3,584 trailing zero bytes. The complete raw partition image must be
reviewed/chunk-hashed and provisioned through the fixed p26 operation; no arbitrary
target formatter is exposed. It must be created on reviewed host storage with
adequate space, not assumed to fit this Mac's roughly1.3–1.5GiB free.

A **real local mke2fs** formatted only a new64MiB ordinary-file fixture. Superblock
and root inode checks passed: compat0x2c, incompat0x42, ro_compat0x73, 4KiB blocks,
root0:0/0755. Unsupported modern encrypt/verity/64bit/metadata_csum_seed/orphan_file
features are absent. Full-size image creation, filesystem check/mount, Android init
labeling, O_DIRECT/APEX use and actual3.18/4.9 compatibility remain untested.
The source recipe is compatible by feature selection, not runtime proof.

Existing metadata is p20 start294184/sectors65536/32MiB. Parent evidence classifies
its footer at offset0: magic0xd0b5b1c4, version1.3, structure2352, default-password
type1, aes-cbc-essiv:sha256, KDF5 SCRYPT_KEYMASTER,1338-byte keymaster blob. No key
was extracted/derived/uploaded here. “Default password” never implied software-only
decryption. Old data no longer needs preservation, so no legacy Trustonic/vold port
is required just to migrate to fresh data.

**OEM factory reset is not a bounded footer-only route.** The exact saved recovery
binary at0x407fd0–0x408028 opens an absolute key_loc and passes its whole size to the
wipe helper. Its size helper uses BLKGETSIZE64 (0x4166e0), and the wipe routine's
BLKDISCARD extent is [0,length] (0x41b2b4). Stock recovery fstab points key_loc at
p20. AOSP7 roots.cpp corroborates this code sequence. The normal recovery reset
also includes cache and recovery bookkeeping. Do not invoke OEM `--wipe_data` or
its UI as this tool's rollback procedure; it exceeds the staged scope.

The concrete **proposed** bounded stock-data reinitialization route is:

- While dedicated rescue remains intact, restore original full SYSTEM then BOOT;
  require the exact saved hashes, and provision a fresh compatible plain p26 image.
- Leave p20 untouched for the Android17 trial. For return to stock, only after
  separate parent review, require the reviewed full32MiB metadata preimage hash and
  magic, then zero **exactly bytes0..3** of p20. Full readback, with the old four magic
  bytes logically substituted for verification, must equal the complete original
  hash. No other metadata bytes may differ. Unknown/changed/already-invalid footer
  refuses; there is no automatic retry. The fake-boundary test verifies this behavior.
- Stock's forceencrypt path should treat the invalid old footer as absent and create
  new encryption state for the fresh filesystem using its own existing Keymaster.
  AOSP7 cryptfs.c rejects bad magic and initializes a new footer/key when starting
  encryption without a valid resumable header. This is a source-supported route,
  **not a verified OEM stock-vold runtime result**. The old default-password/KDF blob
  is not used as a migration dependency.
- Before relying on it, parent must verify the actual stock init/vold path and
  `ro.vold.wipe_on_crypt_fail` behavior. AOSP includes an encryption-failure branch
  that can request a BCB recovery wipe when that property is1. No such command is
  issued here, and no stock factory-reset/reinitialization success is claimed.
  Keep p10 usable until actual stock boot/ADB/new data state succeed. Do not replace
  a failed narrow plan with a blanket metadata or security wipe.

The footer operation is staged and disabled by default (`migration=false`,
`footer_review=false`). Consent to discard userdata is not silent approval to wipe
32MiB of metadata. Existing private metadata backups stay where they are. Only
BOOT/SYSTEM may use the parent's reviewed builder backup channel; no userdata or
calibration upload is added. A complete old userdata backup is no longer required.

## Parent actions and gates, in order

1. Review the new diagnostic source, policy results and exact candidate/hash contract.
   Make a new approved contract copy only after review; do not alter the old v3 one.
   Capture fresh exact-stock USB physical pin, stock health and current p10 geometry.
2. Parent performs the same single p10 control procedure and full padded readback.
   Physically select Recovery, observe the new endpoint on the pinned USB port,
   retrieve the UID2000/shell report, and confirm marker/end, enforcing and RAM-only
   mounts. Unauthorized-host rejection still needs a deliberate runtime check.
   Deadline return is separate from report success; never infer 4.9/BOOT acceptance.
3. After return, existing parent transport verifies/restores exact stock recovery;
   recognize automatic stock repair and avoid a redundant write. Verify original
   BOOT, stock health/Enforcing and cleanup. Keep all new and old evidence.
4. Parent completes and independently verifies the backup agent's full original
   SYSTEM stream plus the existing full BOOT/recovery backups. Integrate that exact
   SYSTEM hash/durable receipt, no fabricated value, into a new rescue contract.
5. Implement/integrate the currently missing Linux adapter, fixed UID2000 proxy,
   dedicated domain and reviewed full rescue image. Check actual constrained policy,
   labels, credentials, binary framing and physical re-entry under stock kernel.
   Demonstrate the fixed BOOT/SYSTEM inverse and full readback from recovery with
   normal Android unavailable to the command path, before replacing normal Android.
   An already-stock no-write check alone does not prove the writer works.
6. Keep that dedicated p10 intact throughout the full-OS trial. Returning to normal
   stock can automatically overwrite it; recheck/reinstall before the OS trial as
   necessary, rather than disabling stock repair. Audit experimental image init for
   any recovery-repair service. Verify p10 before and after all OS/data operations.
7. Complete separate4.9 bring-up, normal-BOOT acceptance review, full image fit and
   internal-data/stock-reinitialization review. Recovery runtime acceptance and the
   static ignored-return pattern in normal BOOT are different evidence. Parent
   authorizes exact candidate raw hashes and clean p26 image only when ready.
8. In authenticated dedicated recovery, with verified backups and no mounts/holders,
   install full SYSTEM, provision clean p26, then install BOOT last. Verify every
   full partition and preserved p10. Manually select Normal Boot; do not write BCB.
9. On failure, physical Recovery must still reach the independent channel. After
   resolving any uncertain writer, intentionally restore original SYSTEM/BOOT and
   perform the separately reviewed fresh-data/footer procedure above. Verify actual
   stock reinitialization/boot. Then parent can verify final stock recovery repair.

No full-OS trial should start with the supplied unarmed binary or with stock-root
restore as its only inverse. The useful completed output is a repaired, reproducible
control plus concrete tested recovery/data primitives and an explicit integration
boundary, not a claim of functional target recoverability already achieved.

## Actual verification and reproduction

- `evidence/offline-tests-final.txt`: **27 tests passed**, including actual local
  socketpair binary transport; full-size fake3,753,902,080-byte SYSTEM restore and
  11,331,268,096-byte p26 provision; node/geometry/alias/mount/identity/recovery-hash
  refusal; chunk corruption/order/size; backup/review guards; already-original
  zero-write inverse; partial write/EOF/flush/journal uncertainty with no retry;
  full readback mismatch; forbidden recovery/security operations; four-byte footer
  preservation; dual-serial observer ambiguity and failed report checks.
- `artifacts/tools-final/build.json`: actual ARM64 static diagnostic compilation,
  host libsepol compilation and ASan/UBSan C fake-syscall tests. The first development
  test exposed embedded NUL handling in the mock capture; it was fixed before the
  passing final build. Earlier outputs are preserved as superseded evidence.
- `evidence/diagnostic-final.json`: actual binary policy/constraint checks, image
  packaging, preserved stock binary inputs, DAC reproduction; no target execution.
- `evidence/binary-audit-v1.json`: exact init/OEM recovery instruction assertions.
- `evidence/ext4-fixture-final.json`: real64MiB host-file formatter output and feature
  inspection. No physical filesystem or full-sized data image was formatted.
- `artifacts/reproduction-final/reproduction.json`: independent byte-identical rebuild.
- `artifacts/rescue-v1/build.json`: host native gate and freestanding ARM64 **unarmed**
  binary compilation. New rescue-domain policy and Linux adapter were not compiled.

From this spike, offline only:

```sh
python3 -B source/reproduce.py --out artifacts/NEW-reproduction
python3 -B -m unittest discover -s tests -v
python3 -B source/rescue.py --manifest artifacts/rescue-v1/manifest.UNAPPROVED.json
python3 -B source/data_plan.py
../2026-11-05-asus-boot-access-audit/.venv/bin/python -B source/audit_binaries.py --out evidence/NEW-binary-audit.json
```

Do not use Python -O: assertions in the inherited boot-image verifier are deliberate.
Reproduction needs existing local clang, rust-lld path in the script and unchanged
local stock backups. No source fetch/VM/device operation is part of reproduction.
References fetched once are pinned with hashes in `source/reference/provenance.json`:
[AOSP7 roots.cpp](https://android.googlesource.com/platform/bootable/recovery/+/android-7.0.0_r1/roots.cpp),
[recovery.cpp](https://android.googlesource.com/platform/bootable/recovery/+/android-7.0.0_r1/recovery.cpp),
[cryptfs.c](https://android.googlesource.com/platform/system/vold/+/android-7.0.0_r1/cryptfs.c).
