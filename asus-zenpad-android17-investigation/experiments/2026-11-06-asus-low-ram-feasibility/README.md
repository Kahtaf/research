# Android17 usability on the 2GB ASUS

Question: can the current Android17 target be useful on this low-RAM tablet?

Status: physical usability unproved. Stock exposes2000192KiB (~1.91GiB) MemTotal. Prepared source selects low-RAM mode and bounded compressed RAM; full Android17+Google memory footprint is not yet measured. Kernel supports PSI/zram/swap, MEMCG disabled.

Outputs: source snapshots/pins and PERFORMANCE-ACCEPTANCE.md.

Continuation: test genuine SDK37 lmkd/PSI/zRAM behavior in an isolated approximately2GB guest, then measure the actual finished product and physical app workloads. No OS-downgrade decision or Google removal is authorized by this assessment.
