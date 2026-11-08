# Fixed RAM-side original p10 restoration

**Implementation complete; offline candidate remains unarmed and unexecuted.**
This closes the software implementation gap: a separately typed, terminal
operation can restore the exact original recovery while running entirely from
an already loaded rescue, without booting Android or using userdata. It does
not close physical commissioning, approve arming, or qualify a future full-OS
rescue profile. The delivered zero-record image deliberately refuses handoff.

The actual source, static AArch64 binaries, fixed original payload, derived
policy, compiled contexts, unarmed image, host receipt implementation and tests
are included. `HANDOFF.json`, `ARTIFACTS.json`, `SOURCE_PINS.json` and the
candidate's `session-contract.UNAPPROVED.json` provide exact current pins.
The former STOCK-only commissioning image remains unchanged.

## Exact final artifact pins

| Artifact | SHA256 |
| --- | --- |
| Unarmed image | `94e6747bc5998d7e5cf58a33280d362bb0dd97c14941c7fae6625117cc53ef91` |
| Complete padded p10 | `e3df64342477816bc9aa2c8bb44cb61adf7a0f910d2d016c339c3250ff8457e3` |
| Original payload | `902b2f06a01cca574b4aa374e67c4e7f8f0ed53f6e6a55017b6d96351f0f1f20` |
| ARM64 helper | `1d5c51991fd74129a1aac3694a860fca7c7fbf8d1e22cfa601620248de50b463` |
| Policy | `16f6ce7f25c1b56aba9e4179573c49a6c55f9b9fe3f18336029f6d83b5b4b2c2` |
| Compiled contexts | `d82c9ca28d1d9017aea5f58d1cb9b46f6122ef22953ab32b7b4a3a8ccd07186c` |

Image: 10317824 bytes. Combined ramdisk: 2841212 bytes; 1353092 bytes remain before the fixed reservation.

## Fixed scope and inputs

The only new writable device is p10 recovery: alias
`/dev/block/platform/mtk-msdc.0/11230000.MSDC0/by-name/recovery`, direct node
`/dev/block/mmcblk0p10`, major/minor 179:10, start sector 160184, 32696 sectors,
16,740,352 bytes. The payload is the complete original partition, SHA256
`902b2f06a01cca574b4aa374e67c4e7f8f0ed53f6e6a55017b6d96351f0f1f20`.
Both public initial/verify backup copies were read and compared. The host
preflights the fixed delivered payload through one no-follow descriptor and
holds its complete bytes in memory before protocol work.

The fixed STOCK-only manifest identity is
`605cdec038dafe3dddabfe92b8bd6cd189734f740230dfc362d02a43421e4e47`.
The helper requires exactly its two original SYSTEM/BOOT records. It reuses
CID SHA256 binding `c03db6320ba5e4e1916c2dce84f87ba26220102701675f1ed638c513b597b7d8`,
primary GPT `f87e70586706b06d029a2bc8521f1b8ae9176873cba1e5b4281cbaca816742ae`,
and backup GPT `2bf991125a74bf360d0cf4eb217df369ba2f78acf3dd312f26dc7695d2f31784`.
No raw CID was acquired. Runtime identity checks remain the original production
implementation. No p20, calibration, security, key or private preservation
payload was opened, copied or included.

The parent userdata contract and public aggregate preservation acceptance were
adopted as supplied. The original inverse restores SYSTEM/BOOT; this helper
supplies the missing p10 capability. Later original OEM reset still separately
owns its legitimate p20/p26/cache/para effects. Nothing here performs that reset
or normal-boots stock against unusable userdata.

## Implementation and transition proof

`source/rescue.c` contains only an optional `P10_HANDOFF` extension around the
original session/serve code. Opcode 0x30 is admitted only in IDLE, with two
records, no uncertain transaction, valid identity and whole original SYSTEM
and BOOT proofs. It preserves the accepted connection, original listener and
abstract lifetime writer lock across exec. After descriptor handoff begins,
any failure exits; it cannot return to a partially reconfigured old daemon.
`/sbin/p10-restore --handoff` is the sole executable/argument route.

SELinux transitions `os_rescue` to `p10_restore` through a dedicated executable
type. The old daemon gets no p10 write permission. The helper rechecks root,
Enforcing, exact domain, inherited lock, peer UID2000 and shell domain,
manifest identity, CID/GPT and the original SYSTEM/BOOT pair. It refuses active
swap; its working buffers are anonymous RAM. The inherited single writer lock,
oneshot service, no ordinary shell and narrow policy are retained.

The target stages exactly 16 chunks into a bounded 16,740,352-byte allocation.
It refuses early activation, extra bytes, wrong lengths and any payload hash
mismatch. `mprotect(PROT_READ)` seals the entire payload, followed by another
full hash. No writable p10 descriptor exists during staging. The target then
reads all actual p10 bytes into a separate bounded preimage allocation. Exact
stock yields SKIP only after that actual full read and hash, with no writable
open. Other bytes must match the exact immutable-container construction below.

Before writing, the host checks the returned actual prior digest against its
fixed generated full-image pin. The target rechecks the sealed payload and
actual whole p10 against the captured admitted preimage. It enters UNKNOWN
before opening only fixed p10 with `O_RDWR|O_EXCL|O_DIRECT|O_NOFOLLOW`.
The existing label, mode/owner, descriptor/path identity, alias, geometry,
holders, mount, CID/GPT and Enforcing checks remain in use. O_EXCL is an
additional block-device claim, not a substitute for those checks.

Each sequential chunk is written at its internally fixed whole-partition
offset. After every write and fsync, a complete actual p10 scan must equal the
already-written stock prefix plus the unchanged captured prior suffix. Every
chunk begins with identity/descriptor guards. Thus legitimate prefix changes
have an explicit proof; no global recovery guard is cached, disabled or
weakened. Final success requires fsync, close, fresh read-only reopen, another
full actual read, guards and the exact original hash. Partial I/O is failure,
not a request to retry the remaining range.

Any uncertainty is terminal. The helper retains the writer lock and only
serves terminal status or fixed read-only p10 observation on new authenticated
connections. No second attempt, ordinary RSC1 transaction, fallback write,
discard/TRIM/erase, arbitrary ioctl, reboot or automatic restart is reachable.
An EOF or lost acknowledgement can leave target DONE while the host correctly
remains UNKNOWN. Host `attempt.json` is fsynced before the first request;
`receipt.json` is atomically published and directory-fsynced only after exact
final verification. Failed receipt persistence retains durable UNKNOWN.
The detailed frame contract is in `PROTOCOL.md`.

## Image binding without a self-referential hash

The final Android/MTK ramdisk contains two archives:

* A deterministic gzip core, padded with zeroes to a four-byte boundary. It
  contains the exact stock init/adbd, original fixed proxy, extended daemon,
  narrow policy/contexts, public ADB key and zero-record identity manifest.
* A canonical uncompressed newc archive containing only the static helper.

The core is built first. Its normalized Android header, wrapped stock kernel,
MTK wrapper and exact padded gzip bytes are pinned in generated
`source/core_binding.h`. The helper is then compiled against those immutable
pins. At runtime it verifies those components, the derived Android SHA1 ID,
canonical helper archive metadata and every padding byte. The helper archive
must equal the actual read-only RAM-loaded `/sbin/p10-restore` bytes.
There are no request-supplied hash or layout fields.

The helper does **not** claim cryptographic self-authentication against an
arbitrary hostile RAM/kernel/root actor. The parent independently binds the
entire final padded p10 image and exact helper before deployment; the fixed
host binding is generated only after final assembly. That external trust
boundary authenticates the RAM helper. Under it, the target's structural check
admits one exact prior container, and the host additionally compares its full
actual digest before activation. No old `cb30...` pin is reused and no image
contains its own claimed full SHA256. Unknown future full-OS containers or
five-role manifests remain refused until separately reviewed and bound.

The delivered image is zero-record and `ARMED=False`. The bound production
helper also requires the exact two-role manifest, so it cannot execute from
this unarmed candidate. A parent-approved fixed STOCK-only rebuild must replace
only the selected manifest input, rebuild core then helper, recompute the
entire image pin and regenerate the fixed host binding. Merely editing a
manifest or supplying the old commissioning pin cannot work. No such arming
build or approval was performed here.

## Evidence and limits

Final results are recorded in `evidence/`:

| Evidence | Result | What it establishes |
| --- | --- | --- |
| `core-tests.json` | 24 passing cases | Actual production core; exact full-size payload and candidate preimage; incomplete/corrupt payload, short I/O, seal/open/fsync/close/reopen failures, suffix/prefix mutation, bad container fields, complete readback mismatch, SKIP, sealed-memory mutation and no second attempt |
| `host-tests.json` | 16 passing cases | Actual production session/exchange; fragmented transport, timeout, lost final receipt, mismatch, override rejection, partial activation, reconnect after UNKNOWN/DONE and unarmed host refusal |
| `host-durability.json` | 5 passing cases | Failed initial fsync prevents transport; final publication failure retains durable UNKNOWN; bad/short/symlink payload rejected |
| `build-log.json` legacy run | 24 passing original cases | Original ASUSR002/RSC1 regression suite using isolated regular files |
| `policy-checks.json` | 72 checks, including 29 compiled lookups | Actual binary policy decisions and 907-row compiled contexts, including block-mode `-b`, symlink and regular-file lookups |
| `policy-structure.json` | Pass | Original AV rules/constraints/permissive map preserved; new domain has exactly one block writer and four BLKGETSIZE64-only ioctl entries; no broad inherited attributes |
| `concat-guest.json` | Pass | Existing ARM64 fixture kernel unpacks the exact two candidate members and executes the actual helper's non-operative argument refusal; no disks, USB or network attached |
| `independent-container.json` | Pass | Independent Android/MTK/newc parser checks actual image, padding, ID, ELF static ARM64 identity, stock kernel/init/adbd, manifest and layout |
| `reproduction.json` | Pass | Fresh daemon/core/helper/archive/image/full-p10 reproduction in another owned subdirectory is byte-identical |

Host storage adapters use bounded memory or ordinary fixture files, never real
block devices. Production descriptor, O_EXCL and hardware durability behavior
are **not** claimed from injected storage. The QEMU test uses a test-only third
archive with an observer, an existing compatible kernel and no block devices;
it does not boot the hardware stock kernel or prove physical rescue init,
USB/authentication, domain transition or eMMC behavior. The actual delivered
kernel is nevertheless byte-identical to both original recovery backups.

Original RSC1 compiled with the extension disabled reproduces the earlier
production daemon exactly (`30ae9252...`). The extension keeps its per-chunk
recovery hashing unchanged. The new helper's original-pair proof is performed
both before and after exec, adding two whole SYSTEM/BOOT reads at runtime.
No such large reads occurred in these tests. These are correctness checks,
not latency measurements; the parent must budget and observe them.

All build/test children used one allowed CPU and a 1 GiB address-space limit;
compilation was sequential. QEMU used one vCPU, 384 MiB RAM and a 16 MiB JIT
cache. No new kernel build was needed. Earlier failures are retained in the
owned builder's revision directories and summarized in `evidence/DEVELOPMENT.md`.
The significant packaging defect was missing four-byte alignment between
archive members; the final candidate and preimage binding both include it.

## Parent-only continuation

1. Review the actual source, exact pins, policy delta, fault evidence and
   immutable-container trust boundary. Retain the original SYSTEM/BOOT inverse,
   both original recovery copies and the aggregate preservation acceptance.
2. If the parent later approves a STOCK-only operational build, use the fixed
   existing two-role manifest. Rebuild core/helper/full image and fixed host
   binding together. Review the resulting new exact padded p10 pin; do not arm
   by changing the delivered JSON or toggling only `ARMED`.
3. In a separately authorized physical session, establish authenticated proxy,
   root/domain/Enforcing, correct unit/GPT/node/alias/label, empty swap, mounts,
   holders and exclusive access. Prove the complete actual prior p10 digest
   against that exact final artifact, and retain the qualified direct original
   recovery entry/fallback plan. The concat fixture is not physical boot proof.
4. Complete the original SYSTEM then BOOT inverse and its durable host receipts.
   Establish actual idle/no uncertain transaction. Run only the fixed terminal
   restorer on that already loaded RAM rescue; preload and verify all original
   bytes before activation. Host receipt loss means UNKNOWN regardless of later
   status; observe actual bytes read-only without restarting or retrying.
5. Only the parent can decide direct original recovery entry after accepted full
   original p10 readback. Later supervised OEM reset, stock crypto/data startup,
   persistence and factory acceptance remain separate unqualified gates.

No device command, arming, physical GO, reset, cloud lifecycle action, shared
source mutation, private data access or third-party contact was performed.
The existing build VM was used only for the owned offline fixture. This is
software implementation and evidence, not physical rescue readiness.
