# Review-only, unqualified future candidate

`kernel-source.patch` is relative to a kernel root and touches six paths. `resolved-config.patch` is relative to a future kernel output/config root and patches `.config`; its preimage is the complete pinned physical BMC config. They are separate to avoid confusing a source defconfig with a generated output config.

Pre/post hashes and new-file absence requirements are in ../evidence/pre-post-pins.json. The full candidate and preimages are supplied. Both patches replayed exactly in fresh owned evidence copies. No application to an existing kernel/product or any target build occurred.

The new configuration snapshot has not been run through olddefconfig. Keep internal MTK speaker enabled, AW8737S disabled and the explicit board-profile option together. Do not treat patch replay, native host tests or the GPIO28 software binding as physical qualification or permission to boot/flash/enable hardware.
