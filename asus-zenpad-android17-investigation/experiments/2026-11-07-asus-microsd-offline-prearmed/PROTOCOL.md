# Retained RSC1 exchange with two explicit execution profiles

Public opcodes/payloads are unchanged. Frames are RSC1 + little-endian op/length,
maximum payload1MiB. The frontend authenticates root/os_rescue on its fixed Unix
socket; daemon authenticates UID2000/shell. RAM manifest hash, role count, PID and
actual random run nonce are bound by status (op1 ->0x81) on each connection.

Default PLAN closes the initial status connection, checks complete source
reconstruction and full raw hashes, and exits with no reconciliation/mutation.
Both execution profiles also close that connection before preflight, so the
unchanged daemon15s inactivity limit cannot invalidate an idled status stream.
A deliberate post-preflight connection must report the same PID AND nonce;
neither profile silently rebinds to a restarted daemon.

Online --execute uses the unchanged live-run manifest/selection trigger and
independent root-owned RAM recovery pin. Offline --offline-prearmed uses exact
`OFFLINE-PREARMED ASUSR002 manifest arm selection` + LF in execute.trigger, bound
to immutable root-owned RAM /rescue.sd.arm and actual daemon-bound RAM manifest.
The arm is an ordinary preboot pairing ID; it is not authentication or admission.

A new O_EXCL durable UNKNOWN attempt is published before any image reconcile or
write. An existing report ends execution across daemon/recovery boots. After
same-instance reconnect, op6 `(10,chunk)` returns0x86 chunk hash +0x87 actual raw
bytes. The complete16740352-byte hash either must match the independent online
pin or becomes the offline boot-session RAM baseline. Offline capture takes no
pin from SD and publishes no baseline on a missing/invalid frame. The actual
whole hash is fsynced to the report before image mutation. Parent independently
full-readback-verifies admitted p10 before manual entry; offline capture does not
prove that admission/action.

Ordered normal roles remain2,4,3. For each: op2 manifest/p10baseline/role ->0x82
token+bitmap (explicit inverse retains op8 constraints); op3 token ->0x83;
ordered op4 validated raw chunk or op7 verified target skip ->0x84 index/skip;
op5 ->0x85 actual full target digest; op9 digest ->0x89 identical acceptance.
Any failed/unknown source, status, report, target or ack stops before a later
role. Successful live acceptance plus report publication is required to advance.
Historical reports do not recreate live success. No retry/inverse/reboot occurs.

The accepted recovery_phase session/header is unchanged. Full recovery proofs:
before reconciliation, after scan, activation, after full target readback and
commit. Per-chunk checks retain source/token/image/pin/manifest bindings,
identity and held target/recovery descriptors plus current-target/chunk proofs.
The phase guard is session-local, closes on all exits/handoff, and never survives
reconnect or a failed proof. Content changes are detected only if a later proof
reads the changed bytes. Same-node open-description substitution is not fully
detected; the accepted no-writer/no-rebinding premise must hold through receipt.

Wire phase deadlines remain30s status,60s chunk and600s recovery/reconciliation/
commit; not physically qualified timings. SD/kernel I/O can still stall, and
expiry never cancels target I/O or authorizes another attempt. Final helper
admission/integration is a separate parent input, not a new opcode in this task.
