# Stock USB reporter failure-log trial

Question: which reporter setup call fails on the working stock kernel? Status: parent preflight, one logging-only recovery control; stock kernel unchanged, normal OS partitions untouched. Outputs: evidence, private raw collector references. Continuation: after one recovery boot collect retained ASUS-RAM-FAILLOG-20261107-R1 marker lines; do not repeat uncertain entry. Prior session Power fallback remains available by explicit owner instruction.

## Actual result

One verified recovery write and entry returned safely to verified Android. Retained marker log proves setup progressed through RAM medium, descriptors and backing-file attachment; first failure is put.write to configfs g1/UDC with errno16 (EBUSY). Later unbind errno19 is subsequent cleanup. Read-only current-stock uevent identifies android_usb as controller driver. Root verified legacy android0 controls and f_mass_storage/lun/{file,ro}; normal config is mtp,ffs. No runtime USB settings were changed by those reads. This stock-specific conflict is not established for4.9. Next is a narrow legacy-interface RAM reporter revision, with kernel unchanged.
