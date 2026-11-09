# Access restored; retained stock ALSA kernel oops

USB reconnect returned exact stock Android 7 on the original 3.18.35 kernel, with a different boot ID from the last pinned Alpine session. Stock property/serial guards and SELinux Enforcing passed. The Android foreground window was the stock launcher. No re-entry or reboot has been sent.

The saved prior-kernel log shows a kernel paging fault at uptime4514.11 in `cubeb r~ thread`, PC `snd_pcm_mmap_data_fault+0x68/0xf0`, invalid address `ffffffbee0000000`; it ends in nested panic. This is a separate output-path failure after the isolated AAC decoding fix, not evidence against that decoder result. It explains the subsequent loss of Alpine SSH. Which bootloader branch selected Android following the crash is not yet proved.

Full read-back confirms original BOOT SHA7bb68511… and canonical stock recovery SHA902b2f06… . BCB still exactly matches the known command-only Linux selection SHA7b3d5382…, with every byte after the32-byte command zero. Do not clear it or blindly run the historical installer, whose stock-return boot binding and empty-BCB precondition do not match this boot. Android has restored canonical recovery, as in the earlier stock round trip.

Raw logs, full identities and BCB backup are ignored under private/live/access-return-* . Sanitized exact oops excerpt is evidence/stock-alsa-mmap-oops.txt; verification receipt is evidence/access-return-kernel-oops.json. The first read-only audit stopped when the optional pstore directory was absent; the retained last_kmsg and BCB had already been captured. The second bounded audit completed and restored Enforcing. Root helper staging and transient checksum tmpfs were the only writes; no partition writes, radio initialization or reboot occurred.

The owner reports that the landscape page is not visible. The previous six-minute trial expired without physical qualification. No fresh trial is active on this Android boot. Hold landscape and media trials until output-path stability is resolved and Alpine control is restored.

Next: read-only Opus5.5 consultation of this exact crash, the original DL1 `.page` callback and Firefox cubeb/ALSA access selection. Seek one userspace-only path that never faults the broken hardware mapping. Do not patch the stock kernel, weaken Firefox sandboxing, or test raw mmap again. Re-entry subsequently needs a newly guarded recovery-only write from canonical stock preimage, preserving the already-valid BCB, and a safe browser startup/session before any media workload.
