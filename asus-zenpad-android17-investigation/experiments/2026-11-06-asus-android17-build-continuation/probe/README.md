# Separate RAM-only 4.9 probe

In progress; no image or hardware acceptance is claimed until artifacts and verification receipts are published.

The helper derives from the repaired stock control but uses a separate configfs init path for the actual MT8163 USB20 child UDC `musb-hdrc`. Stock init/adbd and public trust input remain unchanged. Only `adb shell report` is implemented, with actual UID2000 and shell-domain guards; the report is atomically published0444 after a20-second monotonic delay. The independent root deadline starts in early-init and requests normal reboot after120seconds. No persistent mounts, calibration payloads, block writer, radio activation or charging permission are included.

The isolated combined kernel removes the stale DTS2MiB initrd argument. Packaging supplies the actual compressed ramdisk range at0x44000200 in BOTH chosen bootargs and linux,initrd-start/end, and in the Android header command line. Kernel source order confirms FDT discovery occurs before parse_early_param; an inherited initrd argument can override the FDT range. Every other DT property and reservation stays unchanged. This avoids relying on an unproved LK overwrite for the length. Physical LK transfer and4.9boot remain untested.

Geometry: header0/page2048; kernel40080000; wrapped ramdisk44000000/payload44000200; tags4e000000; emptysecond40f00000. The final artifact uses the RECOVERY wrapper for this diagnostic, not the full product boot packaging. Parent alone reviews/executes it. Do not use the old legacy-USB-only stock control as the4.9ramdisk.
