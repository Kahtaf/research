# One sparse watchdog observation trial

Question: did the watchdog probe clear its enable bit, and which request configuration and restart-entry facts were observed?

Status: one recovery-only physical trial completed; stock Android returned. Full p10 readback matched the candidate. MODE changed from 0xdd to 0xdc (EN 1 to 0); probe rc0; request mode 0x00340003 and request IRQ 0x00380000. No restart-handler marker was observed. RAM loop completion, alarm delivery and after-IRQ snapshot remain unresolved.

Outputs: `evidence/RESULT.json`, `evidence/recovery-entry.json`; complete target console and parser result remain private.

Continuation: consult Large with these measured facts before choosing one new experiment. Do not disable thermal reset paths or infer a reset cause from decimal32. EN0 is one instant, and marker absence is inconclusive. BOOT/SYSTEM/DATA were not written.
