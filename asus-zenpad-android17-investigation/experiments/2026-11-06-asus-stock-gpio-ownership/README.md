# Stock GPIO ownership observation

Question: which GPIO lines are requested by the stock kernel, particularly the GPIO28 speaker gate and potentially shared GPIO24?

Status: parent-owned read-only kernel metadata observation. The existing pinned authenticated Wi-Fi root helper stages its binary and restores Enforcing. No GPIO/pinctrl/mixer/PCM setting, mount, partition write or reboot is requested. Existing debugfs must already expose the report; an absent report is not permission to mount or infer ownership.

Outputs: unique evidence JSON. Continuation: feed public metadata to the source-port task; this establishes software ownership/state only, not fitted amplifier identity, electrical wiring, active route selection or audio function.

Observed at2026-11-07T00:34:13UTC: chipbase869 for1000b000.pinctrl; global897=local28 requested spkamp-en-gpio/outputlow, global893=local24 requestedUSB_DPN_SEL/outputhigh. Roothelperexit0 confirms its Enforcing-restoration check. These are sampled software requests/states only. The future port must use controller-relativeDTlookup, never these dynamic global numbers. Source-port owner received the public receipt; no physical ownership/electrical/active-route inference follows.
