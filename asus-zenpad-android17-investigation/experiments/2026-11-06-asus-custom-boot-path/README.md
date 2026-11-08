# ASUS Z380M/P00A_2 custom boot path

Question: how can this exact locked WW 5.3.20 unit execute a changed
kernel/ramdisk while retaining a credible stock return?

Status: offline research complete, 6 November 2026. **CONDITIONAL GO for one
supervised recovery-slot diagnostic using the unchanged stock recovery kernel
and a minimal changed ramdisk.** Hardware acceptance and restoration after a
failed custom boot remain unproved. No device commands, writers, unlocks,
security changes, cloud operations, VM changes or source/candidate edits were
performed. All work is confined to this spike.

The concrete route is a root-assisted replacement of **recovery only**, followed
by ordinary physical Recovery selection. Keep normal boot intact; return through
Power/Normal Boot, regain the already established stock root, and restore the
exact recovery backup. This does not depend on temporary fastboot boot or BROM.
Root access is established; permission to complete the actual block write has
not been empirically tested. The supervised write/readback would establish it.

New evidence makes this more than a generic suggestion: the exact live-matching
LK invokes image verification, but the recovery header loader **discards the
verification result** and returns the successful header-comparison result. The
earlier policy checker also records a red verified-boot state and proceeds into
the image loader after failure. This is strong static evidence for testing an
ordinary well-formed unsigned recovery image without changing LK or lock state.
It is not a claim that our diagnostic, or the new 4.9 kernel, has run.

## Important outputs

- [REPORT.md](REPORT.md): bounded findings, precise rollback and supervised test.
- [evidence/lk-acceptance-review.md](evidence/lk-acceptance-review.md): instruction
  addresses and manual interpretation of both checks and the recovery load path.
- [evidence/acceptance-facts.json](evidence/acceptance-facts.json): checked bytes,
  state-pointer resolution, recovery geometry and freshly verified backup hashes.
- [evidence/acceptance-disassembly.txt](evidence/acceptance-disassembly.txt): bounded
  decoding of the existing public LK, with literal annotations.
- [evidence/primary-source-search.md](evidence/primary-source-search.md): primary
  source links, limits of the historical evidence, and unsuccessful XDA retrieval.
- [evidence/decision-flow.html](evidence/decision-flow.html): compact supervised test and return diagram.
- `scripts/inspect_acceptance.py` and `scripts/check_evidence.py`: reproducible
  local analysis; neither contains a device transport or writer.

## Continue

From the ideas workspace, the existing audit environment can reproduce this:

```sh
2026-11-05-asus-boot-access-audit/.venv/bin/python 2026-11-06-asus-custom-boot-path/scripts/inspect_acceptance.py
2026-11-05-asus-boot-access-audit/.venv/bin/python 2026-11-06-asus-custom-boot-path/scripts/check_evidence.py
```

They read the existing saved LK, recovery backups and GPT report, and write only
this spike's evidence. Capstone is already installed in that environment.
No backup/key contents are copied here or uploaded. Retain the original private
backup locations and permissions.

Parent's first action: review the diagnostic agent's completed **stock-kernel
control** against REPORT.md and rerun `check_evidence.py`; then arrange the one
supervised recovery-only trial and immediate stock recovery restoration. The
parent owns the hardware decision and any separate writer. Do not substitute the
experimental-kernel candidate for the control. Stop after the control roundtrip
and record the actual outcome before deciding the next kernel test.
