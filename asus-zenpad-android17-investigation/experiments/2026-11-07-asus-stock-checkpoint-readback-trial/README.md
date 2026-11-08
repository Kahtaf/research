# Stock checkpoint before/after-reset trial

Question: does setter(167) read back before reset, and survive into the stock saved reader?

Status: completed one supervised recovery-only trial. Full p10 readback matched d6949069eaa498fcfbc27be707d01dffd7099992c5eb71e2c7c3926639851355. BOOT/SYSTEM/DATA unchanged. Fresh readonly RAM USB reported actual Linux 3.18.35. Android returned automatically to boot c62d7755-35bb-4e53-920c-e69d136043f7.

Result: the complete retained console contains exactly one A7_READ=167 before reset. The saved fiq record is 0. This proves current write/readback in this trial and narrows the failure to subsequent overwrite, reset preservation, snapshot or saved-reader handling. It does not prove Linux4.9 nonexecution. Enforcing restoration verified.

Outputs: evidence/recovery-entry.json, evidence/RESULT.json; full console and saved record under private/. Continue with one bounded offline reset/snapshot/cache analysis before selecting the next diagnostic. Do not repeat this trial or infer a physical boot result from absent markers.
