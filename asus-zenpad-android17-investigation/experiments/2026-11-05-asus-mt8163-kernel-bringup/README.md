# ASUS P00A: MT8163 4.9 kernel bring-up

Question: Can the Android-oriented MT8163 Linux 4.9.337 kernel be built with an explicit ASUS Z380M/P00A board configuration and the required ASUS drivers, as a foundation for Android 17 / LineageOS 24?

Status: First offline build experiment complete. Control kernel links; ASUS board/panel/touch compile; final ASUS link is blocked by the unported charger. See [STATUS.md](STATUS.md) and [DRIVER-MATRIX.md](DRIVER-MATRIX.md). No tablet flashing, unlocking or root changes in this phase.

Inputs: The completed ../2026-11-05-asus-latest-android-feasibility audit, original ASUS 3.18 source, decoded official/live device trees and vendor inventory. Original 4.9 candidate a81e526957ef342c4ea0c7ff5a3e95366427d0cd has an incomplete BPF backport. Current build foundation: amazon-oss/android_kernel_amazon_mt8163 at dc63af1741072236efb511499f1f0b9dd281d694 (Linux 4.9.337).

Outputs: scripts/, evidence/, patches/, artifacts/, and a driver dependency matrix. Build outputs are experimental and must not be flashed. A successful compile is not proof of ASUS hardware support or Android 17 compatibility.

Continuation: Read the final STATUS.md and evidence first. Keep the stock tablet unchanged until a separate recovery experiment establishes verified backups and a restore path. Keep Google components. Android 17 remains the platform target.
