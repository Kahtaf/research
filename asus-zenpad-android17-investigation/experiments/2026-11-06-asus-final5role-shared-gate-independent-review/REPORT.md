# Independent review of the shared final-five-role terminal gate

## Findings first

**No blocking implementation defect found in the bounded three-file gate delta.**
The exact source proposal is implemented, both callers use the shared count-5
and full 32-byte digest predicate, and the helper freshly parses and checks its
manifest after modeled exec. The original 114 cases reproduce successfully in
this owned spike. An additional **56 adversarial cases pass**, with zero
production writable opens or pwrites. This is a local software review under
synthetic bindings and syscall models, not final integration or physical approval.

Two nonblocking coverage gaps in the original 114-case suite were closed in
the independent harness. Neither required a production-source fix:

1. **Incomplete rejection coverage after daemon admission.** The original suite
   changes one digest byte and removes the manifest after exec, but does not
   then replace it with parseable zero/two/four-role profiles, or separately
   change original BOOT/SYSTEM full hashes and tables. Reproduce with
   `scripts/run_adversarial.py`; see `adversarial-x_manifest_two`,
   `adversarial-x_manifest_system_full`, and the other `x_manifest_*` rows in
   `evidence/run-20261106-193614/cases.json`. Each first completes the real
   daemon original-pair proofs and descriptor path, then changes owned fixture
   bytes at modeled exec. The production helper returns 84 before self load,
   identity, original proofs or p10 access. Malformed magic, count six,
   truncation and trailing bytes also return 84. **Smallest follow-up:** carry
   these cross-boundary tests into a future authorized test fork; retain the
   current helper parse/predicate sequence.
2. **Self-file and authority failure ordering was under-tested.** The original
   harness always supplies acceptable self-file metadata and a real successful
   read-only mapping. Its peer/lock negatives cover selected errors rather than
   malformed returned lengths and lock address fields. Reproduce the same
   script and inspect `adversarial-h_self_mode`, `adversarial-h_self_mmap`,
   `adversarial-h_peercred_short` and `adversarial-h_lock_long`. The actual
   helper rejects authority errors with 77 before swaps/manifest/self work;
   self-load errors return 85 before helper identity or proofs. There is no
   p10 open. **Smallest follow-up:** retain these syscall-fault regressions;
   no relaxation or additional production guard is indicated by these results.

These are evidence improvements, not claims that the previous harness replaced
the gate logic. I inspected its actual source: it includes production parser,
session, both gates, identity, image proofs and hash implementations unchanged.

## Exact reviewed source and integrity

Read the implementation REPORT.md, terminal-profile.patch, final run
source-prepost.json, actual copied C/headers, 114-case runner and harness,
compiled-input/test-input/native-product pins and corrected design CONTRACT.md.
The captured contract equals the current corrected contract byte for byte.
The earlier captured design review is historical context; its policy hold is
not a new finding here. Per the supplied scope, DATA policy `3d982859...` has
separate parent offline acceptance in
`2026-11-06-asus-android17-orchestration/evidence/parent-data-policy-scoped-acceptance.json`.
I did not re-review or integrate that policy.

`evidence/pin-verification.json` records successful rehashing of all **932**
named implementation/source/evidence inputs, all **211** original recorded
compiler dependencies, six native products and six test inputs. All 13
pre/post rows match the actual files. Every copied baseline C/header equals its
counterpart in the frozen stock-only spike. The only source differences are:

- `handoff.h`: preimage `7281fcf20343f8e6fbd95fa70c73b0c753f42f91e7230fc84014f02ee68af908`,
  postimage `852d3ded867fd54cb3b6508352d2fa048cdbb88861efc71b64af57bf8182ef2f`.
- `p10_restore.c`: preimage `cddda42708f1444b7d773d57cb7e750a8a34d32e7a78b2c791a096a0a420b943`,
  postimage `1471d9f0d4088223363db96f7f289444301d02201e40e68460c40a1eb2e23e02`.
- New `terminal_profile.h`: 367 bytes,
  `7e98cb5b9f9b9baf172b7350eb79cb4ce8fd80d6f8da5a108cb19ae1a54df9d1`.

The 2,049-byte patch equals the corrected design proposal exactly:
`1784ffb48df5063336c122ff9c8049a962c07522ce28c09482dd39f96e2b93e5`.
The reproduced runner applies its hunks to preimages in memory and checks all
postimages. `rescue.c` remains
`23b0af1a8c813ae925459bf4614f768a5f90e5a76efb49bf8523135159c72c49`;
restore core, prior-container parser, policy source and SHA bodies are unchanged.

The frozen public-input inventory still matches the original before/after
receipts. Frozen compact image SHA256 remains
`5a61d3d65a7ba6b29745a965d9911ab4483c951a0327339839a0541bcb9ab30f`;
hashing its existing bytes and zero padding in memory gives full-p10
`3f99c785cca60bf56c2505711e2d26b72623daf28180515d44c5ba2abf03a44a`.
Frozen policy remains `16f6ce7f25c1b56aba9e4179573c49a6c55f9b9fe3f18336029f6d83b5b4b2c2`.
Frozen two-role manifest remains 115,288 bytes,
`605cdec038dafe3dddabfe92b8bd6cd189734f740230dfc362d02a43421e4e47`.
No padded image was written. Existing source, artifacts and evidence are unchanged;
`review-input-before.json` equals `review-input-after.json`.

## Gate and caller assessment

`source/terminal_profile.h:7` requires exactly `image_count==5` and
`memcmp(manifest_id,terminal_manifest_sha,32)==0`. There is no two-or-five
fallback, range, environment/config override or runtime expected-digest input.
The required generated header is absent from both production source copies.
The reproduced daemon-only and helper-only compilation contexts both fail
native syntax checking with the exact missing-header diagnostic. No target
build was attempted.

The compiler dependency lists independently establish that daemon-only and
helper-only builds consume the same single fixture header for each geometry,
along with the same shared predicate. The first and last expected digest bytes
were independently changed in separate, deliberately wrong test bindings.
Both real callers reject both variants before identity/proof/descriptor or
self-file work, although the actual manifest parses successfully. This checks
caller coverage as well as the predicate; it is supplemental to the complete
startup and cross-boundary tests.

`source/rescue.c:115` permits empty opcode 0x30 only in session IDLE.
The unchanged `p10_handoff()` requires uncertainty exactly -1, then identity
and full original SYSTEM and BOOT verification before any descriptor copies
or exec. The original suite covers RECONCILED, malformed/opcode requests,
uncertainty 0/4/-2, all copy/dup positions and exec failure. The extension adds
INT32_MIN and INT32_MAX uncertainty; both stop before identity and copies.
No second queued terminal request is consumed after handoff.

`source/p10_restore.c:83` retains UID/EUID0, exact helper domain, Enforcing,
authenticated peer and inherited-lock checks. Empty swap precedes fresh
manifest load and the exact shared predicate. A regular, one-link, root-owned,
0700 self file with bounded size must load through read-only MAP_PRIVATE mmap.
Only then do identity and both full original proofs execute, before the first
read-only p10 open. Original-pair proof calls are neither cached nor replaced.
The successful small fixture reads exactly 3,146,240 SYSTEM bytes and 2,097,664
BOOT bytes on each side. Its final 512-byte tails are included. Original
head/tail mutations between daemon and helper are detected by the helper;
SYSTEM failure prevents the BOOT proof. Installed pair or only-restored SYSTEM
does not qualify. Used or absent DATA is not a terminal prerequisite, and no
install-role proof replaces either original proof.

The production parser still accepts generic 0/2/4/5-role shapes and independently
pins original BOOT/GPT in full geometry. It intentionally does not independently
hard-pin original SYSTEM or its chunk table. Exact terminal digest checks cover
changes to those fields in both callers. Preservation of frozen original bytes
0–11, 16–111 and 112–115287 remains a **future generator admission gate**;
this review does not add a new runtime SYSTEM pin. The full-size synthetic
fixture preserves those bytes and appends three synthetic records, producing
576,340 bytes. That demonstrates layout, not actual install admission.

## Test evidence and honest model limits

Reproduced original suite: `evidence/run-20261106-193356/`, **114 cases**:
58 full-geometry parser/profile cases, 42 small file-backed integration cases,
14 separate-caller compilation cases, plus the two expected missing-binding
compiler failures. This retains the original runner and original harness bytes.

Independent extension: `evidence/run-20261106-193614/`, **56 cases**:
50 modeled cross-boundary runs including one successful entry control,
two extra uncertainty cases and four separate-caller digest-byte cases.
It adds 16 manifest replacement/mutation cases; ten malformed peer/lock
results; three swap failures; eleven self-load failures; and nine original
proof/identity/geometry/mount/holder/alias failures after daemon admission.
The original and extension totals are **170 passing cases**. Compiler-negative
checks are not added to that case count. Every case observes zero production
writable opens and pwrites; every negative extension case stops before p10.

`NONDEPLOYABLE/tests/adversarial.c` is derived from the preserved original
harness by `scripts/extend_harness.py`. Only syscall models, fixture mutations,
test input setup and observation counters change. Neither harness defines a
replacement production parser, session, gate, identity, verify_image, fd_hash,
SHA or restoration body. The extension adds mmap interposition solely to
observe/fail the self-file mapping syscall; the successful mapping is real.
Self metadata and authority results remain explicit models.

All host files are ordinary owned fixtures. RESCUE_TEST uses the production
small geometry, skips production BOOT/GPT fixed pins, accepts regular-file
geometry instead of block devices and omits direct I/O. Its proof/hash bodies
and sysfs/alias/mount/holder checks still execute. Full geometry compiles without
RESCUE_TEST and retains actual parser geometry and pins, but deliberately stops
at daemon identity or helper self open. It performs no multi-gigabyte original
proof reads. These modes complement each other; neither is a real-device proof.

Exec/FD duplication/peer/lock/root/SELinux are modeled. Combined modeled exec
resets manifest globals and invokes actual helper startup, but does not prove
a Linux exec transition, CLOEXEC/FD survival or open-file-description identity.
Separate translation units cover the independent inclusion contexts. Harness
fixture mutations use unwrapped syscalls and are deliberately separate from
production writer counters. All production writable opens/pwrites trap; the
successful entry control stops at the first read-only p10 open with return 86.
No p10 restoration, staging, container admission, protocol completion or full
reachable-writer graph is tested. A hash detects bytes it actually reads; these
tests do not establish exclusion of a concurrent real writer or mutation after
the relevant final read.

## Toolchain and execution bounds

Native Darwin 25.6.0 arm64, Apple clang 21.0.0 `clang-2100.1.1.101`, SDK 26.5,
Python 3.13.14. Products are host Mach-O test executables. Recorded tool hashes
match the actual local compiler driver, compiler, linker and Python. The
replicated run has 211 pinned dependencies and six products; the extension has
212 dependencies and five products. Each run retains commands, flags, stdout,
stderr, case traces, toolchain/test/product/dependency pins and limit probes.

Compilation/tests run sequentially, one invocation at a time, with thread
settings 1. Each child has a hard 10-second CPU limit, core limit zero and
32-MiB output-file limit. Compilation wall limit is 20 seconds; tests are five
seconds. The runner checks a 300-second overall deadline at launch/poll points
and kills sampled process-group RSS above 1 GiB. Darwin rejects AS/DATA/RSS
hard caps and lacks sched_setaffinity: **no hard one-CPU affinity, hard 1-GiB
memory envelope, cgroup or hard whole-run wall isolation is claimed**. Sampling
can miss peaks. Highest sampled child-group RSS in the reproduced suite is
83,820,544 bytes; the extension records 78,774,272. Runner high-water RSS is
357,203,968 and 329,924,608 bytes respectively. These describe observed resource
use, not target performance or physical timing qualification.

The test runs have no failed cases. During review-tool preparation, the
preservation verifier initially looked for the original after-inventory in the
wrong directory, then compared unnormalized dependency paths; these verifier
assertions were corrected to the authoritative run directory and resolved
dependency paths. Final verification passes. No existing input changed.

## Remaining real-input and runtime boundaries

Actual qualified full install SYSTEM/BOOT admissions remain absent. A real
five-role manifest/digest and generator, shared production binding, new daemon,
accepted-policy core and core binding, helper, canonical container and external
full-p10/helper pins are not supplied. Fit, exact source inventory, reproduction,
final policy application and full reachable-writer exclusion still need their
own evidence. Synthetic fixtures, copied frozen core bindings and Mach-O tests
cannot satisfy any of those inputs. Separate parent DATA-policy acceptance does
not create those artifacts or establish physical behavior.

Real SELinux transition, FD/lock/exclusivity, direct I/O, durability, full-size
proof timing, independent direct recovery entry/fallback, genuine Android 17
use, post-A17 OEM reset/FDE/two-boot and parent factory acceptance remain open.
No deadline/proof optimization or approval flag was changed. No physical or
flash GO follows from this review.

All work was public, local, offline and self-performed with no subagents.
Writes are confined to this new dated spike. No network, SSH, VM, cloud,
device/ADB/USB, elevated execution, private factory material, keys, AOSP/out,
existing source mutation, target compilation, packaging, image generation,
production binding/manifest/header generation or approval flags were used.
Only clearly NONDEPLOYABLE host fixture manifests/bindings were created.

## Reproduction and continuation

From this spike, run sequentially:

```sh
PYTHONDONTWRITEBYTECODE=1 python3 scripts/run_tests.py
PYTHONDONTWRITEBYTECODE=1 python3 scripts/extend_harness.py
PYTHONDONTWRITEBYTECODE=1 python3 scripts/run_adversarial.py
PYTHONDONTWRITEBYTECODE=1 python3 scripts/verify_preservation.py
```

Each suite creates a timestamped owned evidence/fixture run; the preservation
verifier checks the authoritative retained runs named above and original inputs.
Do not launch suites in parallel or within the same timestamp second.
The only proposed continuation from this review is to retain the added test
coverage in a later authorized fork and preserve the current gate ordering.
Any real-input generation, integration or physical work requires its separate
parent scope and evidence.
