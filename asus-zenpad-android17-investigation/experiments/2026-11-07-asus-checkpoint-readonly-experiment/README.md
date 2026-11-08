# Checkpoint reader and header experiment

Question: do the existing stock diagnostic reader, OEM header access, and retained logger's static contract support a later calibrated checkpoint? Status: one offline contract inspection plus one bounded read-only USB snapshot planned. No VM start, build, memory write, flash or reboot. This can validate reader availability/format and expose guard mismatches; it cannot by itself prove a new marker survives reset. Outputs: evidence, offline report and private raw USB result. Stop after this one snapshot/source check; do not expand into more probes.

## Completed result

Read-only contract experiment supports the candidate channel, not completed retention calibration. Shipped binary confirms saved fiq_step u32 reader and old-state snapshot before current clear. Live corrected USB read retrieves WDTstatus32/fiqstep0 and RAM-console reservation0x44400000+0x80000. Latest4.9 package passes enumerated static DT guards; no obvious static mismatch. Current cached PCs0xffffff800810e078/0xffffff80085b2c54 are retained as clues only; captureepoch unvalidated. CurrentstockDT is not failed4.9runtimeDT. Existing rawheader interface unavailable; no interfacecreated or memorywrite. No reboot, imagewrite, VMstart or firmwarechange; existing on-demandhelperstaging occurred and Enforcingrestored.

Original snapshot's head -c failed on Android7. Preserved errors; one corrected bounded-dd read admitted as snapshot-r2.json. Initial emptyfields do not prove hardware absence. Raw header check frominitialread unavailable and not retried. See evidence/RESULT.json and offline/REPORT.md. This task stops here; a future writer/stockroundtrip must be calibrated before interpreting an absent4.9marker. No fullOSflashGO.
