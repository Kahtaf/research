# Parent-only stock framework clear procedure

This is a new, separately reviewed API operation. It is **not** a retry of the denied shell control request and does not reuse its approval or staging. Research has performed no device/IPC operation and grants no execution approval. The user is away; do not assume a supervised window.

## Proven API shape

- Registered service: `recovery`.
- Interface descriptor: `android.os.IRecoverySystem`.
- Method: `clearBcb()Z`.
- Transaction: **3**, synchronous flags **0**.
- Request: interface token only, **no method arguments**. Do not append `i32`, `s16`, a command string, or a reset option.
- Reply: no-exception marker followed by boolean int (1/0). Binder transaction handled, shell exit0, or daemon exit is not proof of successful whole-partition restoration.
- Administrative caller: UID0 through the already reviewed on-demand root helper, retaining its ordinary shell context. No manual context switch or permission/policy modification.

Actual OEM field, Stub, Proxy, permission and server bytecode evidence is in REPORT.md. The saved policy allows this ordinary Binder/API route and system_server's control request; it denies the earlier direct shell control path.

## Read-only gates, owned and executed only by parent

1. Hold exclusive device-operation ownership. Confirm no pending recovery/update caller, no setup-bcb/uncrypt/clear-bcb process or socket, and that the previous failed attempt is fully reconciled. Empty init properties alone do not mean the service is absent. Keep existing debloat state; no new package/security changes.
2. Confirm exact stock fingerprint `asus/WW_P00A/P00A_2:7.0/NRD90M/WW_P00A-V5.3.20-20180809:user/release-keys`. Pin live selected artifacts against:
   - `/system/framework/arm64/boot-framework.oat`: 44179040 bytes, SHA256 `d49759f44b5551e3d67516302d54a4eb1d0feb5cda6b7ea6162cae5ca0955e4a`.
   - `/system/framework/oat/arm64/services.odex`: 31552208 bytes, SHA256 `51f174af43fbb4bbe4c7532bf89970fb8c0eae08c17fa986150f42258e0b2e8a`.
   - Native uncrypt: `3f7e8c8ed7272540315eaef0af405a57ac701db121dd5c842a8b04be721b2671`; uncrypt.rc: `63b33e2a2271d0c598bca842d0e6b03564004ed1e0e2995e8dd8ed5616455e82`.
   No whole-SYSTEM hash/copy is needed. If current running framework/policy identity differs or is uncertain, stop; do not extend this proof to it.
3. **Pin the live descriptor before the mutating transaction.** Parent may use the read-only interface transaction, whose separate OEM onTransact case was decoded/tested:

   ```
   /system/bin/service call recovery 1598968902
   ```

   Require the returned descriptor to be exactly `android.os.IRecoverySystem`. A parent-owned `service list` result showing that exact service/descriptor can also supply this gate. Existing `service check recovery` establishes existence, not descriptor identity. Do not use transaction3 as a probe. Descriptor mismatch/permission denial blocks execution; no guessed alternatives.
4. Confirm `ro.hardware=mt8163`, the exact 2187-byte `/fstab.mt8163` SHA256 `9f22f786ac2fdbaa10d0d40a7f2a962a3c7008cd22c8c54d4c4454232a6bf46c`, and `/misc` → existing para alias → `/dev/block/mmcblk0p12`. Retain the reader's 179:12, partition12, start225576, 1024×512-byte geometry guards. Record actual target label without changing it. Saved policy allows open/write for both generic block_device and para_block_device; any other live label needs a separate exact query before action.
5. With the independent exact whole-p12 reader, obtain two fresh matching 524288-byte preimages, SHA256 **`8d0cf5c87bcb4abe769f7e4dc2000d45827980b6c12fb792af7bbd0d195c0ef9`**. Privately recompute `sha256(bytes(1088)+current[1088:])`; require **`8c9e2c158ac95f152d08ea9de929ae36d054131ca4b10620890974ed831480ef`**. Prior receipts demonstrate this prediction but are not a waiver of freshness after the user returns. Do not send raw captures to this research task.
6. Parent records a new review/approval and an attempt marker binding these identities, hashes, descriptor, transaction3/no-arguments, timestamp and reconciliation contract. If a clear request may have been submitted, a controller restart must preserve uncertainty rather than replay it.

## Single invocation, after parent review

Under that existing reviewed on-demand root mechanism, parent invokes exactly once:

```
/system/bin/service call recovery 3
```

Do not run `setprop ctl.start clear-bcb` from shell, run the prior IPC client, launch uncrypt manually, change policy/enforcing/context, add setup/reset arguments, or write p12 directly. The existing API performs its own permitted system_server control request and native socket handshake.

The framework sends `ctl.start=clear-bcb` once. Its stock connect helper can internally attempt connection up to 30 times, sleeping 1 second after IOException. These are part of one OEM API invocation, not authorization for a parent retry. It transmits no command bytes, reads one status int, acknowledges with int0, and returns true only for status100.

There is **no socket status-read deadline**, no peer-credential validation and no mutual-exclusion/busy-service guard in this OEM helper. Parent should impose a bounded observation window appropriate to the supervised session (at least the 30-second stock connection phase, e.g. 60 seconds), while treating a timeout as **UNKNOWN**. Killing the shell `service` command or losing transport does not cancel an executing system_server Binder call, a pending init request or a native write. Do not issue another call to find out.

## All-outcome reconciliation

Expected simple Parcel words are `(00000000 00000001)` for no-exception/true or `(00000000 00000000)` for no-exception/false. Preserve complete stdout/stderr and transport exit status. An exception, extra/unrecognized header, truncated Parcel, missing response, timeout or differing descriptor is not success. Do not accept only a success-looking substring or CLI exit code.

- **True:** native clear/status/ack path reported success. Still require independent full readback.
- **False:** may mean connection failure, native failure, unexpected status, or IOException. Some occur after all 1088 bytes were written. Never retry automatically.
- **SecurityException/property exception:** preserve evidence of where it failed. Do not grant permissions/change policy or fall back to direct shell control. Reconcile actual quiescence and bytes.
- **Unknown transport/result:** assume a possibly live framework/native operation. No retry, reboot, flash, reset or diagnostic continuation.

Before authoritative post-readback, parent establishes that the API call completed or is no longer pending and the native operation is quiescent. No current process/socket alone is insufficient if a timed-out Binder call may still be in its stock connection loop or init work remains pending. If terminal state cannot be established, leave the gate blocked for parent-led diagnosis; this task supplies no cancellation/bypass route.

After quiescence, parent captures **two independent full 524288-byte postimages** with the same alias/geometry guards:

- Both equal **`8c9e2c158ac95f152d08ea9de929ae36d054131ca4b10620890974ed831480ef`**: intended complete byte restoration is established. Record it and reconcile any API/transport anomaly before deciding diagnostic continuation.
- Both remain **`8d0cf5c87bcb4abe769f7e4dc2000d45827980b6c12fb792af7bbd0d195c0ef9`**: request remains uncleared. Stop; a different action requires separate qualification/review, not replay.
- Any other hash, unstable pair, failed read, live operation or identity mismatch: stop and preserve evidence. No raw restoration or custom writer.

Only parent may resume the original stock diagnostic, under its own fresh preflight and approval. This API neither reboots nor constitutes diagnostic-entry approval.
