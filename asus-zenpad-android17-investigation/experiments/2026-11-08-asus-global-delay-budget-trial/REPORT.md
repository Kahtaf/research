# One delay-budget trial: UNKNOWN, stock return verified

Exact recovery-only installation/readback passed for full p10 b3ff63a119f791e8d38ab75d2586aba52cf77086026cdfb7ff3fab706d1474c1, then one USB recovery reboot was acknowledged. Fresh kernel UUID a4e847a5-f502-4562-8e6a-c9a358e3f22f appears exactly once. The intentionally reused helper UUID a60fca94-e760-4ce5-a790-5c9a818ce406 reports actual 4.9 uname, normal scheduler and compute-begin only. No compute-end, timer, exhaustion or panic text is retained. Two later thermal deferred-probe lines remain, as before.

Complete original raw: 16,737 bytes, SHA256 e22ab1b87d2e61e20edc6a09b7f6779739f4c4a4b261a08dab6d4093d4abd99a, private path bound by evidence/collection.json. No altered decoder/acceptance was supplied. Missing exhaustion is UNKNOWN, not evidence against the delay family: counter-read/YIELD stalls, repeated shorter calls, publication failure or other obstacles remain possible.

Fresh stock boot 085392d3-3183-407f-827c-ddefe1308613 was independently verified over USB. No BOOT/SYSTEM/DATA image writes. Origin of stock return is not established.

One cached /proc/aed/reboot-reason read on that boot returned 6,494 bytes, SHA256 693fd76847d4f5b16b89b592a4397412ef6f7aeb7a8a99c1637f2cb8b5014540. CPU0 cached PC changes from prior r3 __delay+0x44 (0xffffff80082f6114) to this candidate __delay+0x54 (0xffffff80082f6124). The new exact linked disassembly identifies the key-load instruction at +0x54. This build-correlated movement supports association with these kernels, but does not prove firmware latch epoch or exclusive stop point. Other cores zero; status32 remains an unqualified retained/preloader field, not decoded raw RGU status. Private report is bound in evidence/cached-reboot-report.json.

Attempt ends after one physical trial. No automatic repeat, new variant or product flash. Experiment 3 remains open. Reassess the complete result before choosing another experiment; identify how it differs from the completed selected CNTPCT and per-invocation-budget controls.
