# Stale recovery request cleared and reconciled

At 2026-11-06T21:46:32Z, the parent made exactly one reviewed OEM framework
`clearBcb` call. It returned no-exception/true. The API return was observed;
`clear-bcb` subsequently reported stopped, no uncrypt process or socket remained,
and the other related services were inactive. No reboot was requested.

Two independent 524,288-byte postimages both match original whole-p12 SHA256
`8c9e2c158ac95f152d08ea9de929ae36d054131ca4b10620890974ed831480ef`.
Both before/after comparisons show exactly 20 changed bytes in [64,84), now
restored to zero. Every other byte is unchanged. Private captures remain in the
existing private capture directory; only aggregate results appear here.

The device still reports completed stock Android, Enforcing, and secure ADB.
No BOOT, SYSTEM or recovery image write was issued. This does not qualify any
recovery diagnostic or Android17 boot; it removes the stale-request gate that
had stopped the previous stock-only preflight.

The original identity preflight stopped correctly on a policy SHA mismatch.
Read-only analysis established that live and saved policy differ solely in
serialization order of all 17,746 complete access-vector records and six
filename-transition records. The complete prefix, intervening fixed sections
and remaining 69,947-byte suffix match; duplicate/conflicting keys are absent.
Both policies parse with actual libsepol, have version30 and the same counts;
all 32 relevant policy queries agree. Five malformed/differing-policy negative
cases are refused. Parent accepted this exact equivalence before the operation.
No policy was changed. Initial failure evidence and source are preserved.

Authoritative records:

- `evidence/final-acceptance.json`: API, quiescence, two full readbacks and stock status.
- `evidence/api-attempt.json` and `api-result.json`: consumed one-shot intent and complete result.
- `evidence/parent-review.json`: source/evidence pins and bounded operation scope.
- `evidence/live-preflight.json`: selected framework, native, fstab, descriptor and policy identity.
- `evidence/parent-policy-acceptance.json` and `policy-order-comparison.json`: exact equivalence proof.

Do not rerun the action. The exclusive attempt marker is intentionally retained.
Any later diagnostic needs its own fresh preflight/review. Whole-p12 identity
must be rechecked at that operation's admission; this receipt is historical
evidence, not a reusable live pin. The original stock-only controller review
expired at21:30UTC and remains expired. First Linux4.9 RAM-probe boot still needs
the separate qualified transport and an actual nearby Power fallback.
