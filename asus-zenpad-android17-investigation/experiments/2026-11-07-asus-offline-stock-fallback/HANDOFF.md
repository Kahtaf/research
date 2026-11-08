# Built selectable offline stock fallback

The fallback is now present in the assembled common core. The same final recovery
can deliberately select normal installation or complete original SYSTEM/BOOT/p10
restoration from SD. No future replacement recovery, USB, Wi-Fi, interactive shell,
terminal five-role helper header or post-boot command channel is needed.

Normal remains SYSTEM2 -> DATA4 -> BOOT3, actual client exit0 -> sync -> normal
reboot, retaining custom p10. Stock selection is SYSTEM0 -> BOOT1 -> retire the
ordinary writer -> fixed original-p10 helper -> durable OEM_RESET_REQUIRED ->
flush/unmount SD -> power-off. A failed/unknown step never selects another mode,
reboots normally, retries or performs an inverse. Factory reset is not automated.

## Actual products

`artifacts/ARTIFACTS.json` contains exact lengths and SHA256 values for all seven
products. All four programs are linked static AArch64 ET_EXEC, not object files:

- `artifacts/os-rescue` — 776472 bytes.
- `artifacts/rescue-sd` — 775920 bytes, normal profile plus fixed stock profiles.
- `artifacts/rescue-sd-supervisor` — 778224 bytes, fixed root selector.
- `artifacts/p10-restore` — 775536 bytes, dedicated original-pair-only helper.
- `artifacts/sepolicy` — 391284 bytes, SHA256
  `e559a17ee13b141ceca868df7311bee2e095cf340afee2fedb549d314b5cad11`.
- `artifacts/file_contexts.bin` — 225637 bytes, actual compiled contexts.
- `artifacts/common-rootfs.cpio.gz` — 2125747 bytes, SHA256
  `2ed5f658e3e2e1361d4881b84a6130c64f088656312875c145f1747781441f29`.

The actual common rootfs includes preserved stock init/ueventd, these four
programs, compiled policy/contexts, minimal init/properties/ueventd configuration
and the real original-pair manifest. It has no adbd, FunctionFS, network service,
interactive shell or automatic client start. Genuine final five-role manifest,
arm ID and final current-container binding are absent until final assembly.
It is a built common core, not a flash-ready candidate.

All implementation is in `source/`; focused source deltas against the completed
core are in `evidence/{rescue.c,sd_frontend.c,supervisor.c}.patch`. The completed
core and all earlier spikes remain untouched.

## Parent final assembly: local only

Run this only after the genuine SYSTEM/BOOT admissions and parent five-role
manifest/arm exist. Run it locally; the private final DATA image/table/manifest
must not be staged to the VM. This agent did not read or copy them.

```sh
python3 -B 2026-11-07-asus-offline-stock-fallback/scripts/final_package.py \
  --manifest "$ASUSR002_MANIFEST" \
  --arm-file "$ASUS_SD_ARM_FILE" \
  --kernel "$ASUS_LINUX49_IMAGE_GZ_DTB" \
  --output-dir 2026-11-07-asus-offline-stock-fallback/artifacts/final
```

The output directory must not exist. The packager requires a genuine five-role
ASUSR002 authority, exact actual role geometry/chunk counts, real original-pair
prefix and non-placeholder digests; it does not create image admissions or arm
IDs and does not read/re-hash any SYSTEM/BOOT/DATA raw image. The original prefix
must match the actual 115288-byte original manifest, SHA256
`605cdec038dafe3dddabfe92b8bd6cd189734f740230dfc362d02a43421e4e47`.
It therefore fixes original SYSTEM to
`4597a7b5a9f30f9e851f1ae71b54a2db1845465e36a1a55b70ae26e171d5cd49`
and original BOOT to
`7bb68511b1ade34d24c3e932da7260e6753fa87270bd8249a7218755a5df3316`.
It also requires the parent's now-admitted final DATA whole identity
`cf433efa509f09814bff0877368f0c1b811b7615eefd3cd2a02f58b57995131b`,
11331268096 bytes, rather than the pristine DATA identity. Its chunk table comes
only from the parent's genuine manifest; no private DATA records were accessed.
SYSTEM/BOOT install admissions and the manifest/arm remain pending.

The kernel must be the unchanged physical Image.gz-dtb SHA256
`e9cde06e85e752aec0433ea37fa926c31b4f7a72cd55453762ec6870e5bb5bf1`,
config SHA256
`10b212cabd28aad012582e86c64695ccd450650b4e09ec8da30c21e094f377c2`.
The reviewed 92-byte LK header, MTK wrappers, initrd relocation and reservation
checks remain. The compressed/decompressed Image bytes stay unchanged; only
permitted chosen metadata is adjusted to the actual complete ramdisk size.
No kernel/platform build or kernel/out access occurred here.

Outputs: `candidate.img`, full-length `candidate.p10.raw`,
`operational-ramdisk.members`, actual `rescue.current.binding`, `assembly.json`,
`manifest.sha256`, `execute.trigger`, `system.trigger`, `boot.trigger`,
`asus-rescue.mode.install`, `asus-rescue.mode.stock`. These control files are
ready to stage under the fixed names below. No SD/card/deployment operation is
performed by this command. Final image assembly has not been executed here;
no fake five-role manifest, arm, current-image hash or candidate was generated.

## Exact card layout and deliberate selection

All paths below are under the fixed mounted FAT32 SD root; every source file
must be ordinary, with no symlinks or alternate paths. Existing 1MiB chunk naming,
manifest chunk hashes, exact tail lengths and verified implicit zero chunks are
unchanged. The 16GB card's actual capacity/durability remain physical checks.

```text
asus-rescue.mode                     ONE deliberately chosen mode line
asus-rescue/
    manifest.sha256                  actual full five-role RAM manifest SHA + LF
    execute.trigger                 normal trigger emitted by final assembly
    role-2/000000.raw ...            admitted install SYSTEM
    role-4/000000.raw ...            admitted final DATA; zero chunks may be omitted
    role-3/000000.raw ...            admitted install BOOT
asus-rescue-report/
    attempt.txt                     prior normal evidence, if any; never deleted
asus-stock/
    manifest.sha256                  same full five-role RAM manifest SHA + LF
    system.trigger                  fixed role0 trigger from final assembly
    boot.trigger                    fixed role1 trigger from final assembly
    recovery.bin                    exact public original recovery, 16740352 bytes
    role-0/000000.raw ...            genuine original SYSTEM chunks
    role-1/000000.raw ...            genuine original BOOT chunks
asus-stock-report/                  pre-create; initially no three attempt files
    system.attempt.txt              created only by role0 client
    boot.attempt.txt                created only by role1 client
    p10.attempt.txt                 created only after both client successes
```

Normal bundle shape stays roles 2/4/3 only. Stock bundle shape allows exactly
`manifest.sha256`, `system.trigger`, `boot.trigger`, `recovery.bin`, `role-0`,
`role-1`; both original chunk directories are required and checked for exact
chunk filename ranges. Normal backup files do not go in `asus-rescue/`.
Report trees are separate; normal/failed evidence is retained. The same complete
stock source tree can remain staged during normal installation without becoming
a normal-client source or authorizing rollback.

Parent supplies `recovery.bin` from the known public stock backup under
`../2026-11-05-asus-boot-access-audit/artifacts/device-backup/{initial,verify}/recovery.bin`,
using its already verified exact identity:
`902b2f06a01cca574b4aa374e67c4e7f8f0ed53f6e6a55017b6d96351f0f1f20`.
This agent did not read, copy or re-hash those full real backup images. Recovery
payload is never embedded in the initrd.

For normal installation, parent deliberately stages the contents of final output
`asus-rescue.mode.install` as the fixed card-root `asus-rescue.mode`. Its exact
line is:

```text
OFFLINE-SELECT ASUSR002 <actual-full-manifest-sha256> <actual-arm-id> INSTALL
```

For a later deliberate stock rollback, while staging the card before recovery
entry, parent instead places the contents of `asus-rescue.mode.stock` under that
same fixed name. Its exact line is:

```text
OFFLINE-SELECT ASUSR002 <actual-full-manifest-sha256> <actual-arm-id> STOCK-RESTORE
```

Each line ends with one LF, without literal angle brackets. The selector reads
this choice exactly once. Missing, malformed, wrong-arm, wrong-manifest, multiple
or ambiguous lines refuse; there is no default-to-install behavior. Normal
failure never switches it to STOCK-RESTORE. Staging the stock mode is a separate
explicit parent decision, never a service-exit reaction.

The emitted per-role stock triggers are, each exactly one LF-terminated line:

```text
OFFLINE-PREARMED ASUSR002 <actual-full-manifest-sha256> <actual-arm-id> rollback:0:inverse:-1
OFFLINE-PREARMED ASUSR002 <actual-full-manifest-sha256> <actual-arm-id> rollback:1:inverse:-1
```

They go in `asus-stock/system.trigger` and `asus-stock/boot.trigger`, respectively.
`execute.trigger` retains the existing normal `install:2,4,3` selection. These are
not card-supplied manifest authority: all source/target full/chunk hashes still
come from the immutable RAM manifest. The arm remains a build-pairing ID, not a
secret/signature. Final assembly emits the actual lines, avoiding manual editing.

Before deliberate stock mutation the selector checks that none of the three
stock attempts already exists and preflights the exact original-recovery source
hash. It does not delete, rotate or resume reports. Once either role or p10 has
consumed its attempt, a later boot refuses automatic stock replay. UNKNOWN needs
parent reconciliation; changing mode/arm does not erase that evidence.

## Runtime ordering and exclusion of a concurrent writer

Stock init/ueventd, enforcing startup, root-owned RAM inputs/entrypoints and
socket creator behavior remain. Init starts the oneshot writer, waits boundedly
for the daemon's real atomically published readiness and kernel-created fixed
SD node, then starts the oneshot selector. The exact removable mmcblk1p1 predicate,
shared mount namespace, VFAT contexts/DAC and mount options are retained from the
completed core. No repair, format, alternate path, USB/adbd/network startup or
service restart/resume loop was added.

The normal choice executes precisely `rescue-sd --offline-prearmed`, UID/GID2000,
`u:r:shell:s0`, and waits for its actual exit0 before sync and RB_AUTOBOOT. Source
preflight, authenticated actual status/PID/run continuity, full runtime p10
baseline, five phase proofs, CID/GPT/descriptor/holder/mount guards, durable
exclusive UNKNOWN report, whole-target readbacks and final ACKs remain. Source
inspection confirms the actual writer session and guard bodies are unchanged.

The stock choice executes only these fixed RAM programs/arguments, serially:

1. `rescue-sd --offline-stock-system`, UID2000 shell domain. New durable exclusive
   `system.attempt.txt` precedes role0 mutation. Actual full readback/final ACK,
   durable completion and successful child exit are mandatory.
2. `rescue-sd --offline-stock-boot`, same credentials, after that actual exit0.
   It uses its own `boot.attempt.txt`, exact per-role trigger, source preflight,
   full target readback/final ACK and durable completion. No normal reboot occurs.
3. The selector durably creates O_EXCL `p10.attempt.txt` with UNKNOWN and the actual
   manifest/arm/selection before initiating terminal writer retirement.
4. Over a separate root:root 0600 init-created socket, the selector authenticates
   the real os_rescue root/domain/PID and supplies actual manifest and ready nonce.
   The daemon accepts this control request only from UID0 `u:r:init:s0`, in its
   serial idle accept loop, with `uncertain_image==-1`. It freshly proves identity
   and both original images, transfers the actual abstract lifetime-lock FD with
   SCM_RIGHTS, then terminally `_exit`s. It never returns to writer service.
5. The selector requires the transferred exact lock and kernel EOF on that
   connection. No success timer/property or status snapshot substitutes for this.
   Target FDs are already closed before transfer; no writer code can run after
   the terminal exit call. The selector continuously retains the writer lock.
   Init has no restart action for the oneshot daemon. Both actual client children
   have finished before helper invocation.
6. The fixed root helper executes in existing `u:r:p10_restore:s0`, with lock FD3,
   an authenticated root-init socket peer FD4 and the selector's fixed read-only
   recovery source FD5. It accepts only `--offline-stock`. The selector opens FD5
   only at `asus-stock/recovery.bin`; no generic image/path/FD argument is accepted.
   Passing this held FD avoids granting the helper DAC override for UID2000 FAT
   files. The helper checks access mode, ordinary shape, label, FAT/dev179:33,
   exact length and unchanged source metadata, then loads the entire payload into
   anonymous RAM and seals it after the hardcoded stock hash check.

The helper independently loads root:root 0444 RAM `/rescue.original.manifest`,
requires its exact real two-role SHA and both hardcoded original hashes, checks
root/domain/peer, enforcing, no swap and the inherited lifetime lock, and freshly
proves actual CID/GPT/original SYSTEM/BOOT before even read-only p10 access.
It retains fixed p10 geometry/node/label/DAC/alias/holder/mount and descriptor
checks, exclusive O_DIRECT writable opening, readonly source sealing, exact
transition-prefix proofs, fsync and full final reopen/readback. The unchanged
`restore_core.h` sets UNKNOWN before writable open and cannot retry.

Fresh original-pair proofs occur in the retiring daemon, again at helper entry,
and again after the helper's full p10 readback. They are bounded whole-image
proofs, not per-chunk SYSTEM scans. The helper's per-p10-chunk transition scans
remain as in the existing restorer. It can write only the known original p10
bytes. No arbitrary p10, p20, GPT, BCB or DATA writer was introduced.

On helper exit0 the selector durably records `OUTCOME=OEM_RESET_REQUIRED`, noting
verified original SYSTEM/BOOT/recovery and that no factory reset was performed.
It syncs, closes all SD FDs, unmounts and requests RB_POWER_OFF. If report/sync/
unmount/power-off fails it stays in recovery. It never normal-boots incompatible
plain DATA/stale FDE metadata. Any earlier child/helper/signal/exec/proof failure
stops with evidence intact, no inverse/retry or reboot.

The user must later physically select OEM Recovery/factory reset, then Normal
Boot. Existing stock-reset evidence/p20 scope remains in
`../2026-11-06-asus-stock-userdata-recovery/`. This code performs neither reset
nor a p20 operation. Original recovery restore and stock crypto/reset/two-boot
persistence remain physically unqualified.

## Actual final binding, without a missing compiler header

The helper compiles now against the real original-pair manifest pin; it has no
`terminal_manifest_binding.h` dependency. Final assembly computes a 144-byte
`ASUSC001` binding from the actual completed operational first gzip member,
normalized actual header, normalized ramdisk wrapper and actual wrapped kernel.
It appends that binding as the sole root:root 0444 file in a canonical raw newc
second member. This retains the reviewed concatenated-member initramfs approach.

The helper loads only immutable RAM `/rescue.current.binding`; card metadata
cannot provide or replace it. It fully reads current p10 and requires the exact
bound first member/kernel/header/wrapper plus canonical binding capsule, Android
SHA1 ID and all zero padding. The helper executable itself is in that pinned
first member. No embedded full-p10 self-hash is used. Already exact stock p10 can
be skipped only after the exact stock digest and original-pair/source proofs.
The parent still independently full-readback-verifies the admitted deployed p10
before entry, as in normal installation; runtime RAM bindings are not independent
admission against compromised RAM or an adversarial pre-measurement p10 writer.

This final binding is a deterministic local byte join using genuine parent
inputs. No helper recompile, unavailable final-image hash header, original-p10
restore gate for normal installation or later inaccessible recovery replacement
is needed. The common default lacks this binding and the final authorities and
cannot automatically execute either installation profile.

## Policy and focused evidence

The input is the completed integrated policy
`4ec49d329396db332a9049cc4a25a886fe5c85a9aa6e2fc975ba1fcbc2060e21`.
The actual delta adds two isolated types (`stock_restore_exec`,
`os_rescue_control_socket`), 17 changed allow entries and one fixed init-to-helper
transition. Exact newly added permission bits are listed in
`evidence/actual-policy-delta.txt`. It adds root selector/helper entry, root
control/FD transfer, helper read-only source/filesystem access and selector report/
unmount access. No helper capability, allow-all or permissive rule was added.

Old constraints/validatetrans, original attributes, rules and individual ioctl
xperm datums are preserved. Actual constrained queries show shell/adbd/ordinary
os_rescue still cannot write p10/whole disk, and the helper cannot write BOOT,
SYSTEM, DATA, whole disk or its SD source. The new entrypoint denies shell and
os_rescue execution; only the root selector branch can invoke it. Legacy helper
entry rules remain on an old label with no executable in this core. Both socket
creator security contexts remain os_rescue; pathname labels are separately
compiled and checked. Normal flow never retires the writer or invokes the helper.

`evidence/build-log.json` records real serial compilation/linking and the focused
host cases: mode/arm/malformed-line refusal, normal/stock branch and role order,
failed-step stopping, four actual child exit outcomes, real SCM_RIGHTS plus
terminal EOF (and missing-FD refusal), actual original-pair parsing, fixed stock
shape, and wrong whole recovery hash refusal before any target callback. Token
transfer tests do not claim target peer labels or physical lock integration.
The initial helper compile rejected an unused parameter under Werror; it was
corrected without weakening checks, and the real helper then linked.

`artifact-checks.json` contains real ELF, constrained policy and compiled-context
results. `final-local-check.json` inspects actual cpio/product bytes and preserved
normal session/source/readback/phase guard bodies, genuine original manifest,
init graph and missing-binding-free compilation. No broad suite, independent
review, extra SDK, platform/kernel build or children were used.

All VM writes/builds used only the newly created owned prefix
`/srv/android/asus-offline-stock-fallback-20261107`, through the existing fixed
minimal-probe SSH transport; compiles were serial, one CPU affinity, 768MiB AS
bound. Only known existing small tooling/libraries were read elsewhere. The
independent product build's processes, cache, source/out, locks, logs and lifecycle
were neither inspected nor touched. No device/card/Wi-Fi/root operation, private
payload/table access, full real image copy/rehash or cloud operation occurred.

Physical Linux4.9/static-libc/stock-init/SELinux compatibility, actual SD detection,
FAT report persistence/capacity/timings, peer/FD transfer enforcement, p10
restoration, power-off and subsequent OEM reset/stock boot remain unproved.
Parent's actually installed/readback-verified SD-report probe is context only:
physical boot remains pending card insertion/detection. No additional suites or
review rounds are needed for this handoff.
