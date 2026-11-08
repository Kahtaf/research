# Parent-owned init/policy integration

This is an integration recipe and source delta, not an assembled image. No init,
policy, mount or device action was performed here. Rebuild the writer with
`daemon.patch` plus `source/sd_mount.h`, retaining the existing handoff/restorer
integration if used; this task compiled only the changed standalone writer
translation unit, not a replacement container or its P10_HANDOFF build. The small
patch changes only the major179 mount predicate and adds a random run nonce to
status/startup. `common.h` and all block-write paths are unchanged.

## Files and service entries

Install the compiled `artifacts/sd_frontend.aarch64` as `/sbin/rescue-sd`,
root:root 0755 in RAM. Keep `/sbin/os-rescue`, its existing init-owned
`os_rescue` stream socket at `/dev/socket/os_rescue`, and existing daemon
root/domain permissions. Do not replace `/system/bin/sh`: in the starting
container that path is a rescue proxy, not an interactive shell interpreter.
The new service executes the static binary directly.

Use these service definitions in the parent's init rc. Both are disabled and
oneshot: a parent-controlled explicit start selects PLAN or EXECUTE, and neither
gets a restart trigger. Keep only one active client. Add no `on boot` execution
trigger and no property that silently upgrades PLAN to EXECUTE.

```rc
service rescue-sd-plan /sbin/rescue-sd
    class core
    user shell
    group shell
    seclabel u:r:shell:s0
    disabled
    oneshot

service rescue-sd-execute /sbin/rescue-sd --execute
    class core
    user shell
    group shell
    seclabel u:r:shell:s0
    disabled
    oneshot
```

Keep the existing writer socket ownership/mode that allows UID2000 connection
and its `os_rescue_socket` label. Both ends must retain SO_PEERCRED/SO_PEERSEC
support. The listening socket's creation security context must be
`u:r:os_rescue:s0`, with root creator credentials: the frontend checks the
connected socket's peer context, not `/proc` process inspection. The pathname's
`os_rescue_socket` object label is separate. In Android init, retain the writer
service's os_rescue context as the socket creation context; do not override it
with shell/init or the pathname object label. Verify this on the integrated
socket; an incompatible inherited socket fails closed. Frontend and daemon
must see the **same mount namespace** and fixed
sysfs/procfs layout; do not place either service in a private namespace that hides
or changes the SD mount.

`/rescue.manifest` remains the exact root-owned 0444 ordinary RAM file consumed
by the daemon. The client separately hashes it and compares daemon status. Supply
`/rescue.recovery.sha256` as another root-owned 0444 ordinary RAM file, exactly
64 lowercase hex plus LF, representing the parent's actual expected current
full p10 content. Do not generate this pin from SD metadata or put placeholder
hashes into a container. Both files must be on ramfs or tmpfs, not a card bind
mount. Only execute needs the recovery pin; PLAN can report source requirements
without it. The parent must supply a newly admitted five-role manifest for
normal installation; changing status/flags cannot admit stock-only artifacts.

Add these file-context entries in the parent's actual policy packaging:

```text
/sbin/rescue-sd          u:object_r:rescue_sd_exec:s0
/rescue\.recovery\.sha256 u:object_r:rootfs:s0
```

The existing `/rescue\.manifest` rootfs labeling remains. Mountpoint directories
`/mnt` and `/mnt/rescue-sd` are root-owned ordinary directories, not symlinks.

## Fixed card mount contract (parent executes later)

After independent physical identification, the only supported filesystem is
partition 1 on a separate SD at `/dev/block/mmcblk1p1` (179:33). Both the client
and writer revalidate kernel sysfs SD/removable/ancestry/dev/geometry facts.
The card must already contain a usable vfat filesystem; there is no preparation,
formatting, fsck, repair or partitioning code here. A different enumeration,
filesystem, mountpoint, bind mount or internal-emulated storage path is refused.

A parent-owned mount action must result in the equivalent of these options:

```text
source=/dev/block/mmcblk1p1
fstype=vfat
target=/mnt/rescue-sd
options=rw,nodev,nosuid,noexec,uid=2000,gid=2000,fmask=0177,dmask=0077,context=u:object_r:rescue_sd_file:s0,fscontext=u:object_r:rescue_sd_fs:s0
```

The context options assume the types/rules below are compiled into the parent's
policy. The filesystem-level label is chosen explicitly so policy rules need not
guess the stock vfat filesystem label. Keep internal eMMC unmounted/unheld as
required by the unchanged writer. No other major179 mount is allowed, including
another mount of the SD, a mounted internal partition, or a bind-mounted source.
The frontend also verifies its held card/directory/file descriptors are on
179:33 and the mounted filesystem is FAT. It never opens any block node.

Stage the producer's `card/` contents at the card root. The top-level bundle and
empty report directory are both required:

```text
/mnt/rescue-sd/asus-rescue/manifest.sha256
/mnt/rescue-sd/asus-rescue/role-2/000000.raw ...
/mnt/rescue-sd/asus-rescue/role-4/ ... optional verified nonzero chunks only
/mnt/rescue-sd/asus-rescue/role-3/000000.raw ...
/mnt/rescue-sd/asus-rescue-report/
```

The examples describe names only, not image contents or admissions. Absent
all-zero roles still require their empty role directories. Do not put receipts,
raw images, a copied authority manifest or arbitrary files under `asus-rescue/`.
The fixed `execute.trigger` is added deliberately only after PLAN reveals this
**live** daemon's manifest/run/selection line. Observe it in the parent's chosen
local/Wi-Fi output channel; no USB/ADB transport is required. A previous boot's
trigger cannot work. The host producer never writes a trigger.

## SELinux union needed in the actual policy

The following is the narrow TE intent with explicit new labels. Integrate it
with the existing binary-policy builder or source policy rather than loading a
second policy or dropping enforcing. It has **not** been compiled against the
container's actual policy in this task. Existing rules should be retained, not
duplicated or replaced. Android attribute membership and actual sysfs/proc labels
must be resolved by the parent when compiling that specific policy.

```te
type rescue_sd_exec, file_type, exec_type;
type rescue_sd_file, file_type;
type rescue_sd_fs, fs_type;

allow rescue_sd_exec rootfs:filesystem associate;
allow init rescue_sd_exec:file { open read getattr execute };
allow init shell:process { transition siginh rlimitinh };
allow shell rescue_sd_exec:file { entrypoint open read getattr execute };

allow shell self:unix_stream_socket { create connect read write getattr getopt setopt shutdown };
allow shell os_rescue_socket:sock_file { write getattr };
allow shell os_rescue:unix_stream_socket connectto;

allow shell rescue_sd_file:dir { open read search getattr write add_name };
allow shell rescue_sd_file:file { open read getattr create write };
allow shell rescue_sd_fs:filesystem getattr;
allow rescue_sd_file rescue_sd_fs:filesystem associate;

allow init rescue_sd_fs:filesystem { mount unmount getattr relabelto };
allow init rescue_sd_file:dir { mounton getattr };
```

`mounton` applies to the **underlying mountpoint** type, which is rootfs before
mounting in this recipe; retain/ensure `allow init rootfs:dir mounton;` there.
If the existing filesystem label used before the forced fscontext is different,
the init mount permission must cover that actual label too. These are init-only
mount permissions; neither shell nor os_rescue gains mount/capability privileges.
`rescue_sd_file` grants are for the card only. The frontend never needs shell
access to internal or SD block nodes. No new native capability is needed.

Retain/ensure only read/search/getattr access for shell to rootfs RAM inputs,
`/proc/self/{mountinfo,attr/current}`, `/sys/fs/selinux/enforce`, and the fixed
`/sys/{class/block,dev/block,devices}` objects traversed by `sd_identified()`.
Directory enumeration is used for card shape, and link read/getattr for the
kernel-owned sysfs links. For the ordinary labels in the source container this
means the following permissions, unioned into existing rules:

```te
allow shell rootfs:dir { open read search getattr };
allow shell rootfs:file { open read getattr };
allow shell rootfs:filesystem getattr;
allow shell device:dir { search getattr };
allow shell socket_device:dir { search getattr };
allow shell proc:dir { open read search getattr };
allow shell proc:file { open read getattr };
allow shell sysfs:dir { open read search getattr };
allow shell sysfs:file { open read getattr };
allow shell sysfs:lnk_file { read getattr };
allow shell selinuxfs:dir { search getattr };
allow shell selinuxfs:file { open read getattr };
```

Use the real specialized labels instead wherever the target policy labels these
objects more narrowly (e.g. mountinfo/proc-security/sysfs MMC). This is a concrete
access set, not a claim those runtime labels were observed. The writer already
reads sysfs/proc/SELinux state; its new `realpath` traversals also need read/getattr
on these fixed kernel sysfs links. Retain its existing authenticated socket and
block descriptor permissions unchanged. Do not add a major179-wide allow rule.
If init's inherited output FDs require the existing shell/init `fd use` or socket
logging rules, retain them for the selected output channel; they are not a
reason to grant block access. Verify the new entrypoint transition and peer
labels in the actual final policy/container rather than assuming the TE example
alone proves the service will run.

## Remaining runtime/physical gates

The parent owns the actual card/host identity, same-boot Wi-Fi trigger staging,
full image admissions and container build. Required runtime evidence remains:
actual separate removable SD enumeration and reliable vfat/report fsync behavior;
Linux4.9 execution of this static libc binary; enforcing entrypoint, namespace,
DAC and socket peer access; physical source capacity after FAT allocation;
provisional phase ceilings versus observed storage speed; and retained daemon
CID/GPT/geometry/recovery/holders/target-readback behavior. Failure or lost final
ack requires an explicit reconciliation decision, with no automatic later-image
continuation. No timing-qualified/flash-ready state is asserted by these files.
