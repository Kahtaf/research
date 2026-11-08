Exact sealed kit: 744fa117bba0e4ba9895af792ddc71f1cbe99196cb752593e560064ef8d41e69 (193 files). This local command sheet adds the seal to the sealed generic handoff; it creates no authorization.

# Parent-only continuation commands

Review `kit-seal.json` and `inputs/kit-pins.json`, the 61 explicit lineage records, the 23/3/26 BPF matrix, the parent method receipts, source/preservation audit, root-property-path pins and Linux QA. Method acceptance and input acceptance do not substitute for kit-specific review. Preparation created no affirmative failure acceptance or launch contract.

Run on the VM as the parent. Assign `expected` from the independently reviewed `kit-seal.json` value; do not derive an expected seal from unreviewed bytes.

```sh
kit=/srv/android/asus-reviewed-build-kit/r9-exec-r1
expected=744fa117bba0e4ba9895af792ddc71f1cbe99196cb752593e560064ef8d41e69
python3 -B - "$kit" "$expected" <<'PY'
import sys
from pathlib import Path
root=Path(sys.argv[1]);sys.path.insert(0,str(root/'scripts'))
from integrate import verify_pins
assert verify_pins(root)==sys.argv[2]
assert not (root/'attempt').exists()
print('EXACT_REVIEWED_PREPARATION_VERIFIED')
PY
python3 -B "$kit/scripts/integrate.py" --audit-inputs
```

`--audit-inputs` actually audits its stated selected-source/61-output scope. It does not inspect processes, acquire locks, integrate or establish native closure. Default PLAN_ONLY without review refuses specifically for missing parent-authored actual r8 failure acceptance.

After independently reviewing the kit, obtain the current descriptive template through the inherited parent lifecycle guards. A held lock or other native job refuses immediately; there is no wait/retry path.

```sh
mkdir "$kit/parent-review"
python3 -B "$kit/scripts/integrate.py" --describe-prior > "$kit/parent-review/describe-prior.json"
```

The result contains `result.review_template` with `reviewed_by_parent=false`, an empty reason and the exact observed prior failure/preservation/image identity. The parent must author `parent-review/r8-failure-acceptance.json` from that exact template after review, set its own affirmative review and nonempty reason, and independently pin its SHA256. The worker has not supplied an approved file. Parent factual r8 review in `inputs/parent-r8-terminal-review.json` is retained as facts only. If observed prior bytes change, describe/review the actual current facts; do not edit a sealed kit or reuse a stale acceptance.

```sh
review="$kit/parent-review/r8-failure-acceptance.json"
review_sha=EXACT_PARENT_AUTHORED_REVIEW_SHA256
python3 -B "$kit/scripts/integrate.py" --mode PLAN_ONLY \
  --prior-failure-review "$review" --prior-failure-review-sha256 "$review_sha"
python3 -B "$kit/scripts/integrate.py" --mode PARENT_EXECUTE \
  --prior-failure-review "$review" --prior-failure-review-sha256 "$review_sha"
```

Execute once after review. Native revision remains r9, with `/srv/android/asus-device-product/logs/full-build-r9.*` and this kit's exclusive `attempt` directory. The original global native guard, existing nonblocking continuous flock, inherited FD/ancestry check, actual terminal acceptance, exclusive backups/atomic copy/full readback, post-delta dumpvars/configuration and final validators remain mandatory. Do not invoke build.sh directly, replay logged commands, clean, touch, fabricate log rows or force freshness. Any actual attempt is consumed permanently, including failure.

Expected sole active write: original 134B arm64 WebView pointer a7b12... to the exact 260835655B payload 1d2f... . The payload and frozen qualification milestone are VM-only and unchanged. All other ABI pointers, kernel/configuration, charging inhibition, audio exclusion and frozen probes remain outside the delta.

Remaining acceptance: parent-specific kit/map review and actual failure acceptance; genuine successful ordinary incremental native phases and final product validators; separate exact-final-byte runtime qualification of the three changed/new BPF objects; parent-owned actual full-SYSTEM header/kernel mount gate and all remaining runtime/device/flash gates. The original netd inventory c523... is not a runtime golden. Baseline classification preserves optional-load failures and open feature limitations; the cross-profile loopback/UID migration issues stay open. Host preparation and native host assembly do not claim physical GO, runtime BPF readiness, app-SU or a completed OS build.
