# Linux 4.9 power-supply BPF filter

Question: Can a loop-free filter preserve the production 32..255 scan and packet classification on Linux4.9 without new helpers or relaxed verifier/socket limits?

Status: **Isolated candidate qualified; parent review and ordinary product build remain required.** Original cc68 baseline rejection reproduced. Candidate2284 instructions, verifier10542 processed, attach0,8556 actual synthetic packets and408156 host oracle comparisons with zero mismatches. No children or active AOSP writes.

Important outputs:

- `source/filter.patch`: production source patch against exact371ca110 preimage.
- `source/preimage.c` and `source/postimage.c`: immutable input/candidate source.
- `handoff/artifacts/postimage.o`: isolated candidate only, never installed into AOSP.
- `evidence/final-report.json`: exact source/object/compiler/dependency/runtime binding.
- `handoff/run-r7/serial.log`: original rejection and successful candidate verifier/attach/socket proof.
- `handoff.tar.gz` and `evidence/handoff.json`: compact hash-verified handoff.
- `report.md`: semantics, test boundaries and retained failures.

Remote owned prefix: `/srv/android/asus-linux49-power-supply-filter-20261106`. Candidate source/patch/ELF and baseline object are0444. Allocation including handoff is11923456 bytes; no kernel or full image was copied/downloaded.

Continuation: Parent reviews the patch, then uses the ordinary separately authorized product build. Bind the newly built installed/final-image bytes before platform-loader/service qualification. Do not install this isolated ELF. Preserve the unchanged prior final-bpf-runtime spike and its genuine loader121 failure. Networking/property/namespace work belongs to other owners.
