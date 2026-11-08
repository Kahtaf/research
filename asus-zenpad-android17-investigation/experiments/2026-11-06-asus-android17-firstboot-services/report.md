# SDK 37 first-boot services: implementation handoff

**Result:** a source-supported software service path is staged. Add the existing
`android.hardware.keymaster@4.0-service`, declare its real HIDL/default instance,
and select the existing post-data APEX mode with `apexd.config.use_fiemap=false`.
No platform code patch or fabricated service is needed. Keystore still reads
the activated APEX list, computes its module information/hash, applies its
existing legacy-version rules, and sets its own completion property.

**25 offline source/config checks passed.** Compilation and runtime remain
unverified. This clears the *unselected backend/configuration* part of blocker
4; it does not establish that the tablet boots, that an external data volume
works, or that the resulting installed graph is valid. Stock FDE remains intact
and unsupported by current vold. No physical test is authorized by this report.

All new files are confined to this spike. No VM writes/builds, device actions,
cloud actions, goal changes, other agent-folder edits or subagents were used.
Source was read over the orchestration README's strict-host-key SSH connection.

## Inputs and evidence

- Read root `AGENTS.md`, the orchestration README, and the full-product report,
  particularly remaining blocker 4 and the integration sequence.
- `evidence/source/` contains selected actual `/srv/android/lineage24` files,
  with hashes in `evidence/source-sha256.json`. Missing-path probes are recorded
  as missing; they are not treated as source evidence.
- `evidence/build-state.json` records repository HEADs and existing Soong
  variable excerpts. The current **minimal** `lineage_p00a` variables say
  `Platform_sdk_version=37`, `Shipping_api_level=23`; these are not a freshly
  evaluated full product. No envsetup/lunch/get_build_var/build was executed.
- `evidence/candidate-inputs/` is a read-only snapshot of the full candidate's
  relevant device files, independently hashed. The candidate was not edited.
- The final consistency check found concurrent parent-owned additions of
  connectivity and Google inheritance in `device.mk`; the initial snapshot
  no longer matches that one file. `evidence/candidate-drift.json` records both
  hashes. `evidence/concurrent-inputs/` captures the later device file,
  connectivity product and pinned Google wrapper/ARM64/common makefiles.
  Those additions select no KeyMint, Keymaster, keystore, Gatekeeper or
  AuthSecret service, so this service selection remains applicable. They were
  read, not modified. Retain those additions when integrating this handoff.
- `evidence/product-service-selection.json` records the service-related lines
  and file hashes from actual platform product and Lineage config makefiles,
  plus existence-only checks for optional key/product files. No private key
  material was captured.

## Inheritance: what exists and what is missing

The full candidate's `device.mk` inherits `full_base.mk`. The exact system
chain is `full_base -> generic_no_telephony -> handheld_system -> media_system
-> base_system`. The captured `base_system.mk:127,149` already selects
`gatekeeperd` and `keystore2`. `keystore2/Android.bp` installs its init rc and
system VINTF fragment and links its compatibility code. The compat Binder
service is brought up in-process by keystore; it is not another product daemon
to add. Neither generic inheritance nor the captured Lineage/graphics product
inputs selects a KeyMint or Keymaster backend.

The parallel `generic_no_telephony -> handheld_system_ext -> media_system_ext
-> base_system_ext` chain supplies `hwservicemanager` through
`PRODUCT_PACKAGES_SHIPPING_API_LEVEL_34`. Actual `build/make/core/main.mk:1007`
selects that list when shipping API is at most 34. Thus ship 23 already has the
HIDL service manager; do not add redundant package entries or spoof its
disabled/readiness properties. `hwservicemanager.always_sets_disabled=true`
in base_system means the manager reports its own enabled/disabled state; it
does not by itself disable HIDL.

`build/make/core/soong_config.mk:713-720` also adds
`system/hwservicemanager/hwservicemanager.xml` to the system_ext manifest inputs
when that inherited shipping-API package list contains the manager. Existing
Soong `SystemExtManifestFiles` confirms this exact input in
`evidence/hidl-manifest-buildvars.json`. Its HIDL manager/token declarations
have max-level 8; verify they survive the final legacy device target-level
merge. There is no reason here to turn on `PRODUCT_HIDL_ENABLED`, invent a new
target-level, or duplicate these framework HAL declarations in the device
manifest.

This is a source trace, not a claim that a new final installed graph was
evaluated. Parent must repeat the effective package/property and assembled
manifest checks after integrating all agents and Google inputs. Optional
`vendor/extra/product.mk` was absent at capture. Product overrides, required
module expansion, namespaces, and graphics ABI choices still belong to the
parent's real build.

## Why the selected software backend works in the existing design

Source paths below are relative to `evidence/source/`:

1. `hardware/interfaces/keymaster/4.0/default/service.cpp` constructs
   `V4_0::ng::CreateKeymasterDevice(SecurityLevel::SOFTWARE)`, registers the
   real service and joins its HIDL thread pool. `Android.bp` links the real
   `libkeymaster4`; the service implements cryptographic operations through
   `AndroidKeymaster4Device` and `PureSoftKeymasterContext`. This is not a
   success-only stub. Its upstream rc is `class early_hal`, with the real
   `android.hardware.keymaster@4.0::IKeymasterDevice/default` interface.
2. `system/security/keystore2/src/globals.rs` uses native AIDL KeyMint only if
   it is declared. Otherwise it starts km_compat and requests the legacy
   wrapper. No native KeyMint is declared by this staging.
3. `src/km_compat/km_compat.cpp:1468` explicitly accepts an insecure software
   Keymaster when no secure backend is available. It routes that object via
   the historical `TRUSTED_ENVIRONMENT` lookup slot. **That slot name is not
   its reported hardware security level.** `getHardwareInfo():439` copies
   the backend's SOFTWARE level; `processLegacyCharacteristics():319` maps
   the software-enforced authorizations as SOFTWARE. `raw_device.rs:70`
   preserves `hw_info.securityLevel`, explicitly allowing the requested and
   actual levels to differ. No TEE, StrongBox or hardware attestation claim is
   introduced here.
4. `boot_level_keys.rs:91` has a pre-Keymaster-4.1 path. It chooses
   `MaxUsesPerBoot(1)`, generates/loads a real HMAC key, checks the actual
   security level/authorization, signs `Create boot level key`, and derives
   boot-level keys. This path needs a working keystore database and genuine
   crypto operations; the runtime test must verify those, not just a property.
5. Keymaster 4.0 lacks the newer `earlyBootEnded` method. The existing 4.1
   support wrapper returns `UNIMPLEMENTED` for a 4.0 backend; the existing
   km_compat implementation checks Binder transport success and returns OK.
   We do not alter that legacy behavior or pretend it enforces modern
   EARLY_BOOT_ONLY. Keystore's chosen boot-key strategy for version 40 is
   MAX_USES_PER_BOOT. Real 4.0 crypto service functionality remains essential.
6. `maintenance.rs:520` reads the active module list, DER-encodes it and hashes
   it. Sending `setAdditionalAttestationInfo(MODULE_HASH)` requires normalized
   version **400** (KeyMint v4). Legacy Keymaster 4.0 reports **40**. The
   existing `call_with_watchdog():176` deliberately skips that unsupported
   operation for old versions. An absent StrongBox is also explicitly allowed;
   an absent default backend is not. Only after this platform path completes
   does keystore write `keystore.module_hash.sent=true`.

The property therefore means that the platform's module-information step
completed for the available service versions. It does **not** mean this legacy
software backend received or securely attested the module hash. No property
writer, init wait removal, attestation substitution or invented hardware
feature is staged.

The 4.0 target is smaller than introducing a new service. Its build definition
does not require a hardware-keystore permission XML and has no bundled VINTF
fragment, which is why the one new manifest fragment is necessary. The 4.1
reference target pulls a hardware-keystore feature XML. The Rust nonsecure
reference TA currently reports `TrustedEnvironment` in its source. Neither is
selected. No hardware-backed attestation, Play Integrity result or production
key protection is claimed for the chosen software reference implementation.

## APEX activation and the missing /metadata filesystem

The actual `trunk_staging` aconfig enables `mount_before_data`. Init's
`apex_init_util.cpp:163` chooses that mode using FIEMAP support, compressed-APEX
configuration and the metadata marker. Apexd's main function independently
uses the same FIEMAP property and `ro.init.mnt_ns.count`.

The staged **supported configuration input** `apexd.config.use_fiemap=false`
causes init to retain two mount namespaces and apexd to leave both
`uses_pinned_apex` and `mount_before_data` false. This makes the intended
post-data boot path deterministic even if APEX compression defaults change.
It is not strictly necessary for every possible fresh built-in-only APEX set:
missing image metadata itself is also handled as empty. It is appropriate for
this profile because there is no persistent metadata store for pinned extents.
It does not disable APEX signature checking or fake readiness, and it is not
a switch that disables all staged-update APIs.

On a fresh scratch data volume with only preinstalled APEXes:

- `ApexSessionManager::Create()` only constructs an object.
  `GetSessions()` tolerates `ENOENT` for `/metadata/apex/sessions` and returns
  an empty list. `ProcessSessions()` then returns without applying/reverting
  sessions. `ApexStorageMetadata_Load()` also treats an absent image-metadata
  file as empty; no synthetic metadata partition is needed to enumerate the
  preinstalled set.
- In the selected mode, bootstrap activates the bootstrap APEXes. After data
  directories exist, `ActivateApexesOnStart()` activates the normal set,
  including decompressing compressed APEXes into `/data/apex/decompressed`
  when necessary. `apexservice` registers before `apexd.status=activated`.
- Both DE snapshot routines iterate activated **sessions**. With none, there
  are no session snapshots/restores to perform. The user-DE directory scan
  must still succeed. Actual `vold initUser0` and the normal init-created
  `/data/misc_de` structure are required; it is not a no-op replacement.
  `--snapshotde` sets `apexd.status=ready` only on its successful return.
- `vold/Checkpoint.cpp` determines support from fstab checkpoint flags. The
  scratch profile supplies none. Missing checkpoint state is not a request
  to format storage. This does not establish checkpoint/rollback support.

Platform init still attempts to make `/metadata/...` directories; without a
writable mount those commands can log failures. There is no global success
promise for every metadata consumer. The source trace establishes the APEX
first-activation path, not usable staged installs, persistent rollback,
checkpointing or OTA recovery. Those require separately designed persistent
storage. Do not alias cache, the stock FDE metadata area or scratch `/data`
to `/metadata`, or create a RAM metadata facade to imply persistence.

## Gatekeeper and AuthSecret scope

Neither is in the module-hash/APEX/adbd dependency chain. `gatekeeperd` is
already inherited, but its constructor can log that no Gatekeeper HAL exists.
The APEX wait does not wait on it. For a fresh user with no credential,
`SyntheticPasswordManager.createLskfBasedProtector()` explicitly skips
Gatekeeper enrollment for an empty LSKF. `LockSettingsService` treats absent
AuthSecret as supported absence and returns from `callToAuthSecretIfNeeded()`.
Do not declare an absent HAL, which could turn lookup into a blocking wait.

No Gatekeeper, Weaver or AuthSecret service is added for this bounded gate.
Setting a lockscreen credential is a later genuine requirement. The source
contains `ACCOUNT_REDACTED`, which performs real
password work and carries its own VINTF fragment, but its `.software` executable
does not match the default gatekeeper file-context rule captured here. Simply
adding the package without a matching label is incomplete. It also needs
credential persistence, wrong-password rejection, restart behavior and
Keymaster auth-token interoperability tests before it is a usable lockscreen
solution. This handoff does not silently claim that later task is complete.

## Fresh data strategy, preserving stock FDE

Use a separate dedicated external ext4 volume for an experimental test image.
The non-installable `configsnippets/fstab.mt8163.external-scratch.in` replaces
the original `/data` entry with one unresolved external block-device token.
It retains the existing system read-only first-stage entry and bounded zram.
It contains no stock userdata, cache or metadata mount and no formatting,
fsck, encryption or checkpoint flags. **Replace**, never append beside, the
original data row in both ramdisk and vendor copies.

The parent must identify and record the actual external medium/controller,
block path, capacity, partition extent and fresh ext4 UUID before substituting
the token. Device absence and untested external-controller support mean that
identity is presently a real unresolved input, not a guessed `mmcblk1` path.
See `configsnippets/README.md` for the precise preparation and mount gates.
An 8 GiB or larger dedicated test volume is a planning allowance; first-boot
usage with the complete Google product still needs measurement. Prepare/check
the new filesystem off-device, verify 4.9-compatible ext4 features and
`ro,noload` mounting, then test writable mounting and O_DIRECT on that volume
under the parent's hardware-test authority. No medium was formatted here.

Plain tmpfs `/data` is not staged: `apexd_loop.cpp:599` opens backing files with
O_DIRECT and permits buffered fallback only for EROFS, squashfs and overlayfs.
Compressed APEX extraction into tmpfs can therefore fail when it is mounted as
an APEX. A loop-mounted ext4 image backed by RAM could address that filesystem
issue but would add unverified early loop setup, SELinux and 2 GiB memory
pressure; it is not a proven substitute in this handoff.

No FBE flags are needed for the unencrypted scratch profile. Actual
`IsFbeEnabled()` tests `ro.crypto.type=file`; init applies `encryption=Require`
directory policy only under that condition. Vold's `fscrypt_init_user0()` and
user-storage paths retain a non-FBE branch that creates ordinary directories.
Do not spoof `ro.crypto.*`. Stock FDE unlock/migration remains unavailable;
the presence of old cryptfs filenames does not change the parent's AIDL finding.

Scratch data can preserve development state between tests but does not fulfill
the final internal persistent-tablet goal. Before any internal-data migration,
parent needs a complete local backup/restore plan and an explicit migration
decision. Encryption-area snapshots alone are insufficient. No wipe is implied.

## Ordered parent integration and build checks

1. Wait for graphics ownership to return. Copy only
   `stagedsource/device/asus/p00a/firstboot/` into the integrated device tree.
   Add `configsnippets/device.mk.inc` after shipping API is set. Append
   `configsnippets/BoardConfig.mk.inc` **after** the current
   `DEVICE_MANIFEST_FILE := ...` assignment. Keep the original graphics manifest.
   Install no new rc; the platform package already owns its service.
2. Keep the parent/full-product Android 17 init, keystore, APEX, Google payload
   and authenticated USB implementation. There is no Google payload edit in
   this spike. Do not add the 4.1/C++ KeyMint hardware-feature dependencies or
   an AIDL KeyMint declaration alongside this service.
3. Once source mutations/builds are safe, evaluate the actual integrated
   product with the established `lineage_p00a-trunk_staging-userdebug` lunch.
   Inspect `PRODUCT_PACKAGES`, `PRODUCT_PACKAGES_SHIPPING_API_LEVEL_34`,
   `PRODUCT_SHIPPING_API_LEVEL`, `PRODUCT_SYSTEM_PROPERTIES`,
   `DEVICE_MANIFEST_FILE` and `TARGET_COPY_OUT_VENDOR`. Confirm shipping 23,
   the one 4.0 backend, inherited keystore2/hwservicemanager,
   `apexd.config.use_fiemap=false`, retained authenticated ADB, and no duplicate
   KeyMint/Keymaster/default or hardware-keystore feature declaration.
4. Build the real `android.hardware.keymaster@4.0-service`, `keystore2`,
   `hwservicemanager`, `apexd`, `com.android.adbd`, policy/VINTF and the complete
   images using the parent's normal build runner. Use `host_init_verifier` on
   the upstream installed service rc when available. Resolve actual compiler,
   linker/namespace, policy and VINTF errors; the static checks are not waivers.
5. Inspect installed files: `/system/bin/keystore2`,
   `/system_ext/bin/hwservicemanager` (physical system/system_ext here),
   `/vendor/bin/hw/android.hardware.keymaster@4.0-service`, its vendor init rc,
   merged vendor manifest, final generated properties and ADB APEX. Confirm
   `hal_keymaster_default_exec` labeling and one hwbinder 4.0/default instance.
   Check effective package overrides and library availability after graphics
   integration; the existing generic policy is a source basis, not a compiled
   policy result.
6. Construct a separate **test** image only after the external data identity
   and recovery/image-acceptance plan are resolved. Use the scratch fstab in
   both installed locations and verify no active fstab or init script refers
   to stock userdata/cache/FDE metadata for mounting, fsck or formatting. Supply
   an authorized public ADB key through `PRODUCT_ADB_KEYS` if pre-UI ADB is
   required. Never use a private key or disable authentication.
7. Parent decides packaging/flash/testing using its existing acceptance and
   restore gates. This spike does not resolve locked-LK image acceptance or
   any graphics/kernel-hardware issues, and starts no build competing with
   the graphics agent.

## Runtime proof required for the hash → APEX → adbd chain

At the parent-authorized test, collect these in order from the available early
log/recovery channel; lack of adbd is not itself enough to identify the blocker:

1. Confirm `/data` is the verified external ext4 volume, writable with correct
   SELinux labels; `/data/misc/keystore` can support SQLite and persisted keys.
   Confirm stock userdata and encryption metadata remain unmounted/unchanged.
2. Confirm `vendor.keymaster-4-0`, `hwservicemanager` and `keystore2` run without
   a crash loop. HIDL/default must resolve and `getHardwareInfo` must report
   SOFTWARE. Run real key generation and signing/verification with an
   unauthenticated test key; a successful service registration alone is weak
   evidence. Verify the boot-level key cache and expected MaxUsesPerBoot path.
3. Confirm bootstrap APEX mounts, normal APEX activation and real
   `apexservice.getActivePackages()` results. Observe `apexd.status=activated`
   and keystore's module-list/hash/version-skip logs. Expect the platform's
   legacy-version skip message, followed by its own
   `keystore.module_hash.sent=true`; never force either property.
4. Confirm final `perform_apex_config` parses APEX rc files, generates linker
   configuration, marks the default namespace ready and starts delayed
   updatable services. This is the source-confirmed point that can release the
   ADB APEX service. `activated`, keystore completion, and later APEX `ready`
   are distinct milestones. The normal `init_user0`, odsign and snapshotde
   sequence must also finish; investigate their real errors if it does not.
5. Confirm adbd opens FunctionFS, `sys.usb.ffs.ready=1`, the existing configfs
   action binds the UDC and the host enumerates/authenticates. Blank data
   without an embedded authorized public key can legitimately remain
   `unauthorized`. After reaching ADB, save init/keystore/apexd/vold logs and
   actual mounts, service listings, properties and AVC denials before claiming
   this dependency is cleared at runtime.

Expected source-level outcome: this configuration **can advance** through the
unchanged module-information gate using real software cryptography, without
a modern TEE or persistent metadata for initial built-in APEX activation.
Unproved next tests are the integrated build/manifest/policy, verified external
data mount, real crypto operation, APEX activation and authenticated USB on
the actual tablet. Staged updates, credential-backed lockscreen and the final
persistent internal-data migration remain separate unfinished capabilities.

## Offline validation

Run `python3 -B scripts/validate.py` from this spike (or use its absolute path).
`evidence/validation.json` records all 25 checks and staged-file hashes. Checks
include source hashes, exact inherited module/API-level basis, existing service
construction, default policy label matching, XML parsing, real local GNU Make
evaluation of additions, compatibility/security-level behavior, unchanged hash
wait ordering, supported APEX-mode control, missing-session behavior, scratch
fstab structure and absence of readiness/crypto/hardware-feature spoofing.

These are offline source/configuration checks. They do not execute Android's
init parser, Kati/Soong, Rust/C++, SELinux compilation, assembled VINTF checking,
cryptographic operations, filesystem mounts, APEX activation or a device boot.
