# Shared exact final-five-role terminal gate

Question: does the proposed three-file gate preserve production parser, daemon
handoff, helper startup, and fresh original-pair proof ordering?

Status: implemented the exact three-file proposal; 114 bounded offline host
integration cases pass. Success proves software gate behavior under synthetic
fixture bindings only. Darwin hard one-core/1-GiB isolation is not claimed.
No actual install admission, production terminal binding, target build, policy
acceptance, packaging, physical acceptance, or GO is supplied.

Outputs: `source/` is a copied production fork; `baseline/` contains exact
preimages. `inputs/design/` preserves the corrected contract and independent
review. All synthetic bindings, manifests and host executables belong only in
`NONDEPLOYABLE/`. The production `terminal_manifest_binding.h` is absent.

Review `terminal-profile.patch` and `REPORT.md`. Final receipts and exact
source/toolchain/test/product pins are in `evidence/run-20261106-192903/`.
Earlier passing and failed runs are retained. Both production inclusion
contexts fail compilation without the deliberately absent binding header.

Reproduce host tests only:

```sh
PYTHONDONTWRITEBYTECODE=1 python3 scripts/run_tests.py
```

Do not rerun `scripts/freeze.py`: it is the initial capture and refuses existing
output. Do not copy fixture bindings into a target build. Parent must supply
actual qualified install SYSTEM/BOOT admissions before real binding generation,
then separately accept policy, final core/helper/container and physical gates.
Precise continuation instructions and limitations are in `REPORT.md`.
