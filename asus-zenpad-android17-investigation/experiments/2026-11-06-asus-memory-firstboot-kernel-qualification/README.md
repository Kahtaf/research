# Memory + firstboot kernel qualification

Question: can the existing c59e030c memory-qualified virtual Image support a later genuine firstboot services fixture while preserving the selected physical firstboot and memory correspondence?

Status: complete; existing c59e Image accepted for future selected-parity firstboot reuse with the documented DEBUG_PREEMPT/CMA/test-board limitations. No new runtime or physical GO.

Outputs: [REPORT.md](REPORT.md), [acceptance.json](acceptance.json), [next-fixture-contract.json](next-fixture-contract.json), [next-runtime checklist](NEXT-RUNTIME-CHECKLIST.md), and exact receipts/config deltas/source maps in evidence/. All 290/134 firstboot selections and 210/72 memory selections were checked against actual remote artifacts and exact physical authorities. Local verification passed 27 assertions and all 510 frozen payload hashes/sizes.

Continue by reading the final report and contract. Do not build or boot from this spike. No active source/out, device, keys, private calibration, build supervisor, or lifecycle work is authorized. All remote inspection must use the product-input-build-kit SSH wrapper; only this spike's owned receipts may be written, at one CPU and 1 GiB.
