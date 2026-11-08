# Battery uevent property readout control

Question: does omitting only the named battery's uevent property getter loop change this exposure while other power/thermal readers remain?

Status: **one diagnostic recovery candidate delivered; STOP**. One incremental kernel build (-j8), zero helper compiles, one restricted actual PLAN. Production-body/source/ELF/frozen-package/parser checks passed. No device access or trial. Exact VM verified TERMINATED; owned SSH master closed.

Important outputs: [candidate and handoff](output/HANDOFF.md), [record contract](output/RECORD-CONTRACT.md), [pre-build caller limits](evidence/CALLER-INVENTORY.md), [remaining native channel6 route](evidence/CALLER-ELF-ADDENDUM.md), [complete patch](source/changes.patch), [source/ELF proof](evidence/SOURCE-ELF-PROOF.md), [pins and commands](evidence/handoff.json).

Continuation: parent owns at most ONE separately bound physical trial and verified stock return, then STOP. Do not repeat build/package/PLAN/trial, suppress other readers, integrate product sources, or advance storage. Missing/stale/undrained evidence remains UNKNOWN. Fast2M is not30sec stability; even a positive supports workload dependence only. Read the handoff and parser contract before continuation.
