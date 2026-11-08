# Restore the retained DEVAPC/TEE closure

Question: can the same reduced-consumer experiment build after restoring the ancestor's TEE selection accidentally removed during preparation?

Status: parent accepts one config-only correction and controlled build continuation after exact Opus5.5 review; no device action. This is not a new physical experiment. First compile failure/log/source/helper/initramfs preserved. No driver source repair, warning suppression, DEVAPC removal or newconsumer allowed.

Inputs: failed corrected config and the two-symbol fragment matching ancestor values. OF and CMA alreadyy. requested.config is input to one olddefconfig, not a claimed finalconfig. Resolve changes must stay in the TEE dependency closure and preserve consumer removals, secure memory reservations, hardware protections, DT, helper and build flags. Config hash in entrymetadata must be refreshed honestly; no helper recompile or arbitrary source changes.

Continuation: one olddefconfig and exactdiff review gate, then one incrementalImage build ifthegatepasses. Package the genuineoutput only on success, using preservedhelper/initramfs and all previousadmission/loadguards. Any newsubstantivecompile/link error or unexpectedconfig/DT/source change stops for review. No physicaltrial/retryloop by worker; parent stillownsonefirsttrial. Exactmodel advice/provenance in ../2026-11-08-asus-opus55-minimal-build-dependency.
