# Minimal counter-route adjudication

Question: does the built delay accessor hide an unbounded/MMIO workaround?

Status: bounded offline review. Initial check rejected the local ancestor head.S hash as different from the current compiled source; no source equivalence is assumed. Source/config/DT evidence below is separately qualified. No source/build/device mutation.

Outputs: evidence/route.json and qualified source copies. No new build admitted; continuation requires actual caller/EL0 return evidence or another specifically supported intervention.

Findings: exact map names the key and workaround pointer. Qualified CPU errata source matches current manifest. Both available OOL alternatives read CNTVCT system registers; FSL has a 200-pair retry bound, and ARM1188873 is one read matching A76 rather than the DT-declared A53. Exact compiled DT has no FSL property. Runtime key and firmware LASTPC epoch are not directly observed. No hidden unbounded MMIO workaround found. This does not rule out stalled system-register accesses or repeated short calls.

Parent rejects two consultant shortcuts: zero OOL key does not make a CNTPCT switch a no-op (it changes the register); missing panic/exhaustion does not exonerate long delays. No global clock pin or further image is justified by this review alone.
