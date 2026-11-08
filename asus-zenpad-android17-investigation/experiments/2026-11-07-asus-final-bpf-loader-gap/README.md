# Final Android boot: offload map metadata gap

Question: Does the first fatal `offload.o/tether_error_map` failure in the completed final-SYSTEM boot identify a product defect or a stale virtual fixture kernel?

Status: **Resolved as a fixture-kernel gap.** The boot selected kernel `95a62a8b…`, which lacks `BPF_OBJ_GET_INFO_BY_FD` (command 15). ARRAY maps work; their metadata cannot be queried. The physical source already contains the qualified implementation. No product-loader change is justified. Staged integration is source-only; nothing was integrated or rebuilt.

Important outputs: [report.md](report.md) explains the exact failure and smallest next action; [integration/pins.json](integration/pins.json) pins the two-file minimum and complete qualified series; [evidence/replay-result.json](evidence/replay-result.json) contains the one bounded syscall replay; [HANDOFF.json](HANDOFF.json) records the decision.

Continuation: Preserve the actual Android fixture config `c2ea1277…`. In a future separately authorized fixture build, integrate the qualified map-info patch; carry the already qualified LPM/helper series for subsequent networking requirements. Do not substitute the standalone network Image without merging its missing Android configuration. Do not change product loader checks, flags, readiness, SELinux, the physical kernel, or the retained-trace kernel. See the exact source pre/post pins before integration. No further runtime was requested by this handoff.

Scope: One standalone syscall guest, 0.47 seconds under a 90-second bound; no Android OS boot, disk, entropy input, device, cloud lifecycle, active source/output write, or other-worker process operation. Remote writes are confined to `/srv/android/asus-final-bpf-loader-gap-20261107`. Existing private DATA/COW/entropy were not opened or exported. Only public compact facts and hashes were exported; local patch copies come from the published qualification handoff.
