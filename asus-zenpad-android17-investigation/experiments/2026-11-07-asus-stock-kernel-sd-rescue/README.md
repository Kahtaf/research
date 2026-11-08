# Stock 3.18 offline SD rescue and CHECK commissioning

Question: can the real offline rescue PLAN preflight run under the exact successful ASUS stock kernel, independently of Linux 4.9?

Status: implemented and built. Six static ARM64 programs and the nonoperational common rootfs are delivered; three focused behavior groups and actual package-size/ELF checks passed. Policy and contexts are byte-identical. No private inputs were opened and no final candidate or physical qualification is claimed.

Important outputs:

- [HANDOFF.md](HANDOFF.md): parent-local CHECK join command, exact behavior and proof limits.
- [scripts/assemble_check.py](scripts/assemble_check.py): genuine manifest/arm join preserving exact original wrapped kernel and original header bootargs; emits no mode/trigger.
- [artifacts/ARTIFACTS.json](artifacts/ARTIFACTS.json): actual compact product hashes.
- [evidence/runtime.patch](evidence/runtime.patch): focused runtime adaptation and CHECK startup.
- [evidence/build-log.json](evidence/build-log.json), [evidence/local-check.json](evidence/local-check.json): actual compile, focused behavior and local package-constraint evidence.

Continuation: parent supplies the actual manifest and existing arm locally using HANDOFF.md, inspects the resulting receipt, and alone drives the physical CHECK trial. PLAN still requires the existing card `asus-rescue-report` directory. CHECK publishes fresh exclusive `SDCHECK.TXT`, requires actual client exit0/full reconstructed-source verification, then syncs and normally reboots. The 600-second client deadline and known parent-controlled Power fallback are documented. Normal/stock production paths remain unqualified. No device/card/cloud lifecycle/process-control work is part of this spike.
