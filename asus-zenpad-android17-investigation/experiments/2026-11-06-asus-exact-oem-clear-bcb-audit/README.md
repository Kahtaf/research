# Exact OEM clear-BCB audit

Question: can ASUS WW_P00A-V5.3.20-20180809's stock clear-bcb service remove the pending recovery request and reproduce the exact original whole-para hash?

Status: offline binary audit and fixed client complete. **Parent gates remain: candidate postimage and live fstab/path identity, then parent review.** No device operations, real sockets, raw unit reads, metadata writes, root changes, service starts, reboot, flash, or execution approval by this research task.

Important outputs:

- [PARENT-PROCEDURE.md](PARENT-PROCEDURE.md): concrete gated one-shot invocation and all-outcome readback contract.
- [REPORT.md](REPORT.md): exact 1088-byte write span, dispatch/alias/IPC evidence, provenance and limits.
- [EARLY-HANDOFF.md](EARLY-HANDOFF.md): original narrow milestone delivered before final report; later full-parser evidence is in REPORT.md.
- `artifacts/clear-bcb-client`: static ARM64 ELF, 3240 bytes, SHA256 `ea4f875e95f6c0b331edbad1817a60b7ce3d8a988516db8ec247ecf801f29630`. **Never run on host/device as part of offline reproduction.**
- `source/clear_bcb_client.c`, `evidence/client-build.json`, `evidence/client-tests.json`: build and 44 compiled-ELF virtual UNIX-socket fixture tests.
- `evidence/oem-emulation.json`: 16 original-instruction cases, including real embedded OEM fstab parser. No real external effects.
- `source/predict_postimage.py`: parent-only pure in-memory postimage calculation; no file reads/writes.
- `source/oem/`, `evidence/input-pins.json`, `evidence/uncrypt-annotated.txt`: copied public software, provenance and instruction-boundary evidence.

Continuation: parent reads the report/procedure, retains exclusive device ownership, privately proves `sha256(bytes(1088)+fresh_current[1088:])` equals original `8c9e2c158ac95f152d08ea9de929ae36d054131ca4b10620890974ed831480ef`, verifies live identity, and performs its own approval review. Do not reuse the earlier diagnostic staging or approval. No generic Binder transaction number is established.

Offline reproduction from this workspace root (one process at a time; existing venv read-only, no installs):

```
PYTHONDONTWRITEBYTECODE=1 2026-11-06-asus-stock-userdata-recovery/.venv/bin/python 2026-11-06-asus-exact-oem-clear-bcb-audit/source/inspect_oem.py
PYTHONDONTWRITEBYTECODE=1 2026-11-06-asus-stock-userdata-recovery/.venv/bin/python 2026-11-06-asus-exact-oem-clear-bcb-audit/source/emulate_oem.py
PYTHONDONTWRITEBYTECODE=1 2026-11-06-asus-stock-userdata-recovery/.venv/bin/python 2026-11-06-asus-exact-oem-clear-bcb-audit/source/build_client.py
PYTHONDONTWRITEBYTECODE=1 2026-11-06-asus-stock-userdata-recovery/.venv/bin/python 2026-11-06-asus-exact-oem-clear-bcb-audit/source/test_client.py
```

These scripts analyze public files or execute instructions only inside Unicorn with explicit stubs. They never invoke the produced ELF as a host process. The client itself is a real IPC executable for the parent's separately reviewed use; do not execute it during offline testing.
