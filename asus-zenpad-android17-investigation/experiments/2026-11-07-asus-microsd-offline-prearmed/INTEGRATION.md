# Explicit offline operational integration

This follow-up supplies source, a static frontend, and a compiled daemon object.
It does not build/edit a container, helper, policy or physical card. The previous
exact mount/policy/online service recipe is preserved as
`inputs/PREVIOUS-INTEGRATION.md`. Its fixed paths, single removable SD predicate,
socket peer checks and policy types remain in force. Changes below are specific
to the offline operational profile, not an automatic resume mechanism.

## Parent build inputs

Install `artifacts/sd_frontend.aarch64` as root:root 0755 `/sbin/rescue-sd` in RAM,
label `u:object_r:rescue_sd_exec:s0`. Build the writer from source/rescue.c with
both sd_mount.h and recovery_phase.h. The delivered object was compiled without
P10_HANDOFF; final helper integration/binding belongs to the parent. Nothing in
this change relaxes a frozen helper manifest or container admission check.

`/rescue.manifest` is the exact admitted ASUSR002 file, root:root 0444 on ordinary
ramfs/tmpfs. Normal install requires five actual admitted roles. SD
`manifest.sha256` only identifies this RAM authority; it never replaces it.

For offline only, embed `/rescue.sd.arm`, root:root 0444 on ordinary ramfs/tmpfs,
containing the parent's chosen build-pairing ID: exactly 64 lowercase hex + LF.
There is no default/example real ID here. The parent stages the exact card line
before boot, using the SHA256 of the actual admitted RAM manifest and that ID:

```text
OFFLINE-PREARMED ASUSR002 <manifest-sha256> <arm-id> install:2,4,3
```

File: `/mnt/rescue-sd/asus-rescue/execute.trigger`, ordinary file, exact line + LF.
The marker distinguishes it from the existing online trigger. The parent can
construct it directly from known build inputs; the frontend's post-boot printed
line is informational and need not be retrieved or restaged. PROBE.ID at the card
root does not authorize execution and is outside the checked bundle subtree.
No Wi-Fi, USB/ADB or interactive UI is needed to execute this profile.

Do **not** embed a candidate's own full p10 hash inside that candidate to satisfy
this offline profile. `/rescue.recovery.sha256` is not read in offline mode.
Before manually entering recovery, parent MUST full-readback-verify the exact
admitted deployed p10. At runtime the frontend fully measures actual p10 through
the root/domain-authenticated daemon, records the whole baseline before image
mutation and uses it unchanged for subsequent recovery phase proofs. This is
stability binding, not independent recovery admission or evidence of preboot
verification. No equivalence is claimed against an adversarial p10 writer before
measurement. Keep the ordinary no-concurrent-p10-writer/no-fd-rebinding invariant
through all phases and the terminal receipt.

Online --execute remains available separately, with its original independent
RAM pin check and live-run card trigger. It is not selected by the operational
offline service. Default no-argument invocation still selects PLAN.

## Service and launch ordering

Add this one explicit service for an offline operational container:

```rc
service rescue-sd-offline /sbin/rescue-sd --offline-prearmed
    class core
    user shell
    group shell
    seclabel u:r:shell:s0
    disabled
    oneshot
```

In the parent's existing one-time startup action, after the existing writer has
started serving and after the fixed SD mount action, use exactly:

```rc
    start rescue-sd-offline
```

This is an intentional boot-time start in an operational container, not a command
the user must send after recovery boots. The startup action must run once per
boot; don't add service-exit triggers, loops, class restarts, cleanup of attempt
reports, reboot callbacks or generic resume properties. No delay or readiness
boolean proves the writer/mount exists: the client authenticates actual status
and checks the actual mount. If initial connection or any later phase fails it
exits; it has no automatic retry. Keep os-rescue itself oneshot with the existing
abstract lifetime lock and no automatic ordinary-writer restart.

Use the existing fixed mount contract; equivalent parent init mount command:

```rc
    mkdir /mnt 0755 root root
    mkdir /mnt/rescue-sd 0755 root root
    mount vfat /dev/block/mmcblk1p1 /mnt/rescue-sd nodev nosuid noexec rw uid=2000,gid=2000,fmask=0177,dmask=0077,context=u:object_r:rescue_sd_file:s0,fscontext=u:object_r:rescue_sd_fs:s0
```

Place that in the actual chosen startup action after required node creation,
labels and writer startup, before the single service start. It is a recipe for
the parent, not a mount operation performed here. The fixed device must first
match independent physical identity; the binary still requires removable SD
mmcblk1, dev179:32 and partition1 dev179:33 with canonical sysfs ancestry and
bounded geometry. FAT32/MBR preparation alone does not establish those runtime
facts. Keep internal eMMC unmounted/unheld. Both services share the same mount
namespace. No alternate source path, repair or filesystem creation is attempted.

The card requires the unchanged `asus-rescue/` chunk tree and pre-created
`asus-rescue-report/`. A new durable O_EXCL attempt.txt is mandatory before any
reconcile/write exchange. Retain it across boots and outcomes, including complete
and UNKNOWN attempts. Existing report means refuse execution, not resume, even
with a new daemon nonce or a matching arm ID. Do not add init actions deleting
it. Parent manages evidence and any later deliberate reconciliation separately.

## Policy addition and retained boundary

Add the RAM arm file context alongside the existing manifest rootfs mapping:

```text
/rescue\.sd\.arm       u:object_r:rootfs:s0
```

It needs the same shell rootfs read/open/getattr and parent rootfs filesystem
association already documented for the RAM manifest. No new policy type,
capability, SD/internal block access or mount permission is needed by the
frontend. Retain the prior rescue_sd_exec entrypoint transition into shell,
root os_rescue socket creation context, os_rescue_socket pathname label, shell
connectto and SO_PEERCRED/SO_PEERSEC checks. Retain the exact narrow vfat
rescue_sd_file/rescue_sd_fs permissions for source reads and durable report
creation. Source fields/hashes still come from daemon-bound RAM.

No policy binary was changed or compiled here. The parent integrates these
specified rules into its actual policy and preserves effective denial of shell/
adbd/ordinary-writer p10 or whole-disk writes. The accepted phase optimization
relies on no concurrent reachable recovery writer and no fd rebinding; this new
static client opens no block nodes and adds no arbitrary command interpreter.
The five full p10 proofs detect changed content only when their read observes it.
Metadata checks neither continuously monitor content nor universally detect an
equivalent same-node descriptor substitution. See the preserved accepted review
REPORT/HANDOFF in inputs/ for these precise limits.

Remaining parent integration is concrete: actual manifest/image admission and arm
pairing; final daemon/helper/container binding; one-time init launch ordering;
actual kernel/static-libc, enforcing entrypoint/socket labels/DAC, mount namespace
and removable SD identity; durable report/capacity and observed storage timing.
This implementation creates no flash-ready claim or new review/approval wrapper.
