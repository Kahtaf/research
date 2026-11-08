# Parent handoff — verified artifact, blocked r9 preparation

R9 kit: `/srv/android/asus-reviewed-build-kit/r9`.
VM-only exact APK: `/srv/android/asus-product-integration-staging/r9/webview.apk`.
Owned fixtures: `/srv/android/asus-reviewed-build-kit/r9-fixtures`.
Seal is recorded in `kit-seal.json` beside this document. This is an immutable preparation seal, not launch eligibility.

The actual WebView blocker is cleared in staging: exact 260835655-byte OID `1d2f61832b2596b0046cb82cf3634609ea866098d097a83fac27c35272ac726a`, obtained from the pinned official LineageOS LFS endpoint. Genuine failed-command fixture passes on that payload and fails on the preserved pointer. Read `REPORT.md`, `inputs/webview-origin.json`, `evidence/artifact-check.json` and `source/scripts-from-r8.patch`.

## Concrete read-only parent commands

Run on the existing VM after independently comparing `kit-seal.json` to the externally reported seal:

```sh
cd /srv/android/asus-reviewed-build-kit/r9
python3 -B - <<'PY'
from pathlib import Path
import sys,json
sys.path.insert(0,'scripts')
from integrate import verify_pins
from artifact import admit
seal=verify_pins(Path.cwd())
assert seal == json.loads(Path('kit-seal.json').read_text())['kit_pins_sha256']
print(seal)
print(admit('/srv/android/asus-product-integration-staging/r9/webview.apk'))
PY
python3 -B scripts/integrate.py --audit-inputs
```

The audit is read-only and does not inspect processes or acquire the lifecycle lock. It establishes source/preimage/receipt integrity, not launch eligibility. The source pointer remains active until parent integration.

To inspect the original r8 failure under the parent's original lock discipline, only the parent may run:

```sh
cd /srv/android/asus-reviewed-build-kit/r9
python3 -B scripts/integrate.py --describe-prior
```

`inputs/r8-unapproved-description.json` is a descriptive worker snapshot; it is **not** a parent acceptance and must never be treated as one. Parent authors its own exact hash-bound review under this kit's `parent-review/` only after actual review. No acceptance file was created by this worker.

## Required continuation before launch

This sealed kit intentionally refuses PLAN_ONLY/PARENT_EXECUTE with `CACHE_LINEAGE_INCOMPLETE` **before** lock acquisition, process inspection, attempt creation or source mutation. Do not invoke build.sh, remove the gate, reseal in place, touch sources, clean outputs, alter Ninja history or blanket-relax timestamps.

Resolve and independently review the exact remaining association in CACHE-PROVENANCE-GAP.md. The current Siso output records now join the frozen r8 completed commands/metrics; the unresolved issue is the consumed transitive input content identity. The PublicVolume dependency record binds 1032 paths and an exact output mtime but not consumed content hashes. Local action digests are absent. Do not manufacture missing Ninja rows or label a newly hashed current input snapshot as a historical execution preimage. Further authoritative evidence and a complete reviewed cache extension are required before affirmative parent launch commands become valid.

The exact WebView INPUT ONLY was independently frozen at `/srv/android/asus-reviewed-build-kit/r9-webview-input-milestone-v1` and parent-accepted. Its pins manifest is `3e6ca30a3074cdd7f19dd522111c52fadbfdb311a3aa16fd23563c9011e35437`. That acceptance is separate from r9/cache/launch; the milestone and payload remain unchanged. The obsolete inventory reader has been stopped under the subsequent narrow authorization; see evidence/cleanup-summary.json.

Any eventual executable continuation must retain the exact single artifact source delta, original continuous flock/FD/inode/ancestry/no-other-native-jobs/nonblocking/one-shot protections, actual r8 failure acceptance, genuine post-delta product dumpvars/config and every inherited final validator. No native full build, integration, kit-specific parent acceptance or physical action was performed here. The separately owned final SYSTEM/kernel mount qualification remains outside this kit.
