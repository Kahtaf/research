# Android runtime network parity

Question: Can the selected Android virtual kernel retain its complete config, integrate qualified networking patches 01–04, and advance one actual final-SYSTEM startup past the missing BPF metadata API?

Status: COMPLETE — one clean-output `-j8` kernel build succeeded; one actual Android startup advanced through NetBpfLoad, then failed on the critical vendor healthd BPF object. QEMU was stopped at init's fatal confirmation after 399.468 seconds, within the 600-second bound. `bpf.progs_loaded` remained unset; zygote/framework were not reached. No second boot or automatic fix.

Important outputs:

- [report.md](report.md): actual result, preservation evidence, stop-delay limitation and next boundary.
- [HANDOFF.json](HANDOFF.json): exact kernel/config/five-source hashes and machine-readable outcome.
- [run-runtime/serial.log](run-runtime/serial.log): actual final-SYSTEM serial.
- [evidence/boot-boundary-lines.txt](evidence/boot-boundary-lines.txt): compact loader/fatal events with serial line numbers.
- [evidence/public-report-compact.txt](evidence/public-report-compact.txt): deduplicated read-only observer output.
- [evidence/build-result.json](evidence/build-result.json), [evidence/integration.json](evidence/integration.json), [evidence/built.config](evidence/built.config): build exit and exact preservation.
- [evidence/base-unchanged-receipt.json](evidence/base-unchanged-receipt.json): SYSTEM/BOOT identities unchanged.
- `scripts/`, `integration/`: owned build/startup machinery and qualified patches/pins.

Remote prefix: `/srv/android/asus-android-runtime-network-parity-20261107`. Large build artifacts, sealed DATA/COW and fresh entropy remain there. No generated keys or private data were exported. Original SYSTEM and BOOT were not modified, copied or fully rehashed.

Continuation: isolate the genuine BPF_PROG_LOAD E2BIG rejection for `/vendor/etc/bpf/filterPowerSupplyEvents.o` on this exact Image/config before proposing another change. Preserve the failed run. Further build/startup requires separate authorization; do not rerun this spike automatically. No full-boot, hardware or flash success is established.
