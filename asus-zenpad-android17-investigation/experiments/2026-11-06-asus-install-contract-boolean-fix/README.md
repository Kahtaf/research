# Strict install-contract boolean

Question: does the actual full-install parent guard admit only JSON boolean true for `armed`?

Status: parent-owned one-line correction, isolated from the reviewed implementation. No transport import, child, device, network, image or approval operation occurs. The focused check executes only the actual parsed guard, so it proves this boundary predicate, not the complete CLI or transfer lifecycle.

Outputs: source/parent_remote.py, strict-armed.patch, evidence/before.json and after.json, and source-pins.json. The original review's other five findings remain unresolved here.

Continuation: incorporate this exact delta into a separate full-install lifecycle correction; retain PLAN_ONLY and obtain fresh independent review of the combined revision. This folder creates no execution authorization.
