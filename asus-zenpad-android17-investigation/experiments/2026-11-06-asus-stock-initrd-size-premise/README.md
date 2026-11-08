# Stock initrd size premise

Question: did the failed exact 5a61 stock-kernel rescue retain the appended
stock FDT's static 2 MiB initrd limit, truncating its larger ramdisk?

Status: complete. The retained-static-2-MiB mechanism is refuted on the exact
LK's successful recovery handoff path. The cause of physical failure remains
inconclusive because runtime handoff/bounds are unobserved. No candidate build
or frozen-byte change.

Outputs: `REPORT.md` (conclusion and next action), `evidence/audit.json`
(exact artifact and stream facts), `evidence/kernel.disasm`,
`evidence/lk-excerpts.disasm`, `evidence/source-excerpts.txt`, and input pins.

Continue with the report. Reproduce only the read-only inspector with the
existing audit interpreter:

```sh
2026-11-05-asus-boot-access-audit/.venv/bin/python -B 2026-11-06-asus-stock-initrd-size-premise/scripts/audit.py
```

Scope: existing public Mac inputs only, no children, device/ADB/root, VM,
network, cloud lifecycle, native process inventory, source writes, target build,
candidate image, or active parent output. All new output stays here, <1 MiB.
