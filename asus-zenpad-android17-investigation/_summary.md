Engineers successfully ported a Linux 4.9 kernel and built experimental Android 17 system images for the legacy MT8163-based ASUS ZenPad 8.0. While the investigation achieved kernel initialization and early process execution, physical hardware stability issues ultimately prevented a full installation into the tablet's primary OS partitions. The project resolved several critical blockers, including [Android Open Source Project](https://source.android.com/) BPF compatibility fixes and build system errors, but was parked in late 2026 after failing to overcome persistent runtime compute halts. All findings and source diffs are preserved to facilitate future attempts or transitions to a lighter Linux userspace using the existing [Linux kernel](https://www.kernel.org/) tree.

* Proved physical Linux 4.9 kernel entry and ARM64 PID1 execution on the target hardware.
* Successfully built and validated Android 17 (SDK37) system components and early-stage services.
* Resolved complex BPF failures and linker errors related to legacy hardware constraints.
* Identified specific physical blockers involving thermal deferred-probing and timer wakeups.
