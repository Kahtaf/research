# Correct the MT8163 APXGPT clock source

Question: can the proven counter-rate mismatch be fixed without changing its bus gate?

Status: one-line source patch staged only, not applied to any active source or full Image. The actual
e9/r2 DT declares `bus`, `clk13m`, `clk32k`. The driver already enables the
separate named `bus` input but then obtains index0 again as the counter clock.
The patch requests the declared `clk13m` input for the counter programmed with
SYS13M. Existing clock prepare/rate/error paths and the separate bus gate remain.
This is specific to the pinned MT8163 DT contract; other board contracts are not
qualified by this patch.

Important outputs: `timer-clock.patch`, source pre/postimages and
`evidence/source-change.json`. The preimage matches the compiled e9 source
receipt in the physical-boot-gap spike. No frozen kernel, device, VM source or
image changed; no new tests were run. This is not a proven boot-gap fix.

Continuation: include this exact one-file delta in a later isolated diagnostic
kernel revision, compile the real object/full Image and retain the original
e9 baseline for comparison. Coordinate the independently owned retained-RAM
logging patch before a combined build. Do not substitute a new kernel into
existing frozen probes or claim physical startup from this source-only result.

Actual real GCC13 ARM64 object compilation passed against pinned e9 headers/config; object8,536B SHA19893e566b1e527894299b07a2951a76e3cfde0d888f080075c04565b06a8cdb. Only new owned prefix received outputs; selected old source/config/command inputs remained unchanged. Full Image and physical operation remain unproved.
