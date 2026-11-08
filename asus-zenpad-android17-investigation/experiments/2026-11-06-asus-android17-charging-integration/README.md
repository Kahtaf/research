# Android 17 checked charging integration

Question: can the checked MT6323/OAM samples drive the BQ25896 charging policy
with fresh measurements, honest readback and a functional runtime charging path?

Status: offline implementation and host/source verification complete; staged for
parent review. Target compilation and physical qualification remain outstanding.
The first new-kernel test stays inhibited; no DT charging permission was added.

Important outputs:

- [REPORT](REPORT.md): changes, actual tests, remaining physical/daily-use gates.
- [Patch](patches/0003-asus-p00a-checked-charging-integration.patch): 11 files,
  strictly after the frozen measurement 0001 and SOC 0002 prerequisites.
- `source/`: frozen base, after-SOC subset, prerequisites and primary references.
- `staged/`: exact changed/new production files; `tests/`: host harnesses.
- `evidence/`: tested-source hashes, strict replay, deterministic patch and logs.
- [Parent build instructions](integration/APPLY-AND-BUILD.md),
  [lock/caller audit](integration/LOCKS-AND-CALLERS.md),
  [commissioning plan](integration/COMMISSIONING.md), [provenance](PROVENANCE.md).

Continuation: read REPORT, replay `scripts/check_host.py` and
`scripts/verify_source.py`, then review/compile under the exclusive full-build
owner. Resolve overlapping edits through reviewed rebasing. Parent owns all
physical operations and any later permission change. No previous spike, full
candidate, VM source, device, data or cloud resource was modified here.
