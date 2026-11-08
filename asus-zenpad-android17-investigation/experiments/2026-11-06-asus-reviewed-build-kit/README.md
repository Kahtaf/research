# Reviewed SDK37 integration/build kit

Question: can the parent integrate the reviewed combined product and launch one incremental full build after the original r5 job is genuinely terminal, without a lock gap or stale validator paths?

Status: implemented in this spike and `/srv/android/asus-reviewed-build-kit/r1`; behavioral tests and read-only live preflight completed. Default PLAN_ONLY. No active integration, next full build or device action was performed. Scoped firstboot parity is accepted separately; full service-chain and physical combined-kernel execution remain unproved.

Important outputs:

- `HANDOFF.md`: exact sealed parent commands and continuation boundaries.
- `REPORT.md`: implementation, self-review, pins, validation and limitations.
- `scripts/integrate.py`, `build.sh`, `check_launch.py`: terminal/process/lock gates, preservation, exact integration and one-shot incremental launch.
- `scripts/validate_completed_product.py`, `verify_full_images.py`, `verify_root_payload.py`, `verify_google_payload.py`: genuine future product/image validation and parent/source-adapter receipts.
- `inputs/plan.json`, `inputs/kit-pins.json`: 41 external pins and 42 internal pinned files.
- `evidence/*verified*`: final 21-test Linux suite, real live-r5 refusal and source/input audit.

Continuation: parent reviews the report and uses `HANDOFF.md` only after actual r5 terminal evidence. The kit takes the real full-build lock and retains it through integration, build and host validation. Never bypass an existing attempt/revision, retry partial integration, or treat a receipt or time as physical presence. Parent owns all device/root/USB/flashing and hardware decisions.
