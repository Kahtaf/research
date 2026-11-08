# Parent r8 product build

Question: does the exact reviewed two-file WPA and zRAM-context continuation produce complete Android17 images and pass host qualification?

Status: exact reviewed r8 integrated and launched once. First native phase passed; frozen logs prove the corrected WPA source compiled. Actual native full-image phase ended exit1 at23:48:28UTC; WebView is an unmaterialized134byteLFS pointer. Both original process handles are absent; all attempt/log/cache state is preserved. New r9 source admission is required; no retry. Final image/host/runtime/physical validation remains pending. The actual r7 compiler failure and separately targeted runtime r1/r2 failures remain preserved. No targeted r3 build is needed when the full r8 SYSTEM dependency closure is available.

Outputs: exact prior-failure description, parent acceptance, eligibility and one-shot native launch/terminal observations under evidence. Sealed worker kit remains at /srv/android/asus-reviewed-build-kit/r8.

Continuation: only the kit integrate.py parent entry point, continuously holding the original lifecycle lock. Observe the same actual job; do not retry, clean, alter source, or infer physical readiness from host success. Physical rescue/kernel commissioning and full service/hardware validation remain separate.
