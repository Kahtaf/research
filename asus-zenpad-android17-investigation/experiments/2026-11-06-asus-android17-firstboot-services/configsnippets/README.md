# Parent integration inputs

Copy only `stagedsource/device/asus/p00a/firstboot/` into the integrated device
tree after the graphics owner returns build/source ownership. Apply
`device.mk.inc` and `BoardConfig.mk.inc` at their indicated positions. Do not
copy these `.inc` files into Android init directories. The upstream package
installs its own init service; no new daemon source, service rc or policy is
needed for Keymaster 4.0.

`fstab.mt8163.external-scratch.in` is a **non-installable template**, separate
from those two service inputs. It contains no original userdata, cache or
metadata mount. The only unresolved token must become a verified external
scratch partition's actual Android block-device path. Do not guess `mmcblk1`,
use an internal by-name alias, or substitute stock userdata. Parent must
record the external medium's identity, capacity, partition start/length and
fresh filesystem UUID, and verify the block path belongs to that medium in
the diagnostic environment before constructing a test image. No identification
or write to a physical medium occurred in this task.

Use a new dedicated external SD card/partition, at least 8 GiB for the first
full-product test (a planning allowance, not a measured upper bound). Prepare
ext4 off-device, with 4 KiB blocks and features supported by the actual 4.9
kernel. Inspect features rather than accepting a modern `mke2fs` default:
avoid unsupported `metadata_csum_seed`, `orphan_file`, `casefold`, `encrypt`,
`verity`, `bigalloc` and `64bit` features. Keep journal, extents, filetype and
SELinux xattrs. Check it offline, then verify a read-only `ro,noload` mount in
the diagnostic environment, O_DIRECT capability, and kernel ext4 support
before authorizing the writable test. Read-only mounting with journal replay
is not a preservation test. Confirm the actual external controller works with
the new kernel; if it does not, this plan is not yet executable.

The test fstab deliberately omits `check`, `formattable`, checkpoint, FDE,
FBE and metadata-encryption flags. Mounting is still writable and ext4 can
replay its journal on the **fresh scratch volume**. There is no fallback to
stock storage. Replace the original data entry; appending this alongside it
is unsafe. Both installed fstabs must have exactly one /data entry. Keep the
existing real `mount_all --late` lifecycle. Do not add any `ro.crypto.*` or
keystore/APEX readiness property overrides.

Do not place `/metadata` on cache, stock encryption metadata, scratch data,
or RAM as an implicit substitute. Missing persistent metadata leaves staged
APEX sessions/rollback unsupported. The staged `use_fiemap=false` configuration
keeps the existing post-data activation mode and signature checks. It is not
an update-disable switch; do not test staged Mainline updates in this profile.

Supply an authorized **public** ADB key through the existing `PRODUCT_ADB_KEYS`
mechanism if the parent wants diagnostics before the authorization UI works.
Never include a private key or disable ADB authentication.

This separate volume is a bring-up tool and can preserve test state across
reboots. It does not migrate stock FDE or fulfill the final internal persistent
tablet goal. Parent still needs a complete local stock-data backup/restore
plan and an explicit migration decision before changing internal userdata.
