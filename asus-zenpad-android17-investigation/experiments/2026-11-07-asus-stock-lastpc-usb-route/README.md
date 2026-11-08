# ASUS stock LASTPC USB route

Question: Does stock `/sys/bus/platform/drivers/lastpc/lastpc_dump` provide a useful previous-reset diagnostic after the failed Linux 4.9 recovery trial, and is an existing cached interface preferable?

Status: Complete, bounded local source/binary qualification on 2026-11-07. No device access, private inputs/logs/calibration, network fetch, process/cloud/AOSP changes, tests, builds, image generation, flashing, or reboot. Only this spike was created/written. No children were spawned.

Important outputs:

- [HANDOFF.md](HANDOFF.md): conclusion, limitations, and one next action for the parent.
- [evidence/source-pins.json](evidence/source-pins.json): exact SHA-256 pins, paths, and source provenance.
- [source/excerpts.txt](source/excerpts.txt): relevant source with original line numbers.
- [evidence/stock-lastpc.json](evidence/stock-lastpc.json) and [stock-lastpc.disasm](evidence/stock-lastpc.disasm): public original stock binary corroboration, selected function pins, compiled DT, and callback table evidence.
- [scripts/inspect_public_stock.py](scripts/inspect_public_stock.py): reproducible offline inspection; reads only the named public artifact and existing parser source, writes evidence only here. Run with the existing boot-access-audit `.venv/bin/python -B`; it does not build or emit an image.

Continuation: Parent may perform the single cached report read described in HANDOFF.md using its established USB collection path. Preserve raw numeric PCs and capture provenance. No new reboot or flash is supported by this investigation. Any absent/zero output is inconclusive about Linux 4.9 execution.
