# Parent-only one-shot clear procedure

**Do not execute from this research task.** This document is a concrete review packet, not permission. Only the parent operates the device, chooses the supervised window, and obtains/records applicable approval. The prior diagnostic run `2026-11-06-asus-stock-helper-dispatch-fix/evidence/service/runs/20261106T204650Z-ad05ad12f954e3de` and its staging/approval are not reused.

The clear writes 1,088 zero bytes at para offset 0. It starts on **socket accept**, not on receipt of a command or acknowledgement. Starting the service leaves it waiting for a connection; do not probe-connect to test it. Once a client may have connected, every subsequent error is a possibly-completed write, not permission to retry.

## 1. Close the remaining read-only gates

Parent holds the existing exclusive device-operation lock and ensures no other actor will request recovery, uncrypt, setup-bcb or clear-bcb. Parent confirms normal stock Android and user nearby. The ASUS dmOTA disabled-user/process-absent finding is retained as parent evidence; Google remains enabled. Research changes no packages.

Record all of the following in a new purpose-specific receipt:

- Current stock fingerprint `asus/WW_P00A/P00A_2:7.0/NRD90M/WW_P00A-V5.3.20-20180809:user/release-keys`; `ro.hardware=mt8163`.
- Fresh `/system/bin/uncrypt`: 68,752 bytes, SHA256 `3f7e8c8ed7272540315eaef0af405a57ac701db121dd5c842a8b04be721b2671`.
- Fresh `/system/etc/init/uncrypt.rc`: 390 bytes, SHA256 `63b33e2a2271d0c598bca842d0e6b03564004ed1e0e2995e8dd8ed5616455e82`. Exact service is `/system/bin/uncrypt --clear-bcb`, disabled and oneshot, socket `uncrypt stream 600 system system`.
- Actual `/fstab.mt8163`: 2,187 bytes, SHA256 `9f22f786ac2fdbaa10d0d40a7f2a962a3c7008cd22c8c54d4c4454232a6bf46c`. It has the single `/misc` entry to `/dev/block/platform/mtk-msdc.0/11230000.MSDC0/by-name/para`; no slotselect. Stop on any different live file or path, even if another mapping looks plausible.
- Para resolves to `/dev/block/mmcblk0p12`, major/minor 179:12, partition 12, start 225576, size 1024 logical 512-byte sectors = 524288 bytes. Parent's reviewed `source/read_para.py` already guards these identities; do not infer them from this offline study.
- `init.svc.clear-bcb`, `init.svc.setup-bcb`, `init.svc.uncrypt` stopped; no matching daemon process and no active recovery/update caller. No stale `/dev/socket/uncrypt` endpoint. Do not remove unexpected paths to force the gate to pass.
- Parent's two fresh independent whole-para captures match each other and exact current hash `8d0cf5c87bcb4abe769f7e4dc2000d45827980b6c12fb792af7bbd0d195c0ef9`. The existing public receipt `before-capture-ac7cd9c04571db33.json` reports this; determine freshness under the same exclusive operation window.
- Compute candidate postimage privately **without writing any file back to the device**: `sha256(bytes(1088) + fresh_current[1088:])`. Require exact original hash `8c9e2c158ac95f152d08ea9de929ae36d054131ca4b10620890974ed831480ef`. The pure `source/predict_postimage.py::predict(current)` returns only hashes and aggregate match status. It provides no execution permission. **Any mismatch blocks clear.** Do not send the raw capture to the research agent.

A matching candidate establishes that zeroing the additional 1,068 bytes beyond the changed twenty bytes does not destroy other original content. The aggregate twenty-byte diff by itself does not establish this.

## 2. Prepare a distinct, reviewable attempt

Parent stages `artifacts/clear-bcb-client` in a new parent-controlled, purpose-specific location with appropriate ordinary permissions and verifies its on-device length/hash. Expected: **3240 bytes**, SHA256 **`ea4f875e95f6c0b331edbad1817a60b7ce3d8a988516db8ec247ecf801f29630`**. Retain local source/build/test evidence hashes. No prior diagnostic helper path is reused.

The client takes exactly one decimal daemon PID, 2 through 4194304; it has no socket/path/command/partition argument. Do not add shell wrappers that retry. It does not use Binder, start services, write properties, modify security policy, open block devices, or issue reboot.

Parent reviews this exact span, identity evidence, client, and outcome rules and records approval for this specific metadata-clear attempt. Before the first start request, record an irrevocable attempt marker with all pins, current/candidate hashes, timestamps, and the explicit no-retry rule. A controller crash must leave an uncertain attempt, not an invitation to launch again.

If the supervised window has expired, leave the attempt unexecuted. The time window does not waive any gate.

## 3. Invoke the smallest stock mechanism once

Only after the above review, parent uses its existing on-demand root mechanism to issue this single service-start request:

```
setprop ctl.start clear-bcb
```

Do not call `uncrypt` directly, use `--setup-bcb`, send a wipe command, use an assumed Binder transaction number, or change the service definition/security properties.

Within a bounded parent wait (suggested 5 seconds), observe `init.svc.clear-bcb=running` and the known socket. Inspect the unique daemon PID and exact NUL-separated cmdline `/system/bin/uncrypt\0--clear-bcb\0`; verify executable identity against the pinned uncrypt. Recheck competing service states and ordinary `/dev/socket` directory identity. Do not connect as a probe.

The socket must be a nonsymlink UNIX socket owned system:system (1000:1000), mode 0600. Parent obtains the verified **daemon PID**, not init PID 1. The source reference's Linux `listen()` initializes the server credentials to the calling daemon, and the OEM binary calls listen itself.

Parent invokes the pinned client **once**, under the authorized context able to access this socket:

```
<fresh-parent-staging-path>/clear-bcb-client <verified-clear-bcb-daemon-PID>
```

These angle-bracket values are parent-resolved placeholders, not literal shell input. The socket endpoint inside the client is always `/dev/socket/uncrypt`. The client checks socket inode/owner/mode before and after connect, SO_PEERCRED (that PID, uid0, gid0), and exact peer path. **Checks after connect detect discrepancies but cannot prevent an already-triggered OEM write.** Parent preconnect identity checks therefore matter.

Client protocol: no request bytes; read exactly four network-order status bytes; accept only 100 or -1; send exactly four zero acknowledgement bytes; require peer EOF; close. One connect call only. Connect stage 5s, status 10s, ack 2s, peer close 2s, bounded EINTR loops. Parent should also bound its transport wait (e.g. 30s) and preserve uncertain results without retrying.

The OEM's own write/read loops and fsync have no finite deadline. Client timeout/disconnection does **not** cancel or roll back a write already in progress. A daemon may still be blocked in the kernel after the client exits. Do not reboot to resolve this uncertainty.

## 4. Reconcile every outcome independently

Parent records service start result, observed PID/executable/cmdline, client result, service/process state and timestamps. Do not infer completion from `setprop` returning or daemon process exit alone.

| Client result | Meaning | Required next step |
|---|---|---|
| 0 | Received OEM100, sent ack0, peer EOF, client close succeeded | Full independent whole-para readback still mandatory. |
| 20 | Received OEM-1, sent ack0, peer EOF | Write may be absent, partial or complete (e.g. fsync failure). Stop and reconcile; never retry. |
| 21 / 22 | Missing/short/failed status, or unexpected status | Possibly completed write; close and reconcile. |
| 23 / 24 / 25 | Ack failure, missing/unexpected peer termination, or client close failure | Possibly completed write; reconcile. |
| 90 / 91 / 92 / 93 | Argument, socket metadata, socket creation, or initial clock failure before connect | This client has not connected, but service/other-client state must still be reconciled. No new invocation under this attempt. |
| 94 | Connect failed or indeterminate / connect deadline / SO_ERROR | No automatic retry; verify daemon state and capture. |
| 95 / 96 / 97 | Socket identity changed, peer credentials differ, or peer path differs after connect | Mutation may already have happened. Stop; preserve evidence and full readback. |
| Transport timeout, killed process, missing exit status | Unknown | Treat as uncertain write; no retry or diagnostic continuation. |

First establish that the same clear-bcb daemon is gone and init reports stopped. If still waiting at accept after a known preconnect failure, parent may review a stop of that exact service as a separate reconciliation action; do not create a second client merely to release it. If a write may be in flight, stopping a process or a transport timeout is not proof that kernel I/O has ceased. If quiescence cannot be established, the gate remains blocked.

After quiescence, parent uses its independently reviewed whole-para reader to capture two fresh full 524288-byte reads, with p12/alias/geometry guards. Do not substitute the client's success status, a short BCB read, or a raw restore. Reconcile:

- **Both hashes equal old required `8c9e2c158ac95f152d08ea9de929ae36d054131ca4b10620890974ed831480ef`:** intended entire-partition byte restoration is proven. Record postimage evidence. Any IPC/fsync anomaly remains an explicit reconciliation finding; review it before deciding diagnostic continuation.
- **Both hashes remain current `8d0cf5c87bcb4abe769f7e4dc2000d45827980b6c12fb792af7bbd0d195c0ef9`:** pending request remains; stop. Do not silently repeat the clear.
- **Hashes differ from each other or either expected image, read fails, daemon remains active, or identity differs:** stop, preserve all evidence, no further metadata writes, reboot, flash, or diagnostic entry.

Only the parent, after independent full readback and separate diagnostic preflight review, decides whether the original supervised diagnostic may continue. Cleanup of the new client staging is parent-owned after evidence preservation; cleanup is not another clear attempt.
