# Fixed P10R1 protocol with corrected host completion contract

The target protocol/C sources are unchanged from the reviewed restorer. The new immutable manifest contains exactly original SYSTEM and BOOT. Host `ARMED=False` and `TIMING_QUALIFIED=False` refuse public restoration before protocol. There is no connection discovery, automatic reconnect, live execute profile or approval.

All frames retain RSC1 magic and little-endian uint32 opcode/length, maximum 1 MiB payload. No request accepts a source identifier, partition, path, offset or hash override.

| Request | Payload | Response |
| --- | --- | --- |
| 0x30 | Empty; original daemon IDLE only | 0xb0 after both original-pair proofs and terminal handoff |
| 0x31 | Next exact RAM chunk; 16 chunks total, final 1,011,712 bytes | 0xb1 empty |
| 0x32 | Empty after complete staging | 0xb2 uint32 SKIP plus actual full prior digest; SKIP also emits 0xb4 |
| 0x33 | Empty; READY only | 0xb4 exact full final digest, only after complete write/fsync/reopen/readback |
| 0x40 | Empty, deliberate terminal connection | 0xc0 terminal status; never resets state |
| 0x41 | Empty, deliberate terminal connection | Fixed actual read-only p10 chunks 0xc1 and whole digest 0xc2; never recreates lost host acceptance |

The payload is fully preloaded and verified on the host before requests, then staged/sealed/rehashed in target RAM before writable open. Both original-pair proofs and all p10 scans/identity/descriptor guards remain. The full candidate prior digest is the newly generated external host pin. SKIP needs an actual whole original-p10 read and opens no writable descriptor. Neither branch is physically qualified here.

The host's schema2 attempt is durable UNKNOWN before its first request. The on-disk receipt always remains UNKNOWN with `publication_accepted=false`; `device_outcome` records observations separately. Only successful live return after file publication yields accepted DONE/SKIPPED. Interrupted or failed publication/return remains UNKNOWN even if a file says device_outcome DONE. Replay, target status and later stock observation cannot recreate acceptance. Retain all evidence and never automatically retry, reconnect, reboot or reset.

Whole-phase deadlines include all fragmented I/O and are capped by a hard 600 seconds. Provisional ceilings: handoff180; staging15 per chunk; prepare60; restore120 seconds. They are not measured/sufficient limits. Public timing qualification remains false. Phase expiry cannot cancel target block I/O or authorize restarting a consumed daemon. Target socket inactivity limits remain unchanged. Later physical timing qualification and source/evidence binding belong to the parent; the flags must not simply be toggled.

See `inputs/host-contract-HANDOFF.md` for the exact parent's R1/R2 contract and `REPORT.md` for evidence boundaries and remaining physical gates.
