# Independent PropertyMap source candidate review

Question: do the frozen PropertyMap source, donor, ABI/provider receipts and importer rewrite support the report's bounded claims?

Status: complete. **One P1 finding:** the ARM32 rewrite changes 63 packed relocation targets and misassigns 274 symbols' sections. The production adapter passes the original host fixture plus focused adversarial checks. Originals were not modified.

Important outputs:

- [Findings, exact pins, smallest fix and scope](REVIEW.md).
- [All relocation/section mismatches](evidence/elf-review.json) and [byte-for-byte witness reproduction](evidence/witness-reproduction.json).
- [Fresh version-matched direct provider audit](evidence/provider-recheck.json).
- [Host behavior/ownership receipts](evidence/host-review-commands.json), [focused cases](tests/adversarial.cpp) and [input pins](evidence/review-input-pins.json).

Continuation: run `python3 -B scripts/reproduce_local.py` and `python3 -B scripts/elf_review.py` from this directory, or use workspace-relative paths in REVIEW.md. The latter succeeds when it reproduces the finding. Repair only in a separately owned implementation step, then compare packed relocations by resolved identity and valid ELF metadata. Preserve missing recursive provider/loader, OEM ARM64 object and genuine Android execution gates. No integration/hardware/physical/flash GO.

Remote writes were confined to `/srv/android/asus-camera-property-map-review-20261106` (1,403,617 bytes, below 32 MiB), one CPU/1 GiB with finite CPU/wall bounds. No active R9 state or lifecycle was touched.
