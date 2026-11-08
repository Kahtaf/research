# ASUS kernel virtual validation

Question: Can the generic ARM64 kernel and BPF code from the ASUS port be booted
and exercised under QEMU before risking the physical tablet?

Status: A generic ARM64 configuration boots under QEMU, executes basic BPF map
and socket-filter tests and powers off cleanly. Runtime probes confirmed missing
program/map ID APIs. An isolated adaptation now passes enumeration, lifecycle,
permission and allocation-failure tests in QEMU. The same BPF code also compiles
under the separate ASUS hardware configuration. No hardware boot is claimed.
Map/program lookup by ID now also passes virtual persistence, permission,
creation-failure race and program-array cleanup tests. Its separate hardware
rebuild passes too. The Android 17 framework/runtime build is running; see STATUS.md.

The device hardware configuration and virtual configuration have different
purposes. A virtual pass cannot establish ASUS display, touch, charging, Wi-Fi,
Bluetooth or GPU behavior. This experiment runs no commands on the tablet and
must never produce an image labeled as ready to flash.

Outputs: Reproduction scripts, exact source/configuration provenance, bounded
QEMU boot logs and executable BPF API probes. Keep these inside this spike.

Continuation: Use the existing labeled GCP builder in `PROJECT_REDACTED`;
retain its automatic stop limit and resource labels. Preserve all existing
hardware kernel candidates. Compile under Linux, since the Mac checkout loses
case-distinct kernel paths. See the sibling kernel-backport and device-product
spikes for their actual build status and hashes.
