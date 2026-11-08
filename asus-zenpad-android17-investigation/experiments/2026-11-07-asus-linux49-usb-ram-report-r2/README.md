# Correct USB RAM report initrd bound

Question: remove the512-byte MTK wrapper from the DT initrd payload-length calculation before the USB diagnostic boot.

Status: corrected package, no boot attempt. The prior USBv1 image was recovery-only installed/readback-verified, never rebooted by parent. Only linux,initrd-end changes to payload end; compressed/uncompressed kernelImage and wrapped RAM-report program remain byte-identical. USB serial/run/VID/PID stay as the never-booted v1.

Outputs: artifacts/candidate.img, candidate.p10.raw, source/install.py and evidence/packaging-receipt.json. Program source/runtime contract remain in ../2026-11-07-asus-linux49-usb-ram-report. The user allowed automatic ADB recovery probes.

Continuation: use source/install.py defaultPLAN, then parent-only --execute for exact recovery-onlywrite and fullreadback, freshUSBidentity and one adb reboot recovery. Observe freshUSBserialP499342cbf13bf044d4b655 VID0b05 PID4a49 onknownlocation01111000, runtimeASUS-PID1:uname.release and optional readonlyRAMFATPROBE.TXT. No SD/internalstorage access bydiagnostic. NormalAndroidreturn and actual report/descriptor must beverified; no physicalGO claimed.

Actual parent trial: installed once with full p10 SHA5c892630 verified and private staging cleanup verified (runa38efdb2-eef5-4ca4-9653-94f2a83a8878). One USB adb reboot recovery acknowledged2026-11-07T13:49:15Z. Android returned independently at13:50:47Z with fresh boot6823914c-c2aa-48d1-a5ec-30e7bd925a00, bootcomplete1, SDK24, Enforcing, secureADB. USB observer remains authoritative for presence/absence of fresh probe identity; absence does not uniquely establish failure before PID1.
