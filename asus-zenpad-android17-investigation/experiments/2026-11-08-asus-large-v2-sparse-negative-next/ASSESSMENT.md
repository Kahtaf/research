# Parent decision

Adopt B as one sparse, observational runtime watchdog unit. Readback/caller facts only; no timeout/kicker/reset-policy/thermal/charging/clock changes. Verify exact base driver/callflow first, keep normal helper/config/DT/virtualcounter/sparseobserver profile. Cold markers: probe/earlyfailure, original stop’s MODE before-value plus one after-read, source-qualified reset-request configuration snapshot, kernel restart-handler entry/caller. No hotarea or per-IRQ recording reintroduced.

Reject overclaims: sparse failure is not publication-independent, nor does an uncertain-epoch cached PC establish stable stall locus. A-readback EN0 does not show this write changed hardware if it was already0; record original before-value and after. EN0 plus no observed restartmarker cannot exonerateRGU/resetrequests or softwarepaths if publication failed. Kernel restart marker identifies entry and immediate caller, NOTpreloader-saved rr_pl.wdt_status producer provenance or necessarily original requester. No clock-to-walltime margin or guaranteed expected console conclusion.

Unknown absence of probe/sink output remains absence, not proof probe wasn’t called. No added lock/barrier spans original hardware operation; accepted marker publication retains known intrusion. One build/trial then interpret, no automatic next watchdogfix/GICunit.
