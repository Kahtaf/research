# Verify the staged SD source bytes in normal Android

Question: do the actual installation and stock fallback files on the tablet's
microSD match the parent-admitted chunk table?

Status: actual source byte observation passed on stock boot c328c9b4-fdaf-4b36-b3e0-5b36c13b3885. This does not install anything,
mount a filesystem, open a block device, create execution controls, or replace
the recovery installer's own source checks. The verifier reads fixed SD paths
through Android's existing filesystem view. It checks every present chunk and
allows an omitted chunk only when the admitted digest is the digest of exactly
that many zero bytes. It also verifies the original recovery source and both
bundle manifest bindings. Whole image/chunk coherence comes from the existing
exact parent-admitted manifest; whole logical images are not rehashed here.

Only code and the existing SHA implementation may be sent to the compiler VM.
The private manifest stays on this Mac and its owner's tablet. Device staging
is a new private shell directory; generated outputs stay in this spike.

Continuation: inspect the final device receipt. A successful observation proves
the source files read on that boot, not future card stability, recovery policy,
Linux 4.9 startup, or a successful Android 17 installation.

## Actual observation

All 5,409 present source files (5,687,439,360 bytes) matched, including original recovery. All 12,591 omitted chunks matched exact-length zero digests in the admitted manifest. Target verifier exited0 with its fresh host nonce. The original host driver exited1 after a subsequent WiFi cleanup query timed out; this failure is preserved. A fresh USB read confirmed the same healthy boot/card and that the small staging directory remains. Receipt: `evidence/device.json`; actual target log: `evidence/device.log`. No source check was repeated, no card/internal partition was written, and no root was used. The updated launcher now records this postcheck/cleanup uncertainty explicitly if reused in a separately reviewed run.

After the subsequent known recovery control returned, parent reconciled the retained staging directory under fresh new-boot and exact owned-file metadata guards, removed only its three known files and empty directory, and verified absence. Original cleanup timeout remains in the receipt; no source reader was restarted.
