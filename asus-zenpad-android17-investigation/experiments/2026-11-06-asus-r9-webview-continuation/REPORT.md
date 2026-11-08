# Exact WebView admission and r9 preparation

The actual missing selected artifact is retrieved and verified in owned VM staging. No active source integration or native product build was performed. R9 is deliberately blocked before process inspection, lock acquisition, attempt creation or source writes because sound compiler cache lineage has not been completed.

## Artifact and source origin

The manifest chain is `.repo/manifest.xml` → `.repo/manifests/default.xml` → `snippets/lineage.xml`. The latter selects `LineageOS/android_external_chromium-webview_prebuilt_arm64`, revision `main`. The specific source cohort is pinned by the nested prebuilt project's `.repo/projects/external/chromium-webview/prebuilt/arm64.git/{HEAD,FETCH_HEAD,config}` to `5de662a4d42b57a2efe4114e499d38fa3ce41f9d`. No root `external/chromium-webview/.git` was assumed, no checkout was created, and no Git metadata or index was written.

The pinned public repository's tree and raw pointer match the actual input. Pointer Git blob SHA1 is `7c4d3ca737b0559a5a248d5124adae14aba21ce0`. Its 134-byte SHA256 is `a7b12c1895a3b354a91997fffe0e383a88e5b0e0d4371f8fdc090c71f62aade7`.

GitHub media URLs returned 404 and GitHub's default LFS endpoint reported the object absent. These were intermediate route failures. The pinned upstream `.lfsconfig` explicitly sets `https://review.lineageos.org/LineageOS/android_external_chromium-webview_prebuilt_arm64.git/info/lfs`. The authorized public download batch for the exact OID/size returned an R2 download action. Streaming download completed with exactly **260835655 bytes**, SHA256 **`1d2f61832b2596b0046cb82cf3634609ea866098d097a83fac27c35272ac726a`**. Public temporary signed URLs were not exported; the receipt retains the authoritative endpoint, exact request, HTTP success and destination hostname. `inputs/webview-origin.json` is the compact origin proof.

VM-only payload: `/srv/android/asus-product-integration-staging/r9/webview.apk`. No payload was downloaded locally, substituted, re-signed or modified. No WebView configuration, library declaration or signature check was disabled.

## Actual isolated behavior

`evidence/artifact-check.json` binds the original frozen failed command, actual tools and two fixture outcomes. The same genuine `manifest_check`/`aapt2` command was executed with only APK/status paths redirected; stdout/stderr stayed in owned fixtures. CPU affinity was one CPU and address-space limit was 1 GiB. Original pointer: exit255 with `failed opening zip: Invalid file`. Exact object: exit0, empty status, empty stderr. The original source pointer and frozen failed command remain intact.

All 646 ZIP entries passed CRC validation. The actual binary AndroidManifest.xml SHA256 is `03c5496f8dd8936f2242855db30a004a20c5d0eb688a1607218475d89a859d67`. Genuine aapt2 decoded package `com.android.webview`, version `156.0.8078.47`, code `807804701`, SDK37, minimum29. Native ZIP entries contain AArch64 ELF64 and ARM ELF32 libraries, as expected for this arm64 prebuilt. Raw decoded manifest/badging remain VM-only fixtures, with compact hashes in the receipt.

## Relevant selected LFS scope

The admitted audit follows the actual `bootimage`/`systemimage` image/packaging edges, not `.installable_files` (which also enumerates potential test installables). It binds all 14 current graph byte hashes and a 1430-node selected closure. Fourteen source APK leaves were checked through relevant `.gitattributes`; the arm64 WebView is the only selected unmaterialized LFS APK in this bounded scope. No additional materialization is required. The other three known WebView ABI pointers remain unselected and untouched. This is not an audit of every binary in the tree.

The early inventory-based reader was rejected and its output quarantined with `REJECTED_AUDIT_NOT_ADMITTED`. Under the subsequent exact user cleanup exception, UID/start/script/cwd/parent/SSH-port/graph-FD identity proved its ownership; one TERM stopped only the obsolete reader. Its wrapper and dedicated SSH exited naturally. No KILL or other process signal was used. The terminal/rejection evidence remains in `evidence/`; `cleanup-summary.json` records the small outcome and the frozen payload/milestone pin recheck.

## Compiler cache gate

See [CACHE-PROVENANCE-GAP.md](CACHE-PROVENANCE-GAP.md). Genuine r8 completed commands, frozen Ninja entries and metrics command hashes now join 36 inspected current Siso v1.5.8 output records, including the first-phase bpfloader/vold/PublicVolume outputs. Current output digests/mtimes match, and installed/unstripped ELF build IDs were checked. Current `.ninja_log` rows were not manufactured.

The remaining unresolved identity is the precise consumed transitive input content. Local Siso action digests are absent, metrics contain counts rather than per-input digests, and the actual PublicVolume Ninja-deps record contains 1032 dependency paths and its matching output mtime but no consumed content versions. Current graph/source snapshots cannot automatically stand in for execution-time preimages. `cache-provenance-gap.json`, `selected-siso-state-v2.json`, `selected-siso-dependencies.json` and exact-version Siso source receipts make the remaining gate concrete for parent decision.

The existing strict compiler channel and `verify_product_r3.py` remain byte-exact. No timestamp cutoff was lowered, cache removed, source touched, input timestamp faked or rebuild forced. `cache_lineage.require_ready` is a hard refusal with no override and admits no production rows. A sound per-output dependency/source/graph/rsp/toolchain identity extension is still required. This preparation seal is **not launchable**.

## Independent frozen input milestone

`/srv/android/asus-reviewed-build-kit/r9-webview-input-milestone-v1` is frozen separately. Its pins.json SHA256 is `3e6ca30a3074cdd7f19dd522111c52fadbfdb311a3aa16fd23563c9011e35437`; MILESTONE.json SHA256 is `b73988f5565df5b7cf54fb49acbcc23c98b8b5b0a07027082ce9a55033c2ee44`. The snapshot correctly records that r9 was unsealed/unlaunched at publication. Published bytes and the read-only payload have not been changed.

Parent independently accepted the exact input only at `2026-11-06-asus-android17-orchestration/evidence/parent-webview-input-acceptance.json`. The factual r8 terminal/source review and input acceptance are referenced separately; neither authorizes this r9 kit, cache lineage or launch.

## Preservation and limits

The source audit checks the actual integrated r8 source, complete 61976-file kernel baseline, platform source deltas, source set, configured kernel and exact product files. Kernel `e9cde06e85e752aec0433ea37fa926c31b4f7a72cd55453762ec6870e5bb5bf1`, config `10b212cabd28aad012582e86c64695ccd450650b4e09ec8da30c21e094f377c2`, WPA fix and zRAM context are retained. Charging remains inhibited, audio PCM excluded and frozen probes unchanged. All original r8 and ancestor attempts/logs/native channels stay in place. Current Ninja scope hashes are compared after fixture work. An initial overbroad metadata inventory was discarded and replaced with bounded manifest/project receipts; no source contents were changed.

Parent-only code retains original nonblocking flock, inherited FD/inode/ancestry checks, no-other-native-jobs guard, one-shot attempt consumption and terminal acceptance requirements. It has no baseline replay. The proposed only active write is `external/chromium-webview/prebuilt/arm64/webview.apk`; exact preimage, owned backup, exclusive temp copy, SHA/size/ZIP admission and atomic replacement are required. New genuine post-delta lunch/dumpvars/config checks remain before compilation in inherited build.sh. All full Google32/root/ELF/BPF26/APEX/BOOT/SYSTEM/init/SELinux/neverallow/VINTF/source validators remain required.

No parent-authored r9 acceptance exists. The unapproved description retains `reviewed_by_parent=false`. No lifecycle lock or native process was managed; the only process operation was the separately authorized exact obsolete-reader cleanup. No build engine was invoked, and no ADB/device/root/private calibration/key/cloud lifecycle work was done. The separately owned SDK37 ext4 qualification/final actual SYSTEM mount gate was acknowledged but not merged into this kit. Host full-image validation, actual SYSTEM/kernel mount, service/hardware/runtime/Google/root usability and physical readiness remain parent gates. No flash or physical GO is granted.
