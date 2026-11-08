# Selectable offline stock fallback

Question: can the same assembled USB-independent SD recovery deliberately restore original SYSTEM/BOOT/recovery after Android fails, then require OEM factory reset, while keeping the normal installer unchanged?

Status: implemented and built. Four real static AArch64 executables, compiled policy/contexts and common rootfs are delivered. Normal selection retains custom recovery; separate manifest/arm-bound STOCK-RESTORE selection restores roles0/1, retires the ordinary writer, invokes the fixed original-pair helper, durably records OEM_RESET_REQUIRED and powers off after SD flush/unmount. Failures stop without retry/inverse/normal reboot. Physical operation remains unproved.

Important outputs:

- [HANDOFF.md](HANDOFF.md): exact card layout, mode/per-role trigger generation, local final assembly command, runtime ordering and limits.
- `artifacts/{os-rescue,rescue-sd,rescue-sd-supervisor,p10-restore,sepolicy,file_contexts.bin,common-rootfs.cpio.gz}`: actual compiled/assembled products.
- `artifacts/ARTIFACTS.json`, `evidence/DELIVERY_PINS.json`: product and joined input pins.
- `source/`: implementation; `scripts/final_package.py`: final local real-input-only join, including actual immutable current-container binding and both mode control files.
- `evidence/{build-log.json,artifact-checks.json,actual-policy-delta.txt,final-local-check.json}`: focused actual build, mode/order/exit/source/FD-transfer and policy/label/archive evidence.

Continuation: parent locally runs HANDOFF.md's final command only with genuine SYSTEM/BOOT admissions, the actual five-role manifest containing final DATA identity cf433efa509f09814bff0877368f0c1b811b7615eefd3cd2a02f58b57995131b, and the real arm file. No private DATA image/table/records were accessed or sent to the VM. No fake manifest/arm/current-image header/candidate was generated. The helper compiles now and requires no missing terminal five-role header or future replacement recovery. Default common core has no automatic selector start. Preserve all old attempts and deliberately stage STOCK-RESTORE only for rollback, never as a response to install failure.

Owned VM prefix: `/srv/android/asus-offline-stock-fallback-20261107`; serial small builds only. Earlier spikes/frozen artifacts and the independently running product build remain untouched. No device/card/root/Wi-Fi/private payload/full real image operations or children were used. Physical boot is still pending the parent's card insertion/detection trial.
