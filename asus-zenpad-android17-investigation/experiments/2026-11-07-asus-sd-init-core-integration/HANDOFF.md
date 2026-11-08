# Built SD init/core handoff

Common integration is built. It is not a flash-ready candidate. No real install
SYSTEM/BOOT admission or arm ID was supplied, fabricated or generated. No device,
card, USB, ADB, Wi-Fi or independently running product-build operation occurred.

## Actual delivery

`artifacts/ARTIFACTS.json` contains exact sizes and SHA256 values:

- `artifacts/os-rescue`: linked static AArch64 ET_EXEC, 776040 bytes.
- `artifacts/rescue-sd-supervisor`: linked static AArch64 ET_EXEC, 775584 bytes.
- `artifacts/rescue-sd`: unchanged static offline frontend, 775736 bytes,
  SHA256 `0d7ad266bbe5fefc1ce7db8716d209ed3a6da3d4de124e1d99d84a4634d5e7cb`.
- `artifacts/sepolicy`: actual compiled binary policy, 390982 bytes,
  SHA256 `4ec49d329396db332a9049cc4a25a886fe5c85a9aa6e2fc975ba1fcbc2060e21`.
- `artifacts/file_contexts.bin`: actual Android compiled contexts, 224877 bytes.
- `artifacts/common-rootfs.cpio.gz`: assembled 1693147-byte common rootfs,
  SHA256 `47838aff086c7c70204c7c2f5ce12b3c985428b5076691bafa3047a342f5013b`.
  It contains the preserved stock init and its ueventd symlink, executable
  artifacts, actual policy/contexts, minimal properties, ueventd rules and init
  services. It contains no manifest, arm ID, adbd, command shell or p10 helper.
  It cannot start the SD client automatically. The writer fails closed without
  its manifest. It is a reusable nonoperational core, not an install candidate.

Joined source is in `source/`. `rescue.c` differs from the completed offline
writer only by the readiness publication and its syscall include; see
`evidence/daemon-readiness.patch`. `common.h`, `sha256.h`, `sd_mount.h`,
`recovery_phase.h`, `sd_frontend.c`, and the delivered frontend executable are
byte-identical to the completed offline spike. The default PLAN and separate
online profile remain in that frontend. There is no new raw writer.

## Operational startup after the real final join

`source/init.common.rc` starts stock ueventd once, makes/relabels the RAM state
and mount directories and entrypoints, then starts `os-rescue --serve` once.
The existing init-created stream socket remains root-created in the os_rescue
socket security context, pathname `/dev/socket/os_rescue`, DAC 0600 shell:shell,
pathname label `os_rescue_socket`. The socket line has no context override;
stock init takes the creator context from the service seclabel, as in the prior
core. Pathname context and connected socket peer context remain distinct.

The daemon initializes the actual RAM manifest/run nonce, acquires the exclusive
abstract lifetime writer lock, validates the inherited fixed socket and calls
real `listen()`. Only then does it write/fsync/close `ready.new` and atomically
publish `/dev/rescue-state/ready` with Linux4.9 `renameat2(RENAME_NOREPLACE)`.
A stale ready or temporary file causes failure; no file is forged by init and
there is no readiness property, timer-based success or replacement of readiness.

Only final assembly appends `source/init.offline.action.rc`. Its `on init`
action is parsed after the common action; stock init explicitly queues `init`.
An untriggered `on boot` action is not used. It waits at most 30 seconds for
actual readiness and 60 seconds for the actual `/dev/block/mmcblk1p1` node,
then starts the disabled, oneshot supervisor. Native init wait errors do not
prove readiness: the supervisor rechecks the ready file and node itself.
No service-exit/property restart, cleanup, report deletion or resume action
exists. A late card after these waits does not cause a later execution.

The fixed root `u:r:init:s0` supervisor accepts no arguments. It checks enforcing,
root-owned ordinary tmpfs readiness and the exact root-owned immutable RAM
client executable/label. It applies the unchanged `sd_identified()` predicate:
removable SD mmcblk1 179:32, partition1 179:33, distinct internal ancestry,
canonical sysfs links and bounded geometry; node DAC 0600 root:root and its
exact new block label are also required. No node is fabricated. Stock ueventd
creates it from the kernel event, with the fixed DAC/context rules.

It mounts only `/dev/block/mmcblk1p1` at `/mnt/rescue-sd` with filesystem `vfat`,
`rw,nodev,nosuid,noexec`, `uid=2000,gid=2000,fmask=0177,dmask=0077`,
`context=u:object_r:rescue_sd_file:s0`, and
`fscontext=u:object_r:rescue_sd_fs:s0`. These give UID2000 file 0600/directory
0700 access, without executing card content. It validates the resulting mount
with the unchanged SD mount predicate. No format, fsck, repair or alternate
path/filesystem is implemented. The parent must retain the pre-created
`asus-rescue-report` and the existing exact source tree contract.

The supervisor forks exactly once, sets the fixed shell exec context, clears
supplementary groups, sets GID/UID2000, and fexecves the held RAM executable
with exactly `/sbin/rescue-sd --offline-prearmed` and a fixed environment. All
services share init's mount namespace; no service uses namespace isolation.
The client still authenticates actual daemon SO_PEERCRED/SO_PEERSEC/status,
RAM manifest, PID/run continuity, SD source/trigger and all unchanged runtime
identity, descriptor, holder, mount, CID/GPT, p9/p25/p26/p10 guards.

The parent waits for the actual child's waitpid status, without a success timer.
Only normal exit0 reaches `syncfs(cardfd)`, `sync()` and `reboot(RB_AUTOBOOT)`.
The fixed offline client returns zero only after all three roles' full readback,
final ACKs and the final durable report. A nonzero exit, signal, exec failure,
syncfs failure or rejected reboot request stays in recovery, with reports kept
and a best-effort RAM `supervisor.result`. There is no timeout reboot, retry or
inverse. The writer/client's own `no_reboot=1` output still describes those
programs; the explicitly added supervisor owns the success-only normal reboot.
A hung child leaves recovery running. Report durability on actual hardware and
power loss is not established by these host checks.

The order remains SYSTEM2 -> DATA4 -> BOOT3. O_EXCL durable UNKNOWN `attempt.txt`
precedes mutation; pre-existing attempts refuse execution across boots. Full
runtime p10 capture and the accepted phase proofs remain unchanged. There is no
self-referential full-p10 pin or card manifest authority. Parent must still
independently full-readback-verify the deployed admitted p10 before entry and
maintain the accepted no-concurrent-p10-writer/no-fd-rebinding invariant.

## Actual narrow policy change

The input is the accepted DATA-corrected 390437-byte policy, exact SHA256
`3d982859fdbf06336d6274e7e700ca64a2551effd769a8cb119b4fed97388815`.
`source/policy_build.c` adds five isolated types with no broad stock attribute
membership: `rescue_sd_exec`, `rescue_sd_supervisor_exec`, `rescue_sd_file`,
`rescue_sd_fs`, `rescue_sd_device`. The actual binary delta is **22 changed allow
keys and one init state-file transition**, listed with only newly added permission
bits in `evidence/actual-policy-delta.txt`. Removing unnecessary directory read
permissions reduced permission bits, not the count of affected keys.

The delta covers RAM exec association/entrypoints, init-only fixed SD block
mounting, shell source/report and filesystem access, traversal of `/dev/socket`,
RAM authority reads, inherited init fd use and supervisor state output. The real
stock `vfat` filesystem label gets init `relabelfrom`; the explicit new filesystem
and context labels get mount/relabel/associate access. The underlying mountpoint
is explicitly rootfs; compiled lookup verifies it instead of assuming stock
`/mnt` (which was tmpfs). Stock genfs for these MMC sysfs paths is `sysfs`, proc
self mountinfo is covered by proc/self-domain reads, and selinuxfs stays read-only
for shell. Existing shell peer socket/process transition rules already suffice.
The socket creator behavior and authenticated peer checks were preserved.

`policy_delta` compares inherited rules (including individual xperm datums),
constraints/validatetrans, original type attributes and permissive bitmap.
`policy_constraints` queries effective TE/MLS/RBAC decisions in the actual output;
shell/adbd/os_rescue still lack p10/whole-disk write, and shell/os_rescue lack
SD block write. The daemon DATA allow plus BLKGETSIZE64 restriction remains.
No permissive mode, allow-all, kernel change, ordinary daemon p10 write or p20/GPT
write was added. Old helper-domain rules remain in policy, but its executable,
service and handoff are absent from the normal rootfs and linked daemon.

## Final assembly command

The parent supplies the **real admitted five-role ASUSR002 file**, its **actual
64-lowercase-hex-plus-LF arm ID file**, and the existing physical `Image.gz-dtb`
artifact. The packager consumes the admission product; it does not recreate or
prove raw-image admissions, read SYSTEM/DATA images or generate an arm ID. Its
parser rejects a stock pair, wrong roles/geometry/GPT/stock BOOT, truncated tables,
zero placeholder digests and non-install pairs. It checks delivered input pins.
No synthetic five-role fixture was generated to exercise a successful final join.

From the ideas workspace, with the three variables pointing to those real files:

```sh
python3 -B 2026-11-07-asus-sd-init-core-integration/scripts/final_package.py \
  --manifest "$ASUSR002_MANIFEST" \
  --arm-file "$ASUS_SD_ARM_FILE" \
  --kernel "$ASUS_LINUX49_IMAGE_GZ_DTB" \
  --output-dir 2026-11-07-asus-sd-init-core-integration/artifacts/final
```

The absent output directory is mandatory. Output is `candidate.img`, full-length
`candidate.p10.raw`, operational rootfs, `assembly.json`, and the exact
manifest/arm/selection-bound `execute.trigger` to stage deliberately later. The
manifest and arm are embedded root:root 0444 on RAM rootfs. No card/deployment
operation is performed. The fixed source tree and empty report directory remain
required; an existing attempt must not be deleted as a restart mechanism.

`source/package_core.py` uses the reviewed LK/MTK wrappers, exact 92-byte header
and initrd relocation. It requires kernel SHA256
`e9cde06e85e752aec0433ea37fa926c31b4f7a72cd55453762ec6870e5bb5bf1`
and config SHA256
`10b212cabd28aad012582e86c64695ccd450650b4e09ec8da30c21e094f377c2`.
Compressed/decompressed Image bytes are preserved, only permitted chosen DT
metadata changes, the 4MiB compressed initrd reservation/memory checks remain,
and the final image/full-p10 hashes are calculated from actual generated bytes.
The current 1.69MiB common gzip leaves room for the real manifest/arm; the final
join measures its actual size. No kernel build or kernel/out read was done here.
Final image packaging with genuine inputs remains unexecuted because they are
not available. These checks do not establish physical Linux4.9 boot support.

## Separate deliberate stock fallback

Normal install retains custom recovery. It neither invokes nor requires the
original-p10 restorer, and is linked without P10_HANDOFF. There is no concurrent
reachable normal p10 writer. Original SYSTEM/BOOT backups and existing rollback
source/options are preserved in prior spikes and in the unchanged SD frontend.
A later deliberate stock fallback restores original SYSTEM role0, then BOOT
role1, with separate exact selections/attempt evidence and fresh proofs; it
must not reuse the fixed normal-install supervisor to reboot after a partial
rollback. UNKNOWN requires explicit reconciliation, not an automatic inverse.

The existing source path is
`../2026-11-06-asus-final5role-shared-terminal-gate/source/`, with the staged
restorer under `../2026-11-06-asus-ram-original-recovery-restorer/` and stock
userdata/reset evidence under `../2026-11-06-asus-stock-userdata-recovery/`.
The exact pending helper join is **real manifest SHA -> missing production
terminal_manifest_binding.h**, plus new actual core/header/wrapper/kernel/gzip
bindings and the resulting helper/container identity. Frozen prior core bindings
and NONDEPLOYABLE test headers must not be substituted. Both daemon and helper
must freshly prove the actual original SYSTEM/BOOT pair before the separately
selected original-p10 restore. This normal packager intentionally creates no
helper binding or helper-enabled candidate; its compilation is independent of
that pending join. The old helper is not physically qualified for this new core.

Original SYSTEM/BOOT alone do not restore stock-compatible userdata. The distinct
reported stock route continues through separately restored original recovery and
supervised OEM factory reset, then stock crypto/startup and two-boot persistence
acceptance. The prior report says OEM reset may change all p20; that is not a new
p20 writer or an action authorized by this normal installer. No stock fallback,
userdata reset or original-recovery restoration ran here.

## Focused evidence and genuine limits

`evidence/build-log.json` records the serial real compiles/links and four actual
host waitpid cases: exit0, exit1, SIGKILL and exec failure exit127. Only exit0
calls mocked sync/reboot; no host/device reboot was attempted. The tests establish
exit-status handling, not target SELinux/DAC execution or a real installation.
`artifact-checks.json` contains actual ELF, constrained permission decisions and
compiled-context lookups. `final-local-check.json` inspects the actual common
cpio, preserved artifacts/guards, init service graph, Python syntax and rejection
of the actual prior two-role manifest. No large test/review suite was rerun.

Two failed host policy-diff checks are retained in the command log: the initial
comparison incorrectly compared the first matching xperm datum (and padding)
instead of each matching driver datum. The corrected checker preserves each
old datum and passes. This did not require weakening target policy or guards.
A local lexical rc check also initially mistook `.arm ` for an `rm` command;
the final check compares command tokens. Neither was a target execution failure.

All VM writes/builds were inside the new exclusively created prefix
`/srv/android/asus-sd-init-core-integration-20261107`, using the minimal-probe's
existing fixed SSH helper. Only known existing small policy tooling/libraries
were read elsewhere. Builds were serial, one CPU affinity, 768MiB address-space
bound and bounded subprocess times. No process/cache/log/lock/source/out query
or modification of the independent Android product build occurred. No native SDK,
platform build, source/provenance sweep, cloud lifecycle or private payload read.

Physical Linux4.9 boot and stock init/static-libc/SELinux compatibility, real
removable SD enumeration, enforcing peer labels, same namespace, FAT report
persistence/capacity and storage timings remain unproved. The parent's existing
small SD report probe is still the first hardware trial. The final manifest's
OS images, including Play/Google retention, remain parent admission inputs;
this work changes no OS product content.
