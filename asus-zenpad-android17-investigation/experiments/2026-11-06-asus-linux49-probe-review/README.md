# Independent combined Linux 4.9 RAM probe review

Question: does the frozen probe-r2 have a defensible static acceptance contract for a supervised first ASUS P00A_2 Linux 4.9 boot?

Status: **completed; HOLD present handoff.** Fixed artifact packaging passes. Three findings require a separate 4.9 host profile and strict report/return interpretation. First 4.9 execution remains held for physical fallback. Unattended GO and physical boot success are not certified.

Important outputs:

- [REPORT.md](REPORT.md): severity-ordered findings, exact source/address evidence, actual coverage, and conditional continuation gates.
- [review-receipt.json](review-receipt.json): hash-bound static review result, explicitly non-authorizing.
- [proposed-acceptance-contract.json](proposed-acceptance-contract.json): exact candidate binding and host requirements; **not a writer manifest**.
- `evidence/`: independent image parsing, policy/helper reproduction, negative collector/observer reproductions, source pins and executable disassembly.
- `scripts/`, `source/`: review-only tools, mock tests and hash-matched source captures.

No ADB, device, USB probe, root, flash, reboot, remote build/write, cloud lifecycle or running-job/delegate inspection occurred. Existing exports were preferred; missing selected source was read through the authorized SSH connection. Implementation artifacts/manifests and existing spikes were not modified.

Continuation: parent resolves F1/F2 and handles F3 under a new exact-candidate profile, retaining the stock-only writer guard. Read the conditional gates in the report before any supervised first boot. Re-run image parsing using `python3 scripts/inspect_artifact.py`; the other reproductions use exclusive output files and should receive a fresh output directory on replay. Never use live implementation observers/writers or process-observer scripts as offline QA. Parent alone owns physical access, backup completion, recovery qualification and any later physical test.
