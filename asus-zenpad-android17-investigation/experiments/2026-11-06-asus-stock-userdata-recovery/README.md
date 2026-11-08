# Stock userdata recovery after Android 17

Question: How can original Android 7 be deliberately restored after clean Android 17 p26 provisioning, while discarding userdata and preserving factory calibration?

**Status: offline study complete; physical stock-data recovery remains pending (R3).** Recommended candidate: exact original SYSTEM → BOOT → separately restored original recovery → supervised OEM factory reset → stock FDE/data startup and reboot persistence. p20 stays unchanged until OEM reset, which intentionally targets its entire 32 MiB. Bitwise p20 preservation across that reset is incompatible with this route.

Important outputs:

- [REPORT.md](REPORT.md): exact firmware evidence, write scope, ordered contract and smallest physical tests.
- [HANDOFF.json](HANDOFF.json): parent integration status and unresolved gates.
- [Machine-code execution](evidence/emulation.json): **12/12 pass**, original AArch64 slices with all I/O mocked; no physical execution.
- [Static checks](evidence/static-checks.json), [filesystem checks](evidence/filesystem.json), [offline run](evidence/checks.json).
- [Public parent preservation receipt](inputs/parent-preservation-acceptance.json): adopted; private payloads never accessed; restoration remains untested.

Key findings: recovery's data format requests whole-p20 discard; its completion message can still appear after failed erase calls. Both wipe hooks are exact no-ops. Optional `/nvdata` is absent from captured fstab. Actual stock formatter masks are `0x1c / 0x42 / 0x13`; filesystem flags alone do not prove FDE or stock boot. Original rescue roles 0/1 restore neither p26 nor p10. Its inability to restore p10 must be solved by an existing qualified parent path that does not depend on working stock userdata.

Reproduce offline, sequentially:

```sh
.venv/bin/python -B source/run_checks.py
```

Dependencies are pinned in `requirements.txt`; the isolated `.venv` already contains them. This reads only selected firmware files, compares small BOOT/recovery backups, and executes bounded emulator fixtures. It never rehashes/copies full SYSTEM, creates a data image, starts a build, or accesses any device/cloud. The optional `source/fetch_references.py` fetches public AOSP7 references; it is not part of offline checks.

Continuation: parent establishes original recovery entry/cancel/log visibility and a p10 restore path independent of stock userdata, then owns the physical reset and two-boot crypto/persistence acceptance. The completed factory preservation receipt is accepted as supplied; do not reopen private payloads for this research. No new writer, policy exception, arming, or five-role GO is supplied. Preserve all earlier artifacts and nested repositories.
