# Recovery probe over authenticated Wi-Fi

Question: can the existing guarded p10 installer honor the user's Wi-Fi preference without depending on flaky USB enumeration?

Status: parent transport adaptation. The existing reviewed Linux4.9 image admission, install/inverse sequence, exact partition guards, root helper and full readbacks are reused. USB presence is not asserted or required. No reboot or manual entry is performed.

Outputs: one executable parent script. Default is PLAN_ONLY; live command logs, captures and completion evidence stay in ignored private storage. Only exact stock Android on the pinned private endpoint and serial is accepted, with one boot ID retained throughout the operation.

Continuation: first enable authenticated Wi-Fi ADB through one brief USB connection. Run `python3 -B scripts/install.py --execute` once, then use Volume Up + Power for the boot menu, Volume Up to highlight Recovery and Volume Down to confirm. Stock Android may replace recovery on a normal boot, so refresh/readback immediately before entry. The RAM probe has no Wi-Fi; this installer does not make recovery or Android17 network-ready. No full-OS or userdata write is included.
