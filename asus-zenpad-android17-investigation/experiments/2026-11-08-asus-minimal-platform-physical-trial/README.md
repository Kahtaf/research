# Minimal-platform physical experiment

Question: does the reduced-consumer Linux 4.9 baseline complete normal-priority RAM computation and five timer wakeups, then return to stock?

Status: parent review and real PLAN passed; one guarded recovery-only installation and one trial authorized. No BOOT/SYSTEM/DATA writes.

Outputs: evidence/recovery-entry.json, actual installation receipt, original complete retained log and strict decoder result.

Continuation: collect the fresh complete stock last_kmsg after independently verified return, bind the exact installed image and geometry, run the supplied decoder. Incomplete or negative results stop for reassessment; no automatic new variant. Owner accepted eventual manual Power fallback.

Physical result: exact fresh 4.9 entry, PID1/uname and normal scheduler observed. Last helper record is compute-begin; no compute-end or timer records. Stock Android returned with a new boot ID. Experiment 3 remains open; cause UNKNOWN. Original complete raw retained privately via evidence/collection.json. Decoder also refuses the extra known OEM framing; no normalized copy or positive admission was manufactured. No automatic repeat or further variant.
