# Exact rescue startup audit

Question: which ordinary boot, init, SELinux, or USB startup contract in the exact installed stock-kernel rescue can explain the observed lack of USB enumeration?

Status: offline audit complete; no deterministic startup defect established. Read [REPORT.md](REPORT.md). The exact kernel supports the concatenated archive and static ranges fit; actual init/policy checks disprove two plausible patch hypotheses. Runtime handoff/initrd/init/adbd remains unresolved. No physical execution is proved by the retained screen/USB observations. Latest user steering defers original-p10 restoration to the parent.

Scope: public saved artifacts only, sequential local inspection, no device/network/VM access, no active R9 source/output/cache/process inspection, no private parent state, no image construction or integration. Originals are read only. Host analysis uses one process at a time and bounded CPU/address space where supported; this Mac does not expose Linux CPU affinity.

Outputs: `evidence/` holds reproducible metadata and tool reports; `extracted/` contains selected public startup binaries/configuration extracted from the exact images, never a full image/source copy; `scripts/` contains bounded offline inspectors; `proposal/` is reserved for a minimal source-only proposal if justified.

Continuation: read REPORT.md when complete and rerun the documented local inspectors if needed. Any future retained boot errors must be supplied sanitized by the parent. This audit supplies no physical GO, flash/reboot/transport command, or approval change.
