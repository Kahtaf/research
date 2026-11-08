# Parent integration report

The Wi-Fi adapter passed 33 offline tests (27 existing writer/restore scenarios and six adapter cases). A real local plan validated the already-reviewed repaired stock-kernel diagnostic against both immutable recovery backups and the pinned Wi-Fi root helper. No device operation was performed by this spike; no runtime readiness is claimed.

Changes are limited to endpoint selection, separate real-hardware serial validation, secure-ADB checks in health and every root envelope, the pinned existing Wi-Fi helper, explicit original root-binary path, isolated staging, transport metadata, and sharing the original USB writer's host lock. Candidate validation, p10 geometry, write bounds, exact stock-kernel restriction, full staged/readback checks, stock inverse, uncertain-transport stop, and manual boot policy are unchanged. See evidence/adapter.diff.

The adapter deliberately retains stop-on-uncertain-write behavior. A transient query can still end a run; it must not silently cause a block-write retry. Backup continuation is a separate read-only problem. Physical diagnostic execution still requires the parent to check current availability and transport after backup work; after a recovery reboot TCP ADB may need re-enabling with a short USB command.
