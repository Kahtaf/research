# Stock framework clearBcb qualification

**The exact OEM framework API is qualified offline:** service `recovery`, interface `android.os.IRecoverySystem`, transaction **3**, method `clearBcb()Z`, synchronous flags **0**, **no method arguments**. The intended parent-only CLI invocation is `/system/bin/service call recovery 3`. This is established from the OEM Stub's static field and dispatch branch and independently from its compiled Proxy, not inferred from generic AIDL numbering.

The stock framework checks `android.permission.RECOVERY`; its exact permission chain grants UID 0. The saved actual stock policy permits shell-domain Binder access to this service and permits system_server's `ctl_default_prop` control request and connection to uncrypt. No policy, enforcing, domain, service definition, daemon launcher, or socket client change is needed or proposed.

**This is not execution approval or a live success claim.** No device, ADB, root, Binder, actual IPC, raw private capture, metadata write, reboot or flash action occurred. The user is away; presence is not assumed. Parent must pin the live descriptor/selected artifacts and perform a new review before any invocation.

## Starting state: the prior attempt is closed

The first item read was the parent's `clear-attempt-reconciled.json`, timestamp 2026-11-06T21:19:40Z. It states that the one **direct** service-control attempt was denied by init userspace SELinux, before a daemon/client ran; quiescence, two complete unchanged p12 postimages, and staging cleanup were verified. The actual denial was `shell → ctl_default_prop : property_service set`, enforcing. Empty init properties were not evidence of an unregistered service. No new clear attempt occurred here.

Parent receipts also establish: the live 2187-byte fstab matched SHA256 `9f22f786ac2fdbaa10d0d40a7f2a962a3c7008cd22c8c54d4c4454232a6bf46c`; replacing `[0,1088)` with zeros in both fresh captures predicted the exact original full hash; the failed direct attempt left both full postimages at current `8d0cf5c87bcb4abe769f7e4dc2000d45827980b6c12fb792af7bbd0d195c0ef9`. Only aggregate receipts were read/copied, never their private capture paths.

## Binary provenance and extraction boundaries

Source is the existing verified public stock `system.img`, 3,753,902,080 bytes, whole SHA256 **from its prior verified receipt** `4597a7b5a9f30f9e851f1ae71b54a2db1845465e36a1a55b70ae26e171d5cd49`. It was not rehashed or copied. Selected ext4 ranges are recorded in `evidence/extraction.json`.

| Selected public artifact | Bytes | SHA256 |
|---|---:|---|
| `/system/framework/arm64/boot-framework.oat` | 44,179,040 | `d49759f44b5551e3d67516302d54a4eb1d0feb5cda6b7ea6162cae5ca0955e4a` |
| `/system/framework/oat/arm64/services.odex` | 31,552,208 | `51f174af43fbb4bbe4c7532bf89970fb8c0eae08c17fa986150f42258e0b2e8a` |
| `/system/framework/framework.jar` and `services.jar`, each | 126 | `b1ef53afdff586b10b42284b31d550c73cbe95f2be660b03a4e24b6c6e7bf6c9` |

Both JARs are resource placeholders. OAT079 directory records explicitly identify `/system/framework/framework.jar`, its `classes2.dex`, and `/system/framework/services.jar`; embedded DEX locations were verified against those records, not just magic scans. Relevant framework DEX starts at OAT file offset **9208**, SHA256 `26c3677cfda772770bc269dc0c4930508ecbc49400ba566f16cbc26bc70f4087`. Services DEX starts at ODEX file offset **6580**, SHA256 `e7041392d883fa24689449a5e1237752e12b0cfc82ee08121077f54a8e14c155`.

The embedded DEX header SHA1/Adler checksums do **not** match recomputation; original OAT location checksums also differ from embedded header checksums. These preoptimized embedded bytes were not repaired or treated as standalone authenticated original JAR DEX. Provenance is the verified stock image, selected-container SHA256, exact OAT directory offsets and extraction byte equality. All 21 selected methods decode without unresolved quickened operands; all branch/payload targets are instruction boundaries. See `dex-extraction.json`, `oat-directory.json`, and `method-pins.json`.

Only public service/property/file label tables were additionally extracted from verified stock BOOT, SHA256 `7bb68511b1ade34d24c3e932da7260e6753fa87270bd8249a7218755a5df3316`. No boot image was copied into this spike. The saved exact binary policy was reused read-only.

## Exact OEM bytecode result

Offsets below are relative to the indicated embedded DEX; listing files include each instruction's raw code units and byte offset. Add the container offset above for its OAT/ODEX position. Names omit common package prefixes for readability.

| Evidence | Code-item offset / code-unit PC | Result |
|---|---|---|
| `IRecoverySystem$Stub` static encoded values | class-data offset `0x9c6a9c` | `DESCRIPTOR="android.os.IRecoverySystem"`; `TRANSACTION_clearBcb=3`; setup=2; uncrypt=1. Full decoded class data is retained. |
| `Stub.onTransact` | framework `0x4e7a18`; switch at PC `0x2`, case 3 → `0x49` | Enforces exact interface, calls `clearBcb()` at `0x4f`, writes no-exception then boolean 0/1. **No Parcel argument reads in this case.** |
| `Stub$Proxy.clearBcb` | framework `0x4e77ec`; PCs `0x10–0x12` | Writes exact interface token; calls `IBinder.transact(3,data,reply,0)` with no method data; reads exception then result int. |
| `BinderService.clearBcb` | services `0x18653c` | Seven code units: supplies false and null to `setupOrClearBcb(false,null)`, returns boolean. |
| `BinderService.setupOrClearBcb` | services `0x186318` | RECOVERY enforcement at PC `0xb`, before any property/socket action. False selects `ctl.start="clear-bcb"` at PCs `0x29–0x2f`. False at `0x47` jumps over length/command/flush to `readInt` at `0x56`. |
| Status/ack | same method, PCs `0x56–0x60` | Reads one network-order int, sends int zero acknowledgement, returns true only for status100; closes input/output/socket through `IoUtils.closeQuietly`. Non100/IOException returns false; no recovery/reset fallback. |
| `connectService` | services `0x186274` | Fixed LocalSocket address `uncrypt`, namespace RESERVED. Up to 30 connection calls, with 1000ms sleeps on IOException; returns after first successful connect. No parent-supplied path. |
| Registration | services `SystemServer.startOtherServices` PC `0x4f8`; `RecoverySystemService.onStart` code `0x18695c` | SystemServer starts this class; onStart publishes its BinderService as `recovery`. `SystemService` passes publication to ServiceManager. |

This OEM IRecoverySystem exposes only uncrypt/setupBcb/clearBcb in its interface; no reboot method was assumed. The selected clear path contains no factory-reset call, reboot call, wipe command, command-file write or command payload. The shared helper does contain the separate setup branch, but false/null deterministically excludes it. No caller identity is cleared or impersonated by this method.

**Timing and concurrency differences matter:** this OEM helper has no busy-service precheck, lock, peer-credential check or socket read timeout. A single API call performs one service-start request, but its stock connect helper may internally retry connection up to 30 times. Once connected, it reads one status and does not reconnect. A transport timeout neither cancels the server-side Binder operation nor proves absence of a write. Parent exclusive ownership and quiescence reconciliation remain mandatory.

## RECOVERY permission and root caller

Exact compiled chain, with no app permission grant assumption:

- `ContextImpl.enforceCallingOrSelfPermission` (`0x2156c8`) calls `checkCallingOrSelfPermission` (`0x214fc8`), which obtains Binder calling PID/UID and passes them to `checkPermission` (`0x2150c0`).
- `ActivityManagerService.checkPermission` (`0x1e7544`) delegates to `checkComponentPermission` (`0x1e6694`) with those PID/UID values, owning UID -1, exported true. An external PID reaches `ActivityManager.checkComponentPermission`.
- That framework method (`0x1da03c`) calls `UserHandle.getAppId` (`0x4fe818`, actual `%100000` bytecode); appId0 or1000 returns **0 = permission granted** before package permission lookup. UID0 therefore takes the built-in root grant.
- `ContextImpl.enforce` (`0x21425c`) returns on grant0; otherwise throws SecurityException before this API starts native work. An ordinary UID2000 is not presumed to hold RECOVERY.

Parent's existing on-demand root supplies UID0 while retaining `u:r:shell:s0`; it does not need to become system_server. Binder invokes the registered framework service in its existing system_server process. Property/socket operations use that process's allowed MAC path, while the Java permission check still evaluates the original Binder caller.

## Actual saved policy and labels

Binary policy SHA256: **`873141c3874066341dcb4e2c7be4eb3f664686635ee3f84d2c4100f557ae740f`**, policy version30. A pinned existing host libsepol probe evaluated permissions; no live policy was read or modified. All queried source domains were nonpermissive. Full results and probe/source hashes: `evidence/policy-queries.json` (32 queries).

| Exact policy query | Result |
|---|---|
| shell → ctl_default_prop, property_service:set | **Denied**, agrees with the parent's actual failed control attempt |
| system_server → ctl_default_prop, property_service:set | **Allowed** |
| shell → recovery_service, service_manager:find | **Allowed** |
| shell → servicemanager and system_server, binder:call | **Allowed** |
| system_server → recovery_service, service_manager:add | **Allowed** |
| system_server → property_socket, sock_file:write; → init, unix_stream_socket:connectto | **Allowed** |
| system_server → uncrypt_socket, sock_file:write; → uncrypt, unix_stream_socket:connectto | **Allowed** |
| system_server self unix_stream_socket create/connect/read/write/getopt | **Allowed** |
| init → uncrypt, process:transition; uncrypt → uncrypt_exec, file:entrypoint | **Allowed** |
| uncrypt → block_device and para_block_device, blk_file:open/write | **Allowed** |

The saved service label table maps `recovery` to `recovery_service`; property longest-prefix matching maps `ctl.clear-bcb` to `ctl_default_prop`. Decoded compiled file labels bind `/dev/socket/uncrypt` to `uncrypt_socket`, `/system/bin/uncrypt` to `uncrypt_exec`, `/dev/binder` to `binder_device`, and the property socket to `property_socket`.

The saved file table has a para-specific rule for a different `/dev/block/platform/soc/.../by-name/para` spelling; the canonical p12 path also has the generic block-device match. Do not invent the live label. Both candidate block types have open/write grants; the parent should record the actual target label without changing it. Diagnostic queries deny uncrypt `getattr` on those block types and deny `read` on misc_block_device. These are **not asserted grants**; the already-qualified clear writer uses open/write/fsync and does not stat or read para.

## Native primitive and verification

The API selects the same pinned OEM daemon (`3f7e8c8ed7272540315eaef0af405a57ac701db121dd5c842a8b04be721b2671`) and stock clear-bcb init service qualified in the separate [native audit](../2026-11-06-asus-exact-oem-clear-bcb-audit/REPORT.md). Its established effect is 1088 zero bytes at offset0 of the live fstab's para/p12 target, then fsync, status and ack; no userdata/p20/cache write or reboot. This spike changes the caller path, not the primitive. Parent independently confirmed that this span predicts the exact old whole hash.

Fourteen tests interpret **original decoded OEM instruction streams** using a narrow, declared Dalvik subset. They cover UID0 success, Proxy wire shape and false result, unprivileged denial, wrong descriptor, descriptor-only transaction, property failure, native failure/unexpected status, read/ack failures, connection retry then success and 30-attempt exhaustion. Native Java/Parcel/property/socket/package-manager operations are explicit in-memory fixtures; no ART, JNI, real Binder or kernel execution is claimed. Root permission arithmetic, server dispatch, shared false/null branch and return/exception control flow are executed by this interpreter. Tests used one sequential worker, a 45-second CPU budget, roughly 61MB measured peak RSS, and no new packages or compilation jobs.

A separate static cross-check agrees across field value, switch, Proxy and server wrapper. No competing Ninja/build job was started; existing native jobs and sealed artifacts were left untouched.

Format references, not OEM behavior substitutes: [Android 7 ART instruction definitions](https://android.googlesource.com/platform/art/+/android-7.0.0_r1/runtime/dex_instruction_list.h), [OAT reader](https://android.googlesource.com/platform/art/+/android-7.0.0_r1/runtime/oat_file.cc), and [libselinux label format](https://android.googlesource.com/platform/external/selinux/+/android-7.0.0_r1/libselinux/src/label_file.c). The [Android 7 service CLI source](https://android.googlesource.com/platform/frameworks/native/+/android-7.0.0_r1/cmds/service/service.cpp) supplies CLI syntax/token conventions only; the stock service executable itself was not extracted or independently disassembled. Actual API number, descriptor and argument shape come from OEM bytecode.

The remaining gates are live identity/descriptor, fresh preimage/prediction, parent review and one-shot reconciliation—not an unresolved static API number or an assumed system_server MAC grant. See [PARENT-PROCEDURE.md](PARENT-PROCEDURE.md).
