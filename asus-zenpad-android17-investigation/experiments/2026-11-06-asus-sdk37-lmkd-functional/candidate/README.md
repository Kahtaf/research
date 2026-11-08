# Staged zRAM label correction — not applied to product

The real SDK37 `mkswap` applet fails to open `/dev/block/zram0` under the existing compiled enforcing policy when ueventd uses the platform default `ram_device` label. SDK37 `toolbox.te` explicitly directs device owners to label swap partitions `swap_block_device`.

Append `vendor-file-contexts.additions` to the product's device vendor `file_contexts` in a NEW parent-owned integration stage. Do not change allow rules or make SELinux permissive. Scope is only `/dev/block/zram0`; no block device or persistent flash swap is added.

Runtime proof: owned `run-boot-r5` fails mkswap with Permission denied; `run-boot-r10` uses only the additional file-context rule, preserves the compiled policy and enforcement=1, reports the actual swap_block_device xattr, and successfully formats/activates 524284 KiB usable swap in the 536870912-byte zRAM device. These are fixture results, not product/hardware policy acceptance.

Pressure qualification is complete within its bounded scope; inspect report/REPORT.md and report/HANDOFF.md before integrating. The protected-incompressible auxiliary overload failed; full product usability remains unproved.
