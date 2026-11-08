# Stock framework clearBcb qualification

Question: does the exact ASUS Android 7 compiled framework expose a permission-checked recovery clearBcb Binder API using system_server's permitted service-control path and the unchanged OEM 1088-byte clear primitive?

Status: **offline API qualification complete**. OEM Stub, Proxy and service bytecode prove service `recovery`, descriptor `android.os.IRecoverySystem`, transaction **3**, synchronous flags0, no method arguments. Exact OEM permission code grants caller UID0; saved actual stock policy permits the Binder/system_server control/socket path. Parent runtime identity/descriptor, fresh whole-preimage, review and reconciliation gates remain. No execution approval.

The preceding direct shell control attempt was denied by SELinux before any client ran. Parent proved quiescence and two full unchanged p12 postimages and cleaned staging. This spike qualifies the standard framework API as a distinct approach; it does not retry or relaunch that attempt.

No device/ADB/root/Binder/actual IPC, private-unit read, metadata write, policy/context/security change, reboot or flash operation occurred here. No subagents, installs, Ninja or active source/kernel/sealed-artifact changes. User presence is not assumed.

Important outputs:

- [REPORT.md](REPORT.md): exact OEM method offsets, pins, permission chain, policy results and limitations.
- [PARENT-PROCEDURE.md](PARENT-PROCEDURE.md): concrete parent-only API invocation and one-shot/full-readback contract.
- [HANDOFF.json](HANDOFF.json): machine-readable result and remaining parent gates.
- `inputs/`: only selected public framework JAR/OAT/ODEX, embedded DEX, stock label tables and saved stock binary policy. No whole SYSTEM copy.
- `evidence/decoded-methods.json`, individual method listings, `method-pins.json`: 21 targeted OEM methods with code-unit boundaries and byte hashes; registration excerpt separately.
- `evidence/policy-queries.json`: 32 read-only queries of exact policy `873141c3…740f`, including actual shell denial and system_server grant.
- `evidence/bytecode-tests.json`: 14 narrow actual-bytecode interpretation cases; no ART/Binder/kernel execution. Peak RSS about61MB, one sequential worker.
- `evidence/extraction.json`, `oat-directory.json`, `dex-extraction.json`: verified source receipt, selected image ranges and embedded-Dex provenance. Internal embedded DEX header checksums are not treated as authentication; container SHA256 and exact extraction are the pins.

Continuation: parent reads procedure, verifies live descriptor/selected artifacts and fresh before/predicted-after hashes, then performs its own new review. Only one parent invocation is allowed; stock framework's internal 30 connection attempts are documented, and its status read has no deadline. Do not retry on timeout or false. Parent independently obtains two full postimages after quiescence.

Reproduce analysis/tests using existing read-only environment from workspace root (no install, one command at a time):

```
PYTHONDONTWRITEBYTECODE=1 2026-11-06-asus-stock-userdata-recovery/.venv/bin/python 2026-11-06-asus-framework-clear-bcb-api/source/disasm_dex.py
PYTHONDONTWRITEBYTECODE=1 2026-11-06-asus-stock-userdata-recovery/.venv/bin/python 2026-11-06-asus-framework-clear-bcb-api/source/inspect_formats.py
PYTHONDONTWRITEBYTECODE=1 2026-11-06-asus-stock-userdata-recovery/.venv/bin/python 2026-11-06-asus-framework-clear-bcb-api/source/query_policy.py
PYTHONDONTWRITEBYTECODE=1 2026-11-06-asus-stock-userdata-recovery/.venv/bin/python 2026-11-06-asus-framework-clear-bcb-api/source/test_bytecode.py
PYTHONDONTWRITEBYTECODE=1 2026-11-06-asus-stock-userdata-recovery/.venv/bin/python 2026-11-06-asus-framework-clear-bcb-api/source/qualify.py
```

`extract_framework.py` and `extract_dex.py` reproduce only selected public extraction; the existing source image is trusted through its prior verified READY receipt, never rehashed in full. `extract_boot_labels.py` selects only the three public label tables from verified stock BOOT. Query tooling reuses the pinned existing host `policy_probe`, whose binary and source hashes are recorded. Generic AOSP files here document formats/CLI conventions only; actual OEM bytecode decides the API.
