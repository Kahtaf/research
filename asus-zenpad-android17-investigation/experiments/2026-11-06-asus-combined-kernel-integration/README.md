# Combined physical kernel integration

Question: Can the qualified firstboot and network changes be combined with the physical SOC, charging and radio kernel while preserving the live SDK37 AOSP build?

Status: Complete for isolated compilation/static verification and staged handoff; runtime/physical/full-product readiness remains unproved. PLAN_ONLY for device operations. Final kernel SHA256 `46895deb12ec94160ea5af0e85afa89c6de84971db126bb94c60cec1ec3ec401`, 7705525 bytes, compile exit0.

Outputs: `REPORT.md`; `artifacts/handoff-r5/manifest.json`; `artifacts/handoff-r5/Image.gz-dtb`; exact source/config/DT/symbol/product receipts in the handoff; compact evidence in `evidence/`; executed scripts in `scripts/`.

Continuation: Inspect actual remote process/exit/log state before doing work. Never modify `/srv/android/lineage24` while its original r5 build is live. Parent owns all device/USB/ADB/flashing operations and subsequent AOSP integration. Preserve prior artifacts. No physical/runtime/full-OS readiness is implied by compilation.
