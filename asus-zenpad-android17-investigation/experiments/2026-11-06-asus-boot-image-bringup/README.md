# ASUS boot image bring-up

Question: Can the compiled ASUS 4.9 kernel be packaged in this tablet's actual
MTK/Android boot-image format as a step toward the Android 17 port?

Status: Offline packaging completed: the 9,773,056-byte candidate fits the
16,740,352-byte boot partition and the official image reconstructs byte for byte.
The first candidate preserves
the stock ramdisk to isolate kernel packaging; it is not an Android 17 ROM or a
hardware-validated boot image. Do not flash this packaging artifact as-is.

Outputs: A stock-image roundtrip check, experimental kernel image and exact
header/payload manifest. No device commands, firmware writes or data changes.

Continuation: Finish the Android 17 userspace and device/HAL integration in the
sibling device-product spike. A real test ramdisk must define its mount/ADB
behavior before a hardware boot. Retain Play Store/Google components in the final
ROM. Use the actual live GPT sizes, not the firmware scatter offsets.
