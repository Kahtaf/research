# Recovery-only control over authenticated Wi-Fi

Question: can the reviewed stock-kernel diagnostic and exact stock inverse use the already authorized Wi-Fi ADB transport, avoiding the tablet's unreliable USB port for image transfer?

Status: offline adaptation; hardware execution pending. No device operation performed by this spike. The original USB transport, root helpers, backups and reviewed diagnostic are unchanged.

The fixed endpoint is IP_REDACTED:5555. Hardware serial DEVICE_SERIAL_REDACTED remains separately required through ro.serialno; secure ADB, exact stock fingerprint, SDK, boot completion and Enforcing are mandatory. The pinned Wi-Fi root helper retains its own identity, UID/status and SELinux restoration checks. No endpoint discovery or override exists.

Only recovery /dev/block/mmcblk0p10 is writable. Existing geometry, exact stock-kernel candidate profile, manifest pin, bounded writes, staged-byte readback, full partition verification, one guarded stock inverse and stop-on-uncertain-transport behavior are unchanged. No retries were added. A separate fixed staging directory prevents reuse of old sessions; the original USB writer's host advisory lock is shared. Parent must exclude all other device operations.

Important outputs: source/recovery_control.py, evidence/adapter.diff, source-review.json and offline test results. Original scope and implementation review: ../2026-11-06-asus-recovery-control-transport/REVIEW-REPORT.md. This adapter does not establish first 4.9-kernel readiness; its profile intentionally accepts only the exact stock kernel.

Continuation: run offline tests and verify-local, review the adapter diff and existing parent diagnostic manifest, then execute only when the backup has ended and a supervised physical recovery test is ready. Do not reboot or select recovery from this tool. Once stock returns, restore and verify recovery; automatic stock repair may make a block write unnecessary. Wi-Fi ADB may need re-enabling through USB after stock restarts.

```sh
PYTHONDONTWRITEBYTECODE=1 python3 tests/test_recovery_control.py
python3 source/recovery_control.py verify-local
python3 source/recovery_control.py restore
```

The default is PLAN ONLY. Explicit --execute --supervised is required for any device contact. An interrupted operation leaves staging and evidence intact and must be assessed before further commands.
