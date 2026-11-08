# Restore `MTK_IN_HOUSE_TEE_SUPPORT=y`: justified, and it doesn't invalidate the reduction

The reduction was meant to remove consumers and keep the protection stack. Setting TEE to `n` broke that rule. It moved DEVAPC from the TEE path (main clock enabled, interrupts handled in TEE) to the old normal-world path (`request_irq` plus `start_devapc`). That path was never entry-proven and doesn't compile. So the failed build was an unintended variant, not the reviewed baseline. Restoring the ancestor value makes the build match what was reviewed. Record it in the log as a config-generation error that has now been corrected, not as a design change.

**`MTEE_CMA_SECURE_MEMORY`:** restore it to `y`, matching the ancestor, but only if its dependencies (`OF`, `CMA`) are still `y` in the reduced config. If `CMA` was turned off by the reduction, stop for review. Don't add `CMA` back on your own.

## Acceptance checks (all needed before the rebuild)
1. **Fragment:** set `MTK_IN_HOUSE_TEE_SUPPORT=y` explicitly in the config fragment, then run olddefconfig. Confirm it survives.
2. **Delta vs. the failed reduced config:** the only changes are `MTK_IN_HOUSE_TEE_SUPPORT` and symbols that depend on it. Each one equals its ancestor value.
3. **Delta vs. the ancestor:** every difference maps to a reviewed consumer removal. Any protection, infrastructure or TEE-related symbol that differs from the ancestor and isn't on the reviewed list is a stop. This is a single diff, not a new audit.
4. **Unchanged inputs:** the DT source and DTB hashes, the 99 disabled consumer paths, the helper binary hash, the clock and protection rules, and the kernel source tree (no patches). `-Werror` stays as it is.
5. **Reserved memory:** any TEE or secure reserved-memory node the ancestor used is still present and enabled in the DTB.

## Build acceptance
- The full build succeeds with no new warnings compared with the ancestor build.
- `devapc.o` is built from the TEE branch. Check that the "IRQ handling in TEE" string is in the object or in vmlinux.
- The image and package artifacts are produced and their hashes recorded. After that, the already-approved single physical trial goes ahead unchanged.

## Stop boundary
Stop and return for review on any of these:
- Any compile or link error, of any kind.
- Any derived config change outside the TEE dependency closure.
- Any need to change source, DT, the helper or warning flags.
- `CMA` or `OF` missing.
- A checksum mismatch.

You get one rebuild, with no retry loop. What this shows: the TEE branch builds. It doesn't show that the TEE firmware or runtime path will work. That still rests only on the ancestor having been entry-proven.