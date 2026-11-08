# USB retained-log kernel trial

Question: can source-backed initialization of Linux-owned RAM-console fields expose the first failing hardware boot checkpoint using ordinary ADB after stock Android returns?

Status: resumed at the user's request. Preparing one corrected kernel build and recovery-only trial. No full-OS flash is authorized by this readiness record; the user's standing goal and flashing authorization remain applicable once the port is ready. Original BOOT/SYSTEM/userdata stay intact during this diagnostic.

Inputs: the exact early-retained kernel/config and the single-file correction in `../2026-11-07-asus-usb-retained-log-initialization`. Stock retained-RAM transport has passed a physical test; the hardware reset cause remains unknown.

Outputs: `evidence/vm-start.json` records restart of the existing labeled builder. Build/package outputs and physical results will be recorded here as they become available. The existing 60-second diagnostic ramdisk, image layout, recovery writer, readback verification and stock fallback are retained.

Continuation: complete the single build, verify actual candidate packaging and current tablet identity, install only recovery p10, enter recovery once, and immediately collect complete stock `last_kmsg` after a verified new normal boot. No broad test or independent-review loop. A missing marker remains inconclusive; do not infer a reset cause or full-OS readiness.

## Physical result

One full recovery write/readback and one USB-acknowledged recovery entry completed. Normal stock Android returned as boot `07b983d4-92fd-4abd-ad7f-4afb6e017571`. TCP collection failed at its initial get-serialno check before root dispatch; a separately pinned USB specialization then collected the complete 523,020-byte log and verified Enforcing restoration. No v2 marker and no SD report were present. BOOT/SYSTEM/userdata remain stock. See evidence/physical-result.json. The reset cause remains unknown.

Next source-only lead: stock exposes `/sys/bus/platform/drivers/lastpc/lastpc_dump`; qualify whether its values describe the preceding reset or a current sample before reading/interpreting it. No additional recovery entry is planned from this result alone.
