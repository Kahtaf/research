# Final installed BPF runtime qualification

Question: Can the final root-enabled Android17 image BPF objects and installed loaders run on the qualified Linux 4.9 virtual fixture?

Status: Bounded unit complete; runtime acceptance BLOCKED. The final vendor filter is rejected by the Linux4.9 verifier with `back-edge from insn 7 to 8`. Genuine platform loading fails critically, exit121. No product changes, children, device operations or physical/flash approval.

Important outputs:

- `report.md`: finding, resources, limits and smallest next action.
- `evidence/final-report.json`: final 26 object/source pins, loader hashes, actual exits and QA.
- `evidence/remote/run-actual/` and `run-mandatory-malformed/`: actual commands, serial logs, input hashes, resource receipts and exits.
- `evidence/remote/evidence/capture.json`: raw before/after identity and exact SYSTEM/APEX extraction bindings.
- `evidence/remote/evidence/final-audit.json`: post-runtime raw/captured-byte verification and allocation.
- `scripts/`: reproducible bounded commands using the fixed SSH wrapper. Do not rerun blindly: capture and run paths already exist.

Remote owned prefix: `/srv/android/asus-final-bpf-runtime-20261106`. No full images downloaded to Mac. The selected small APEX containers/payloads and extracted runtime bytes remain remotely; unchanged qualified kernel and libraries were read from their original paths.

Continuation: Parent should review a Linux4.9-compatible loop-free vendor filter within verifier instruction limits and build it only in the next authorized product attempt. Bind the new final bytes before retesting. Coordinate genuine namespace/property-service integration with its owner before netd behavior and mandatory malformed-object qualification. Cross-profile loopback and UID permission migration remain OPEN/FAILED. Preserve original R9 exit1, selected root-enabled native/host exit0 and the older genuine SetProperty exit125 boundary.
