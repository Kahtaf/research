# Bounded implementation review

Reviewed by the implementation agent itself; no delegated or independent review is claimed. Final delta is exactly two existing PCM translation units and one local static helper header. There is no Makefile, Kconfig, defconfig, DT, codec, amplifier, route, HAL, calibration, global AFE IRQ implementation, or common PCM-helper change.

The helper is justified by the identical status-only transfer contract and validation/commit algorithm in both directions. A duplicated implementation would make the two error paths drift. The additional edits in the two existing files are necessary to make that commit meaningful: pointer callbacks use the existing IRQ lock and negotiated frame width; DL1 reset takes the same ring lock; stop generations reject stale commits; copying and buffer setup/free use a sleeping mutex. These changes do not execute any user-copy under a spinlock.

Reviewed cases include signed ring counters, zero/negative ring size, null control/data, out-of-ring indices, bounded conversion before multiplication, pos/count overflow, one-ring bounds, whole-request availability, wrap without rounding, positive callback misuse, partial target mutation, failure on later user-copy chunks, buffer changes during user access, IRQ additions/subtractions between snapshot and commit, stale copy callers, and stop/suspend during user access.

A review correction retained capture's existing positive overrun accounting. A negative capture marker could be made positive by the unchanged UL1 IRQ's additive accounting; final capture pointer records the actual produced bytes and leaves an overfull ring overfull. DL1's negative underrun marker is preserved by its IRQ's existing <=0 guard. Added tests execute both exact IRQ bodies after these conditions, plus DMA expiry during user access. No “latch forever despite arbitrary counter overflow” claim is made.

The first ARM64 attempt found an unused CheckNullPointer helper after callback replacement. It was deleted from the owned capture copy; the Werror failure and prior successful pre-review test are retained in `evidence/remote/evidence/attempt1` and `pre-review-pass`. An initial local macOS harness compile could not resolve Linux-only errno names; no local sanitizer run is claimed. Final compile and sanitizer runs are on the Linux builder with explicit resource caps.

Remaining risks are stated in CONTRACT.md and HANDOFF.md. No full kernel was linked, no shipping prebuilt was replaced, no runtime integration was performed, and speaker/mic activation remains blocked.
