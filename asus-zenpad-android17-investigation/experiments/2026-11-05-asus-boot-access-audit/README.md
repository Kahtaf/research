# ASUS P00A boot access and restore audit

Question: Can this exact tablet support reliable read-only bootloader access and verifiable backups/restore before an experimental Android 17 boot?

Status: Alternate libusb fastboot transport works. Sixteen device areas have two matching backups, and the tablet returned to stock Android via USB reboot. Locked-state unsigned boot and a demonstrated restore route remain unresolved. No root exploit, unlock, custom boot, wipe or flash was performed.

Inputs: The sibling power and Android 17 kernel-backport spikes, matching official ASUS firmware, live device metadata, and the failed macOS fastboot 37.0.1 interaction. The earlier query runner lost buffered query results when its reboot cleanup timed out; do not infer individual query responses or lock state from it.

Outputs: Host transport/source investigation, offline bootloader/firmware evidence, next read-only access and backup plan, and explicit remaining gates. Keep any downloaded tools isolated here; do not replace the global Android tools. Preserve all Google components and stock firmware.

Continuation: Read STATUS.md and evidence/backup-manifest.json. The user confirmed five-second Power hold as the physical return procedure; the alternate USB reboot also worked. Keep the tablet in Android during further source work. Do not unlock, erase, repartition, flash or boot a custom image without a concrete backup/restore and runtime plan.
