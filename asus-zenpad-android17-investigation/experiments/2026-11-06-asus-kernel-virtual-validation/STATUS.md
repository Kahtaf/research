# Virtual kernel/BPF validation checkpoint

6 November 2026. The user is asleep and instructs us to continue work that does
not require physical access. Leave the ASUS running its stock Android; continue
source, build and virtual testing. Do not reboot it into an unattended recovery
or attempt a hardware flash while physical recovery help is unavailable.

## Verified baseline

Pinned source `be15c78f96d53b5bf2e3a2db0ed272be803518fd` inherits the ASUS
network configuration candidate `de61780979adc3c52068e244aa62ae0369c00527`.
Its only added source change guards the MediaTek GIC polarity hook with
CONFIG_MTK_GIC as well as !CONFIG_MTK_SYSIRQ, allowing a generic ARM64 build.
The hardware candidates were not modified.

The first tiny configuration failed because CPU hotplug helpers were compiled
out and the GICv3 driver referenced the MediaTek hook without its platform guard.
Enabling HOTPLUG_CPU clears the first. ARM64 unconditionally selects GICv3, so
disabling that option did not clear the second; source/Kconfig inspection
established this and the isolated platform guard fixes it. Original failure logs
are retained.

QEMU `virt,gic-version=3`, Cortex-A53, 2 CPUs and 1 GiB RAM boots the generic
kernel and an independent static Linux PID 1. There are no disks, networking or
physical USB devices attached. The bounded run exited 0 through poweroff without
timing out. It created, updated and read an array map, loaded and executed a
socket filter, and received 7 bytes from the submitted 10-byte packet. The JIT
enable sysctl was written; this alone does not establish that the program used
JIT rather than an interpreter fallback.

GET_NEXT_ID for both programs and maps returned EINVAL, confirming those missing
APIs at runtime. This is not Android 17 userspace, an Android 17 networking pass,
or ASUS hardware validation. The full generic test kernel/initramfs must never be
flashed to the tablet.

The baseline checkpoint archive SHA-256 is
`69ba7c6ec8049831c909299141c747b58780b0dde1fe81e3f1d0c5683b0b8231`.
All 21 files verify on the Mac under artifacts/baseline-result. Exact hashes,
configuration, source patch, probe source/binary and complete boot log are there.

## BPF ID API continuation

The donor's original program-ID patch does not apply directly: this MT8163 source
has older tracing, kallsyms, program-auxiliary and map-allocation code. The failed
index-only apply check did not alter a source worktree.

scripts/prepare_bpf_ids.py in the sibling kernel-backport spike adapts three
pinned upstream/donor commits into a separate kernel-ids worktree. Current feature
revision: `34a8afba47785b0ff9dc2a72dade73c945a54a55`. The adaptation keeps
upstream numeric command IDs and CAP_SYS_ADMIN checks, adds ID lifetime handling,
allocates map IDs after successful memlock charging and rolls IDs back on FD
creation failure. TEST_RUN's number is reserved without claiming an implementation.
GET_FD_BY_ID and object-info APIs remain absent.

The IDs virtual configuration enables MULTIUSER; the original tiny baseline had
it disabled and therefore did not test permission enforcement. New tests cover
enumeration, end-of-list, invalid start, unprivileged denial, FD allocation errors,
absence of leaked IDs and final reference release. All eight ID checks and the
basic map/socket-filter tests pass. QEMU powered off cleanly with exit 0.

The verified ID checkpoint archive is
`41578871a554c342b17099ef3f0b0725dee49a99b99d422fdbcef300f59fa416`.
All 20 captured files verify locally in artifacts/ids-result. The captured
kernel is virtual-only and must never be flashed.

The tested BPF patch also builds successfully in a fresh ASUS hardware worktree,
revision `790faa7607c819a5d61425283cb4784bc413b735`. That hardware build omits
the virtual GIC change. scripts/build_bpf_ids_hardware.sh in the backport spike
requires the passing QEMU result before it creates that separate candidate, and
checks that the hardware DTB remains identical. Its configuration matches the
network baseline byte-for-byte, and its three BPF core source files match the
virtual-tested files byte-for-byte. GET_NEXT_ID is present in the linked System.map.

The hardware kernel is 7240481 bytes, SHA-256
`2be9f759041e4baa7af0f43ba0c800769f922b24443a811747db80e90bf54af4`.
All 12 captured hardware checkpoint files verify in the backport spike's
artifacts/linux-bpf-ids/bpf-ids-result directory. This is a kernel-only,
never-booted ASUS candidate, without MTK boot packaging or a full ROM. Charging
remains inhibited.

Next API group: GET_FD_BY_ID and object information, followed by the larger map,
helper, verifier, BTF and memory prerequisites. Preserve the working baseline and
ID runtime checkpoints; do not set a kernel version override to skip real gaps.
The three original follow-up donor patches and their manifest are already saved
on the VM under /srv/android/asus-android17/patches/bpf-followup.

When adding GET_FD_BY_ID, revisit allocation-failure lifetimes: IDs are published
before the creator receives its FD, and another process can then obtain a live
reference by ID. The current ID-only error paths are safe while IDs cannot yield
references; the follow-up donor changes failure cleanup to reference-counted
puts. Do not simply add lookup calls and retain the current direct frees. Test
concurrent reference acquisition and allocation failure, as well as ordinary
lookup, permission and final-release behavior.

Builder: existing labeled VM/disk PROJECT_REDACTED in
PROJECT_REDACTED/us-central1-a. A 12-hour automatic stop remains configured.
Use the existing SSH key/verified host identity; no new cloud resource was created.
# Lookup-by-ID feature checkpoint

The next virtual branch, kernel-fd, now passes both map/program GET_FD_BY_ID
tests. Final virtual revision is `fcb1b6c2de6348e2724981dcd520dec631ed5255`.
It adapts the two donor API additions and includes the later c8a7a85e / 73ccf8d2
fixes to drop map user references on lookup and creator FD-allocation failures.
The original map constructor here takes explicit O_* access flags.

The first run at 83e07819 failed the actual map-write behavior: passing flag 0
created a read-only descriptor. The correction uses O_RDWR. The failed kernel,
initramfs, probe source, patch and boot/result logs are preserved alongside the
passing checkpoint, so the failure is reviewable rather than discarded.

The final run validates lookup persistence after closing the original FD,
actual map read/write and socket-filter execution through looked-up FDs,
invalid IDs/unused fields, unprivileged denial, lookup FD failures and final
reference release. A two-CPU race performs 3000 failed map creations and 3000
failed program loads, all failing with EMFILE as designed. Parent lookups
captured 680 distinct map objects and 1572 program objects; held references
remain usable after the creators fail. These are observed race cases, not a
proof of all concurrent interleavings.

A program-array regression also passes: its tail call returns 9 bytes before
the final user FD closes; after sixteen failed map-FD lookups and closing that
FD, the still-live caller falls back to 7 bytes. This demonstrates that failed
lookups do not leak the user reference that would keep the tail-call slot active.
The previous basic/ID tests also remain green; QEMU exits 0 through poweroff.

The final virtual archive is
`70ebe10017eeca4072a18d394d54e28f7f94ed0cc0057723b7aaaeeb7550f07d`.
All 31 files verify locally in artifacts/fd-result. No ASUS hardware boot or
Android 17 network-stack pass is claimed.

The separate hardware-FD rebuild has passed; the Android 17 framework/runtime
build is still running. Authoritative job descriptions are recorded in
evidence/overnight-jobs.json (remote copy under logs). At launch their timeout
supervisor PIDs were 148382 and 148383, respectively. Inspect /proc/PID/cmdline
and actual completion/exit files before classifying either job as stopped; do
not restart because a tool observation times out. Each job has a two-hour bound.

The hardware source revision is `717bb3c9e13ce573cfdd2dda856debd27a0fa17f`.
Its kernel-only image is 7242232 bytes, SHA-256
`7c7051c147b03ca865b3481d55cd832bc6f2732eef1c0063af9404823b0ceaa4`.
All 12 captured files verify locally under the backport spike's
artifacts/linux-bpf-fd/bpf-fd-result. Configuration matches the previous hardware
candidate exactly; the tested BPF files match the virtual source exactly. GIC
source matches the original hardware source. Image inspection verifies the
ARM64 header and exactly the expected diagnostic DTB after the gzip stream.
Charging remains inhibited, and no hardware runtime success is claimed.

At 06:25:52 UTC the framework supervisor /proc/148383/cmdline still identified
the original bounded build. The build had entered Ninja's core dependency
compilation. Continue observing that same job while porting kernel prerequisites.

Next object-info prerequisite audit: this kernel's bpf_prog has neither tag nor
jited_len. Port their real implementations before claiming program-info support;
do not fabricate those fields. The source donor contains accea65b1c21 (JITed
length), 5ae1915fde1a (digest-to-tag rename) and a7a6b20da408 (further program
metadata). The original b7a13a9d6541 info patch is saved under bpf-followup.
Refcount saturation and sanitizer checks remain useful future coverage.
Five original prerequisite patches are now saved and hash-verified locally in
the backport spike's patches/bpf-info-prerequisites directory, including the
initial digest implementation 5199702654ff, scratch-buffer change 30ecceb16f1e,
digest-to-tag rename, max-instruction fix and JITed-length addition. Inspect their
dependencies/order before applying; they have not been imported yet. Expand the
hardware/virtual source-equivalence inventory as this touches filter.h/JIT code.

