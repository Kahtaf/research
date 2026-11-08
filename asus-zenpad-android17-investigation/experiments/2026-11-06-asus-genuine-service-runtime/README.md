# Genuine SDK37 service runtime

Question: How far does genuine init → service managers → software Keymaster4 → keystore2 → post-data APEX → authenticated adbd run on the qualified enforcing ARM64 Linux4.9 guest?

Status: **Partial runtime qualification completed; official product artifacts block continuation.** Both real managers answer functional IPC. The mandatory platform BoringSSL self-test is missing; runtime APEX/properties/trust metadata also remain incomplete. No framework/hardware/physical GO.

Important outputs:

- [REPORT.md](REPORT.md): results, provenance, limits and remaining gates.
- [HANDOFF.json](HANDOFF.json): machine-readable continuation.
- [PARENT-REQUEST.md](PARENT-REQUEST.md): exact official targets/dependencies.
- `source/`: runnable owned capture, generation, probe and bounded serial-run scripts.
- `artifacts/evidence-final-r3.tar.gz` and extracted `artifacts/frozen-final-r3/`: compact verified evidence. Large images/ELFs stay on the VM.

Remote ownership: `/srv/android/asus-genuine-service-runtime` only. Read REPORT/HANDOFF and `evidence/qualification-final.json` before continuing. Inspect existing terminal handles; use new numbered input/run directories. From the remote fixture, `python3 source/run.py r10 r9` reproduces the current failure with fresh disposable disks. Initial capture/preparation deliberately rejects existing destinations. Never edit active AOSP/out or prior fixtures; coordinate any new official capture with the parent. Preserve original FDE data.

Model preference: **gpt-6.1-sol** going forward. No subagents. One-CPU, 1-GiB guest with bounded TCG/address space and sequential wall-limited runs. No physical ADB/USB, user credentials/keys or default host ADB server. `source/remote.py` uses the existing strict-host-key SSH route; it contains key paths only.
