# SD frontend RSC1 contract

The supplied baseline PROTOCOL.md describes the separate P10 handoff/restorer.
This frontend uses only the existing image exchange in `baseline/rescue.c` and
`source/client.py`; it never sends op0x30..0x41 handoff/restorer commands.
All frames retain `RSC1`, little-endian uint32 opcode/length, payload <=1048576.

1. Connect fixed `/dev/socket/os_rescue`; require peer UID0/domain os_rescue.
   Daemon still requires client UID2000/domain shell and enforcing policy.
2. Op1 empty -> 0x81 status. Exact RAM manifest hash/count, daemon PID and new
   random per-daemon `run=` nonce must match on every deliberate role connection.
   `run=` is informational binding, not a readiness/admission flag. The daemon
   status addition is backward-compatible with the existing text client.
3. PLAN validates fixed source shape, chunk reconstruction and full raw hashes,
   then closes without reconciliation or mutation. Execute requires exact card
   trigger, immutable parent RAM recovery hash, new durable UNKNOWN card attempt.
4. Op6 `(part=10, chunk=i)` -> 0x86 actual chunk hash, 0x87 actual chunk bytes.
   Hash complete p10 and compare parent RAM pin before writing. No SD pin trusted.
5. For each selected role, op2 `(manifest32,p10pin32,role32)` -> 0x82 token32 plus
   one bitmap byte/chunk. Explicit uncertain-image rollback uses existing op8
   plus uncertain role32 and original full digest32. No new writer API exists.
6. Op3 token -> 0x83 empty. For each exact next chunk, op4 raw bytes or op7 empty
   (only reconciled target matches) -> 0x84 `(index32,skipped32)`. Source bytes are
   validated even when op7 is used. Daemon rereads the target and rechecks all
   existing identity/descriptor/recovery guards; it does not trust the bitmap.
7. Op5 empty -> 0x85 exact expected full digest after actual full target readback.
   Op9 that digest -> 0x89 same digest; daemon terminates the role session.
   Card observation must publish successfully before advancing. The next ordered
   role uses a new deliberate connection to the same authenticated daemon run.

There is no reconnect/retry for a failed role, no rollback/reboot command and no
later role after any unknown/failed outcome. The daemon's 15-second socket
inactivity limit is unchanged. Frontend fragmented frame I/O has whole-phase
limits of 30s status, 60s each chunk exchange, and 600s reconciliation/readback/
commit phases; these are provisional ceilings, not measured target timings.
Local SD reads and kernel syscalls can still stall in the kernel. Expiry does
not cancel daemon block I/O or authorize a retry. Physical timing is a parent
integration gate, not a source flag.
