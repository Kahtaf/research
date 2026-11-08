# Parent review: minimal platform design

Question: is the retained protection closure a meaningful reduced-consumer experiment, and are build inputs practical?

Status: reviewing exact design with Opus first. Original preparation preserved. No target compile, package or device action. Parent layer corrects102-byte commandline to89-byte commandline, accepts this board's two GIC arch timer IRQ rows, and moves onlineCPU check after proc mount. Helper IRQ observations are the sum of unique CPU0 PPI29/30 counts, not a singlePPI claim.

Outputs: parent-corrections.patch overlays the prepared remote kernel/out/helper without editing the frozenoriginal, correctedsource/config copies and evidence/corrections.json. Focusedhostparser check pending. No extra driver/configvariant.

Continuation: incorporate Opus assessment, accept/reject retainedBAT/SOC/SPMclosure, then authorizeonebuild only if meaningful. Original protectioncode stays; no bare-core-failure inference or guaranteedruntimecap.

Final commandline89bytes includes calibrated printk.devkmsg=on, preventing the previously observed ten-message rate limit. Two per-cycle clock observations use direct SYS_clock_gettime, avoiding the known conditional VCT_ACCESS/vDSO inconsistency. No repeated clock loop or kernel clock change. Parent parser body is unchanged since the focused host checks; target compilation remains pending.
