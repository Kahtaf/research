# Fitted sensor applied timing and crop boundary

Question: how do the exact selected OV5670/OV2680 public feature, shutter and dummy bodies apply state-only frame timing, and how far do public crop/grab coordinates reach toward MT8163 ISP programming?

Status: completed source-evidence unit. Three new unchanged production bodies, eight reused dependencies, 134 timing sequences, 646 stage observations and 14 crop/grab cases pass. Main ov5670mipiraw / sub ov2680mipiraw; never OV2680B. No Android metadata, camera enablement or hardware qualification.

Important outputs:

- `report/REPORT.md`: results, exact source hashes/lines, resource policy and continuation boundary.
- `evidence/exact-source-receipts.json`: concise function, source and fragment pins.
- `evidence/applied-timing-crop.json`: byte/source provenance, software versus applied timing, unknown crop bytes and distinct coordinate stages; select fields when reading this 7 MB ledger.
- `evidence/public-path-boundaries.json` and `missing-source-abi-contract.json`: public ioctl/ISP endpoints, exact payload issues, local source search and the smallest missing userspace contracts.
- `evidence/verification.json`, per-sensor traces/build/import receipts, `full-run.json`: behavioral and resource evidence. Failed fixture/compiler evidence is preserved.

Continue/reproduce: run `python3 scripts/run.py` here. Python standard library and installed clang only. The runner rejects changed pinned parent evidence/public sources. All compilation/execution is serial and uses explicit stubbed register-write callbacks, <=1 GiB observed RSS gate on Darwin (hard address-space cap where supported), CPU 30s/zero cores. Earlier mode programs are consumed as accepted trace seeds, not executed or retested. Full drivers/feature dispatch, sensor transport and ISP transport never compile.

Next: obtain locally reviewable public fitted userspace request/3A-to-feature and crop/grab-to-ISP builder source or exact documented ABIs; resolve payload widths/nested-pointer marshalling, then build a host-only adapter witness. No network, device, ADB, sensor reads, probe/open/OTP, hardware transport, private data or active source-tree edits are permitted. See the report before continuing.
