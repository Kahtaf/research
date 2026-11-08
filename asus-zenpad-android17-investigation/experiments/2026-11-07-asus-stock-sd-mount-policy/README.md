# Repair the physically observed SD mount denial

Question: can the stock-kernel CHECK recovery mount the prepared SD after the
observed `init -> rescue_sd_fs:filesystem relabelfrom` denial is repaired?

Status: isolated one-permission policy repair. The first CHECK recovery actually
started stock init, os-rescue and its CHECK runner, then the SD mount was denied.
The runner returned safely to normal Android. No internal image was written.

This spike adds only that observed permission to a copy of the existing policy.
Its inverse must reproduce every original policy byte. Existing types, contexts,
enforcing mode, CHECK-only executables, protocol and kernel remain unchanged.
The parent will rebuild the common archive and locally join the same genuine
manifest/arm after this binary-policy repair succeeds. No private inputs go to VM.

Continuation: inspect the actual policy and assembly receipts, then one physical
CHECK retry with a fresh `SDCHECK.TXT` absence check. Complete source preflight and
a fresh PASS report remain unproved until observed on the tablet.
