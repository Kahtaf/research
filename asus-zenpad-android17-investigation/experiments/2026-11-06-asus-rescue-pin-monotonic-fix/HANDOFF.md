# Parent monotonic pin fix handoff

Exact code receipt: 24196e415ac61a56fac5ef1ce145181c90915323129600cc16d67096d1afc62e. Candidate, profile, engine, root dispatcher and16original inputs remain unchanged. Original adapter spike is preserved.

The fix adds schema2 host-boot-bound monotonic pin timestamps, checks both clocks at load and every dispatch, and caps the existing guard by the pin deadline. macOS reads kern.bootsessionuuid through libc without subprocess; Linux reads the host boot_id. Unknown clock epochs/old pins refuse. Capture age begins before USB queries. Historical install proof validates only binding; actual new dispatch always requires a new fresh pin.

All50supplied+new methods and all9reviewer regressions pass in offline guarded processes. Both previously failing wall-rollback reproductions now refuse without writes. New cases cover future/missing clock data, host epoch change, late pin binding and exact deadline. Original failure logs and fixture correction are preserved. No device or target changes; no physical GO.

Review evidence/adapter-fix.patch, HANDOFF.json and exact source/tests. Future per-phase contracts must bind the new code receipt; old contracts/code cannot be reused. After parent technical review, retain the original command interface but use this spike root and new reviewed code hash. No affirmative live approval or flags are included. First physical use still requires actual nearby fallback/fresh USB and source-bound review. This is a fix of the reported expiry issue, not a rescue boot or timing qualification.
