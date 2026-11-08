# Logging option within the exact LK command-line limit

Question: does the same RAM helper report beyond ten lines when printk.devkmsg=on actually reaches Linux?

Status: correcting the previous packaging failure. That trial retained exactly ten records because the delivered command line truncated the new header option, truncating the intended option to `printk`. This candidate removes only androidboot.selinux=permissive, an Android-init parameter unused by this RAM helper and not interpreted by the Linux kernel parser. All actual kernel parameters, including build_version=3, stay. The complete string must fit the conservative previously used 92-byte budget; the exact truncation threshold is not inferred here. Kernel gzip/raw, whole helper ramdisk and hardware DT are unchanged. Only header/chosen command-line values and required lengths/hash differ. Same helper UUID deliberately reused; require exact new container hash, one fresh verified stock boot transition and new full retained log. Nearby Power fallback required.

No kernel timer, watchdog or storage fix is claimed. See scripts/package.py and evidence/packaging-receipt.json.

## Parent physical result

Installed and verified full p10 once in run 3a1e26bc-d9b1-4bca-87f0-0af1f694c58f (cleanup verified). One recovery entry returned to a fresh stock boot. Actual printk.devkmsg=on reached Linux, and the same helper emitted 76 records instead of ten. The logging confounder is resolved. uname, mounts, enumeration, clock_gettime and alarm setup returned. First unfinished operation is clock_nanosleep relative100ms; neither return nor alarmhandler was observed. See ../2026-11-07-asus-linux49-short-log-trial/evidence/RESULT.json. No next kernel/driver variant is inferred from this source package.
