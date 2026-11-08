# Product input mapping integration

The new isolated product candidate adds the reviewed Goodix touchscreen IDC and
Power/Volume keypad map to the combined-kernel/radio candidate. The original
staging and reviewed build kit r1 remain frozen. Active AOSP inputs were not
changed and no new build or device operation was started.

The candidate is `/srv/android/asus-product-integration-staging/r2`; its staged
receipt SHA256 is `e6550c455d994932180c0f254dc84a0cd51838274dfe0fe66b82522cf3edc213`.
Only the three input files and one exact additive inheritance line differ from
staging r1. Kernel, config, radio, Connectivity11, corrected LK packaging and
scoped firstboot-parity inputs remain the same. The compiled kernel remains
`46895deb12ec94160ea5af0e85afa89c6de84971db126bb94c60cec1ec3ec401`.

The corresponding build kit is `/srv/android/asus-reviewed-build-kit/r2`, with
47 source/input/test files sealed by `inputs/kit-pins.json`, whose SHA256 is
`841581a33251c975d19329d03318fb1e43e94dbdfebddcac4cd7d1def742ad70`.
The new selection check binds the exact three reviewed mapping hashes, the
previous radio device.mk bytes, and exactly one inheritance suffix. Rebinding
a manifest to altered mapping bytes or extra makefile changes is rejected.

Production build commands now use `m -j8`, matching the original build's
observed limit on the 16-CPU/64-GB VM. This corrects the earlier accidental
application of the fixture's one-CPU limit to the full product build. The
bounded test runner keeps its one-CPU/1-GiB limit. Existing one-shot revision,
real-process/lock, terminal-result, preservation and source-preimage gates stay.
No installclean, waiting integrator or competing Ninja was introduced.

Final product validation checks both installed input files and the bytes
extracted from the actual raw SYSTEM ext4 filesystem. These checks do not prove
InputReader startup, touch geometry, physical keys or wake/suspend behavior.

## Verification

All 25 tests passed on the Linux builder. Tests include real lock inheritance,
native process detection, preservation/failure behavior, source-selection
negatives, and real ext4 input payload checks. The latter passed with correct
files and rejected missing/corrupted mappings and the wrong root layout.

The actual read-only input audit passed 61,976 active baseline files, 268 kernel
postimages, 25 radio changes, 29 total product changes, three input files and
three Connectivity files. A subsequent live preflight returned exit 20 with
the real original supervisor/soong_ui/siso processes still alive. No attempt
directory or build launch was made. `evidence/linux-verification.json` records
the actual exit statuses and result tails; the remote evidence keeps full logs.

Audio routes remain unqualified and are not added by this candidate. The
accelerometer's newly delivered source/object/HAL handoff still needs a new
combined kernel and product revision; it is not silently represented as included
here. Google, root, full services, physical recovery and hardware runtime remain
separate acceptance requirements. This kit does not provide flash readiness.
