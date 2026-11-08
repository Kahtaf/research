# Independent DATA policy correction review

Question: does the pinned Android 7 stock-kernel rescue policy add exactly the daemon DATA AV and singleton ioctl grants while preserving all other policy state and original regression scope?

Status: COMPLETE. No actionable P1/P2 defect found. Prior P1/P2 closed for the offline policy/QA scope; integration remains held.

Important outputs: [REPORT.md](REPORT.md), [INPUT_PINS.json](INPUT_PINS.json), [OUTPUT_PINS.json](OUTPUT_PINS.json), independent raw byte projection, original 72-command scope comparison, 144-row effective matrices, 218-check expanded suite, 19 reproduced negatives and 17 added adversarial policies in evidence/ and artifacts/. Fresh bounded native host tools are in tools/.

Original preservation: all 154 original public files and all 1,167 correction files remain exact. Work was public, local and offline, without subagents. No packaging, target execution, deployment, approval flag or physical/flash GO.

Continuation: read REPORT.md first. To reproduce, create another dated owned spike and copy pinned local inputs, baseline/source/tests/patches and scripts into absent fixture paths. Run bounded.py, build_host.py, build_context_host.py, review_reproduce.py, adversarial_review.py, check_original_scope.py and check_ioctl_scope.py in that order; run one script at a time with python3 -B. Construction scripts refuse existing output directories. The delivered correction and this completed review remain immutable references. Retain the documented initial reviewer lock timeout. Actual install admissions, terminal gates/assembly, global reachable-writer and runtime/physical acceptance remain separate parent work.
