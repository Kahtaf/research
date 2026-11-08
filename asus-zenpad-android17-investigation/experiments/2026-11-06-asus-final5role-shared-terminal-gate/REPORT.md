# Exact shared terminal gate implementation

Implemented the proposed three-file source delta in this new owned spike.
**114 bounded host integration cases pass. This establishes software gate
behavior under NONDEPLOYABLE fixture bindings only.** There is no actual
five-role install admission or deployable candidate.

Read the corrected CONTRACT.md and WORK_AND_ACCEPTANCE.md, the independent
design review, and the actual frozen stock-only source context before editing.
Their exact captured bytes are in `inputs/design/`. The separate DATA policy
correction and its ongoing independent review are outside this implementation;
neither was changed, reviewed, integrated, or accepted here.

## Source delta and pins

`terminal-profile.patch` is byte-identical to the supplied proposal: 2,049 bytes,
SHA256 `1784ffb48df5063336c122ff9c8049a962c07522ce28c09482dd39f96e2b93e5`.
The runner applies its hunks to exact preimages in memory and checks the result
against the copied source. Only these three production files differ:

| File | Preimage SHA256 | Postimage SHA256 |
| --- | --- | --- |
| handoff.h | `7281fcf20343f8e6fbd95fa70c73b0c753f42f91e7230fc84014f02ee68af908` | `852d3ded867fd54cb3b6508352d2fa048cdbb88861efc71b64af57bf8182ef2f` |
| p10_restore.c | `cddda42708f1444b7d773d57cb7e750a8a34d32e7a78b2c791a096a0a420b943` | `1471d9f0d4088223363db96f7f289444301d02201e40e68460c40a1eb2e23e02` |
| terminal_profile.h | absent | `7e98cb5b9f9b9baf172b7350eb79cb4ce8fd80d6f8da5a108cb19ae1a54df9d1` |

The shared predicate requires `image_count==5` and equality of all 32 manifest
digest bytes with `terminal_manifest_sha`. Both `p10_handoff()` and
`main_restore()` call it. The helper reloads and parses its manifest at startup.
The daemon retains `uncertain_image!=-1`, then identity, `verify_image(0)`,
`verify_image(1)`, before descriptor changes and exec. The helper retains its
authority/no-swap gates, manifest gate, read-only self load, identity and both
original-image proofs before even its read-only p10 open.

`rescue.c` remains exactly
`23b0af1a8c813ae925459bf4614f768a5f90e5a76efb49bf8523135159c72c49`.
No parser, opcode, session state, prerequisite, role authorization, fixed writer,
host protocol, policy, phase proof, packaging script or approval flag changed.
There is no count range, two-or-five fallback or runtime digest input.

**`source/terminal_manifest_binding.h` is intentionally absent.** Both separate
production inclusion contexts fail native preprocessing with that exact missing
header, exit 1; compiler stderr is retained. No target compilation was attempted.
The same mandatory include prevents a real target build from proceeding until
the parent supplies the real binding. The copied frozen `core_binding.h` and
`stock_binding.h` are unchanged context, not final-five-role bindings. No new
production binding or manifest generator is supplied.

## Production-path host evidence

Authoritative run: `evidence/run-20261106-192903/`. `cases.json` preserves each
result, return code, fixture pin, syscall order trace and actual successful
original-image read byte counts. `commands.json` records exact argv, stdout,
stderr, exit status and resource observations. `summary.json` records scope.

The harness includes the copied production files verbatim. It never replaces
`load_manifest`, `session`, `p10_handoff`, `main_restore`, `identity`,
`verify_image`, `fd_hash`, the shared predicate or SHA implementations.
The modeled boundaries are path redirection to owned ordinary files, authority
syscalls, virtual FD duplication, exec, Linux/Darwin declarations and the final
read-only p10 open stop. Self-file owner/mode checks see modeled root metadata;
the bytes are an ordinary synthetic file mapped by the real `mmap` call.
Every production writable open/pwrite traps and aborts the test.

- **58 full-geometry cases:** 29 inputs through both real gate paths. The parser
  is compiled without RESCUE_TEST, preserving actual geometry and hard-coded
  original BOOT/GPT pins. The synthetic five-role fixture preserves the exact
  frozen original prefix and records; its appended records have explicitly
  synthetic nonzero hashes. It is 576,340 bytes and is not an actual manifest
  admission. Valid fixture five-role reaches daemon identity and helper self
  load stop markers. Frozen two-role, zero, four, six, one and three counts;
  bad magic/version; short header/record/chunk table; oversized file; trailing
  byte; missing DATA record; wrong role/partition/size/chunk count; altered BOOT
  or GPT pins; and parseable altered CID/original SYSTEM/original chunk table/
  install whole hash/install chunk table/DATA hashes all refuse appropriately.
  In particular, generic parsing can accept changed original SYSTEM or tables,
  while both exact-profile gates refuse their changed manifest digest. There
  are no full-size partition files or multi-gigabyte proof reads in this mode.
- **42 file-backed integration cases:** use the existing RESCUE_TEST geometry,
  retaining actual identity, validation and whole-image hash bodies. Small
  SYSTEM is 3,146,240 bytes; BOOT is 2,097,664 bytes, each with a 512-byte tail.
  The successful fixture path reads exactly each entire file on **each side**:
  daemon `[3146240,2097664]`, helper `[3146240,2097664]`. Trace order is identity,
  SYSTEM, BOOT, descriptor copies/duplications, exec, helper authority/swaps,
  fresh manifest parse, self load, identity, SYSTEM, BOOT, read-only p10 stop.
  Helper return 86 is the intentional stop; no restoration succeeded or ran.
  No DATA device exists, and install roles are never proved by this terminal
  path. This verifies that used/unavailable DATA is not a terminal prerequisite.
  Both-installed and only-SYSTEM-restored fixtures refuse. Head/tail corruption
  of either original file refuses before daemon exec; changing either tail
  between exec boundaries causes helper return 85 before p10 access. Both
  sides exercise short-read/I/O and identity failures. Uncertainty 0, 4 and -2
  refuses before identity/proof/descriptor work. Helper UID/EUID/domain/
  Enforcing/peer UID/peer domain/lock failures return 77; swap, manifest removal
  and changed-profile-after-exec cases return 84. Descriptor-copy failures at
  all three positions return without exec; dup2 failures and exec failure exit
  terminally with 74. Actual session RECONCILED state, nonempty 0x30 and another
  opcode refuse handoff. A second queued 0x30 remains unconsumed.
- **14 separate-compilation cases:** independent daemon-only translation units
  include production rescue.c with P10_HANDOFF; independent helper-only units
  include production p10_restore.c without P10_HANDOFF. Both full and small
  builds consume the same single fixture binding header for their geometry.
  Exact, different-digest and malformed inputs, plus actual frozen two-role
  input in full geometry, verify both entry contexts independently. The
  combined harness additionally resets manifest globals at modeled exec and
  runs the real helper startup, allowing between-boundary mutations.

All 114 cases observed zero production writable opens and zero production
pwrite calls. Daemon refusals before exec observed zero execs. Helper refusals
after the daemon's modeled exec observed no p10 access/writer. Deliberate
harness mutations open only owned fixture files and are separate from these
production counters. FD/peer/SELinux/exec models establish caller order and
failure handling; they do not establish real authority, lock or FD survival.
No core/container/restoration protocol/physical durability test is claimed.

## Toolchain, bounds, and retained failure

Native host only: Darwin 25.6.0 arm64; Apple clang 21.0.0
`clang-2100.1.1.101`; macOS SDK 26.5. Outputs are native host Mach-O tests,
not Android ARM64/ELF binaries. Common flags are `-std=c11 -O1 -Wall -Wextra
-Werror -Wno-unused-function -Wno-misleading-indentation`, with test-only
include directories and variant defines recorded per command.

`toolchain.json` records executable hashes and driver identity. Actual clang
SHA256 is `1220c0afafa12a6ae599d097ee7cf8b87c6b4d8e3fbb9783cee6b319a80683ba`;
actual linker SHA256 is
`765e5fa4e30980ddf2803c8a973b20fcc63e403098d2dd9b6cefa38e0cde3c2e`.
Python 3.13.14 executable SHA256 is
`95f75211f35794aa6726febff884339a88756fd89e423a4fbd65aac201145780`.
`compiled-input-pins.json` records all 211 compiler-listed source/header
dependencies, including SDK headers and the two isolated test bindings.
`test-input-pins.json` and `native-product-pins.json` bind the exact runner,
harness, compatibility headers and six native test executables. The driver
trace records actual cc1/linker arguments. Compiler temporary output in the
final run is directed to that run's NONDEPLOYABLE/tmp directory.

Compilation and cases run sequentially, one compiler/test invocation at a time,
with thread environment settings 1. Each child has a 10-second CPU-time hard
limit, no core dumps and a 32-MiB file-size limit. Commands have at most 20
seconds wall time; individual tests have 5 seconds. The runner checks a
300-second overall deadline at launch/poll points and has finite input/case
counts. Sampled process-group RSS above 1 GiB triggers termination.

Darwin rejected RLIMIT_AS, RLIMIT_DATA and RLIMIT_RSS with `current limit exceeds
maximum limit`; `sched_setaffinity` is unavailable. **No hard one-core affinity,
hard 1-GiB address-space/RSS envelope, cgroup isolation, or hard whole-run
wall-clock isolation is claimed.** Single-thread intent/serial execution and a
sampled memory kill backstop are the available controls. Sampling can miss
short peaks. Final observed sampled group peak was 82,116,608 bytes; child
high-water RSS was 71,008,256 bytes; runner high-water RSS was 373,735,424 bytes.
These are envelope observations, not performance or physical timing evidence.

Retained earlier runs: initial 100-case pass `run-20261106-192625`; a rerun
`run-20261106-192713` failed at fixture setup with FileExistsError on an existing
boot-alias symlink after 58 full-geometry cases. Its FAILED.json and raw logs
are preserved. The runner was corrected to allocate new run-specific fixtures,
bindings and binaries; `run-20261106-192749` passed 114 cases. The final rerun
adds complete compiler-dependency/product pins and owned temporary output.
Expected missing-header compiler failures are preserved in every relevant run.
A separate local `ld -help` metadata probe returned `unknown options: -help`
(exit 1); it was not used for a compile or an acceptance result.

## Input preservation

`evidence/input-before.json` and final `input-after.json` match exactly: all 64
named public inputs, including the original SOURCE_PINS entries and captured
design inputs. All copied C/header preimages are in `baseline/`; complete
lengths and before/after hashes are in `source-prepost.json`. The original
SOURCE_PINS.json is copied unchanged, separate from new postimage pins.

Frozen compact image remains
`5a61d3d65a7ba6b29745a965d9911ab4483c951a0327339839a0541bcb9ab30f`;
streaming its documented zero padding into SHA256 still gives whole-p10
`3f99c785cca60bf56c2505711e2d26b72623daf28180515d44c5ba2abf03a44a`.
No padded image was created. Frozen policy remains
`16f6ce7f25c1b56aba9e4179573c49a6c55f9b9fe3f18336029f6d83b5b4b2c2`.
Frozen original manifest remains 115,288 bytes,
`605cdec038dafe3dddabfe92b8bd6cd189734f740230dfc362d02a43421e4e47`.
These hashes preserve historical identities; none authorizes an install role.

All work was local/offline and self-performed. No network, SSH, VM, cloud,
device, ADB, USB, elevated execution, private factory payload, key, AOSP/out,
existing source/artifact mutation, target build or image/core/container
generation occurred. Only isolated synthetic host-test manifests/bindings were
generated. No deployment package or approval/timing flag was produced.

## Parent continuation and remaining gates

1. Create a separately owned final fork from these exact frozen preimages.
   Check the three preimage identities above; apply only
   `terminal-profile.patch`. Verify all three postimage hashes and unchanged
   rescue.c/core/writer/host code. Do not copy NONDEPLOYABLE bindings, fixtures,
   executables, compatibility headers or frozen core bindings as final inputs.
2. Obtain the genuinely missing qualified full-build install SYSTEM/BOOT
   whole/chunk/metadata/provenance/admission records, build/kernel qualification
   and explicit DATA-with-this-build qualification. Fixture, stock, recovery
   probe and zero pins cannot substitute. Independently admit fixed source
   profiles before using them; no runtime arbitrary-path/hash override follows.
3. Implement/review the parent's fail-closed real generator separately, using
   the corrected contract. Prove frozen manifest hash/length; preserve bytes
   0–11, 16–111 and 112–115287 exactly; change only count to 5 and append the
   actual admitted canonical records. Validate exact end/length 576340 and all
   admitted source tables/hashes, then hash those actual bytes and emit one
   `static const unsigned char terminal_manifest_sha[32]` binding. Require that
   same generated header in both real daemon and helper builds. Emit nothing
   on admission failure. This spike intentionally cannot perform that step.
4. Resolve the separately implemented policy correction through its own
   independent review and acceptance. This source gate supplies no policy
   acceptance. Under the parent's later scope, compile the daemon with the
   actual terminal binding; assemble the new exact manifest/daemon/accepted
   policy core; derive the actual new core binding; compile the helper with
   both real bindings; only then derive capsule/image/full-p10 and external
   helper/host pins. These are instructions for pending parent work, not
   artifacts or actions supplied here. Re-establish fit, independent parsing,
   source inventory and reproducibility; do not reuse 5a61/3f99 or old helper
   pins for the changed final profile.
5. Independently review this patch and tests. Later real-bindings/core/helper/
   container/host fault tests and exact final policy/domain/lock/writer-graph
   checks remain pending. The original-pair proofs must run fresh before exec
   and again in the helper; no cache/proof optimization was adopted.
6. Physical original commissioning, final five-role runtime, real SELinux/FD/
   lock/exclusivity/I/O/durability and timing, independent direct recovery entry
   and fallback, genuine A17 use and post-A17 OEM reset/FDE/two-boot/factory
   acceptance remain missing. All full-OS, flashing, restoration execution,
   reset, physical approval and GO decisions remain with the parent.

Reproduce only these host software tests from this spike with
`PYTHONDONTWRITEBYTECODE=1 python3 scripts/run_tests.py`. It writes a new
NONDEPLOYABLE run and evidence directory, preserves previous runs, checks the
original pins, and intentionally expects both missing-header compiler failures.
