# Parent acceptance adjustment for this observer

During this implementation the parent explicitly directed:

> Don't make independent automount prevention a blocker to this minimal PID1
> discriminator. Exact kernel/readonlyRAM image prevents device writes; any host
> automount write attempt is rejected by media. Use raw O_RDONLY only, don't
> explicitly mount/repair/write; retain actual mount state and disclose any
> automatic readonly mount. Positive discriminator can be actual fresh USB
> massstorage identity + exact media readonly/65536B + exact raw seven-field
> report. This narrows claimed result only to kernel/PID1/RAMUSB, not clean host
> automount history. No need change upstream frozen handoff; document parent's
> concrete acceptance adjustment and rationale separately.

This is a parent-directed adjustment to the upstream requirement to prevent
ordinary automount, not a claim that the observer can prevent it. The observer
does not mutate system automount policy, mount or unmount anything. It requires
IOMedia's explicit media-level `Writable=false`, records available diskutil mount
points and read-only facts before/after, and accesses the raw device O_RDONLY.
If macOS automatically mounted the volume, the retained plists disclose the
observed mount point. Available flags are recorded without inventing a complete
mount history or claiming protection from the absence of a mount point alone.

The rationale assumes the parent separately establishes the exact installed
image and readback binding. The host observer cannot establish that binding,
nor prove that a different earlier device was never writable. Its positive
result proves only a fresh enumeration with the required current read-only
medium and exact report, under the parent's supervised trial.

## Explicit mounted-report alternative

The parent subsequently established that this caller lacks read permission on
raw device nodes, without opening one. It explicitly authorized an opt-in
`--report-via-volume` alternative, with an exact `diskutil mount readOnly` only
after existing freshness, identity, capacity and IOMedia write-protection guards.
This is not an automatic fallback or sudo authorization.

The alternative requires the actual mounted filesystem's `ST_RDONLY` flag and
opens only the exact REPORT.TXT relative to a held no-symlink root directory.
It verifies a bounded single-link regular file on the root's device, exact seven
fields, and unchanged exact disk/mountpoint/registry identity before/after.
Its distinct `POSITIVE_PID1_REPORT_VIA_READONLY_VOLUME` result explicitly has
`raw_FAT_verified=false`, with no full-media hash or no-extra-files/clean-FAT
claim. The parent accepts that narrower evidence as sufficient only for the
minimal PID1 discriminator. The upstream frozen contract remains unchanged.
