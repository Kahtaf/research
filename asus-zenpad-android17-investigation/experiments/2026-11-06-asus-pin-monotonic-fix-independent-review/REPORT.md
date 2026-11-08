# Independent review of the monotonic USB-pin fix

No concrete defect found in the reviewed delta. The previous P1 clock-rollback finding is closed by the inspected implementation and offline regressions for code receipt `24196e415ac61a56fac5ef1ce145181c90915323129600cc16d67096d1afc62e`. No remaining software blocker was identified within this narrow offline transport revision. No source fix is requested.

This is an independent child review performed without delegation. It supplies no execution approval, affirmative operational flag, or physical GO. The parent owns all real operations. No physical, transport, boot, or timing success is claimed. Target rescue internals, LK, and audio were not re-reviewed.

## Findings and source assessment

Read the original finding, the new handoffs and README, supplied patch, copied production adapter and relevant dispatch/linkage paths, supplied tests, and previous nine regressions. Independently regenerated the adapter patch: it matches the supplied patch exactly. Only `source/adapter.py` differs among the five receipt files.

[Host epoch acquisition](snapshot/2026-11-06-asus-rescue-pin-monotonic-fix/source/adapter.py#L145) uses the Linux host boot UUID or the macOS boot-session UUID through libc. The actual macOS query was exercised twice under the offline audit hook and returned a stable canonical epoch. Linux reads, invalid/unavailable values, unsupported hosts, and macOS query success/failure/size cases were also exercised with bounded fixtures. No helper process is needed for epoch acquisition.

[Pin validation](snapshot/2026-11-06-asus-rescue-pin-monotonic-fix/source/adapter.py#L224) checks the schema, identity/source binding, current host epoch, wall age, and monotonic age. The [guard](snapshot/2026-11-06-asus-rescue-pin-monotonic-fix/source/adapter.py#L260) caps the existing deadline by `created_monotonic + 180`, including late assignment. Its final strict deadline check rejects the exact 180-second dispatch boundary after source reads, pin validation, or evidence persistence consumes the remaining time. The shorter contract deadline continues to apply.

[USB capture](snapshot/2026-11-06-asus-rescue-pin-monotonic-fix/source/adapter.py#L422) starts both timestamps before enumeration. A deliberately slow 195-second capture retained its original timestamps and was refused on reload. A later health snapshot did not refresh the active pin or its deadline.

[Historical install linkage](snapshot/2026-11-06-asus-rescue-pin-monotonic-fix/source/adapter.py#L530) checks binding and the existing capture/source/completion linkage without requiring the historical pin to be fresh in the current host epoch. This did not bypass freshness of the new restore pin. Tampered source/identity fields or capture bytes were still refused. Uncertain completion still stopped later commands in the previous production-execute regressions.

## Fresh execution evidence

All final suites passed: 50 supplied methods, nine previous independent regressions, and 21 fresh independent methods; zero failures/errors and zero audit-blocked events in those final runs. Each runner installed its process/socket audit hook before importing the implementation and helpers. Actual production subprocess/device/network operations were zero. Typed command/storage fixtures ran the copied production nested helper and adapter methods; their recorded command intents are simulated evidence only.

Receipts and complete test logs:

- [Supplied 50-method run](snapshot/2026-11-06-asus-rescue-pin-monotonic-fix/evidence/offline-1794006389677503000/receipt.json).
- [Previous nine regressions](snapshot/2026-11-06-asus-rescue-pin-monotonic-fix/evidence/targeted-1794006389677542000/receipt.json).
- [Fresh 21-method run](evidence/fresh-1794006533988862000/receipt.json), with [exact test source](scripts/fresh_review.py), per-command records, full modeled readbacks, pins, journals, and scenario observations retained.

Freshly reproduced the original two cases against actual production paths:

1. After production setup, both staging checks and a full stock read, move from wall/monotonic `2000000000/1000` to `2000000100/1200`. Production `Transport.write('candidate')` refuses: zero writes, terminal stop, and the command count remains 114. See [observations](evidence/fresh-1794006533988862000/test_nested_write_refused_at_200_elapsed_despite_100_wall/observations.json).
2. Publish the actual production USB snapshot and completion journal, then reload at wall/monotonic `2000000100/1400`. Production `load_pin` refuses the serialized pin; command count remains 13. See [observations](evidence/fresh-1794006533988862000/test_serialized_pin_refused_after_400_elapsed/observations.json).

Additional fresh cases expired the pin during actual candidate-write intent persistence and after source checking; changed host epoch at that same nested-write boundary; and consumed the final time after pin validation. Each stopped before dispatch and latched refusal of cleanup, stock writes, and enumeration. The final-intent case preserved exact-stock status and recorded the consumed attempt as `not_dispatched_run_consumed`.

The actual production `main` path was exercised with a successfully loaded pin becoming exactly 180 seconds old before late assignment: it refused before reserving install or issuing new commands. A full modeled install/restore lifecycle succeeded after the historical install pin aged out and the host epoch changed, with a fresh schema-2 restore pin and changed transport ID. Conversely, a fresh historical linkage plus a current restore pin aged 400 monotonic/100 wall seconds refused before any restore command. These are fixture lifecycle results, not device results.

The first fresh-suite run had three fixture-placement failures: my contracts were outside the copied adapter root, so the production owned-contract check refused them before the lifecycle was exercised. The [initial run](evidence/fresh-1794006486667146000/receipt.json) and exact test source are retained. Corrected only the review fixture paths; the subsequent 19-method run and final 21-method run pass. No production source failure is inferred. The parent's earlier missing-negative-fixture run/correction also remains preserved in the unchanged parent evidence.

## Exact bytes and preservation

Canonical sorted five-file receipt: `24196e415ac61a56fac5ef1ce145181c90915323129600cc16d67096d1afc62e`.

- `profile.json`: `661d93cbc012d839429bb1b87431fb83b5f646833ee59d307e0e60461b7cda6f`
- `source/adapter.py`: `81555d5b4374e4faca65e98f2212003bada3afba37ee906dd3b72a9fcfe23c01`
- `source/engine.py`: `630c4aaadbb418dc0af1f5a00628b3ec16117bb165707b4d18794c124464a681`
- `source/root_dispatch.py`: `38c8030193f32084b6549bf81f6e1d2f9428fb516a6853295eb1adb4208407bc`
- `source/preserved.json`: `80475bab124d355255ce10d4224ffc89ac20b61ddc440d88303f5fa47638ba8c`

Original receipt independently recomputed as `5f20aece6bfa3ede3e937766ff390e6a575cbbc97759cbe52a3f8a09b68f5a72`. Profile, engine, root dispatcher and provenance bytes are unchanged. Candidate `5a61d3d65a7ba6b29745a965d9911ab4483c951a0327339839a0541bcb9ab30f` (10,412,032 bytes), full padded p10 `3f99c785cca60bf56c2505711e2d26b72623daf28180515d44c5ba2abf03a44a` (16,740,352 bytes), and fixed stock `902b2f06a01cca574b4aa374e67c4e7f8f0ed53f6e6a55017b6d96351f0f1f20` are unchanged. Engine/target definitions were hash-compared, without a new target review.

[Preservation evidence](evidence/preservation.json) verifies all 7,377 baseline files across the parent, original adapter and earlier review trees plus named public inputs remain identical, with no file-set changes. It additionally compares the original 51 adapter files and 16 public inputs to the earlier independent review's recorded hashes. The extra public negative fixture and all 34 initially copied snapshot files are unchanged. Exact pins are in [pins.json](evidence/pins.json); before/after manifests and the regenerated patch are retained. No repository was moved and no private calibration/key input was accessed.

For continuation, use this exact reviewed receipt and retained offline tests. This result concerns the repaired host-side expiry admission and its relevant linkage paths only. Real USB/session/storage behavior, elapsed physical execution, boot, manual return, and hardware remain outside the evidence; they are not new findings. All real decisions and actions remain with the parent.
