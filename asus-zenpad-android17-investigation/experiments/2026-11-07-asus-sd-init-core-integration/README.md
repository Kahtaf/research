# SD init/core integration

Question: can the offline prearmed client and guarded writer be linked and packaged with enforcing stock init/ueventd, an exact SD mount, and success-only normal reboot?

Status: implemented and built. Actual static AArch64 daemon/supervisor, preserved static SD frontend, binary SELinux policy/compiled contexts and common rootfs are delivered. Four focused waitpid cases and actual ELF/policy/context/rootfs checks pass. No physical boot/SD qualification. Final operational image correctly awaits the parent's genuine five-role ASUSR002 manifest and actual arm ID; none was fabricated. No device/card operation or independent product-build inspection occurred.

Important outputs:

- [HANDOFF.md](HANDOFF.md): exact launch/mount/reboot behavior, final assembly command, policy delta, limits and distinct later stock fallback.
- `artifacts/common-rootfs.cpio.gz`: actual assembled nonoperational common core; final assembly adds only real authorities and the one-time operational init action.
- `artifacts/{os-rescue,rescue-sd-supervisor,rescue-sd,sepolicy,file_contexts.bin}`: actual linked executables and compiled policy/contexts.
- `artifacts/ARTIFACTS.json`, `evidence/DELIVERY_PINS.json`: exact product and joined input pins.
- `source/`: joined implementation; `scripts/final_package.py`: real-input-only final packager.
- `evidence/{build-log.json,artifact-checks.json,actual-policy-delta.txt,final-local-check.json}`: focused build/permission/label/assembly evidence.

Continuation: follow HANDOFF.md's one final assembly command after the real image admissions and parent arm file exist. The common core does not automatically execute. Normal install retains custom recovery and excludes the p10 helper/handoff from its reachable graph. The deliberately later original-recovery helper still needs genuine final manifest/core/helper/container bindings and separate physical qualification. Do not substitute any NONDEPLOYABLE binding header or reuse an UNKNOWN attempt.

Builder prefix: `/srv/android/asus-sd-init-core-integration-20261107`. Existing artifacts and all prior spikes remain unchanged. `remote_driver.py setup` refuses this existing prefix; no repeat build is necessary for handoff. No children were used.
