# Rescue host remote source adapter

Question: can the existing RSC1 rescue client consume the approved raw VM sources without storing full images on the Mac?

Status: host implementation complete; 28 offline tests and bounded read-only production SSH samples pass. Default PLAN_ONLY. No device operation, arming, physical qualification, or new OS approval is supplied here.

Outputs: `source/`, fixed `profiles/`, `tests/`, compact `evidence/`, and `REPORT.md` with parent continuation commands and limitations. All work is confined to this spike; original rescue source and artifacts are immutable.

Continuation: read REPORT.md and PARENT_COMMANDS.md before use; run `python3 -B source/verify_handoff.py` for offline integrity. Only the parent owns current authenticated transport selection, approval contracts, arming and target use. Full source preflight must run again on the same held descriptor before any target shell. Bounded samples are not preflight receipts. Unknown install images remain unbound.
