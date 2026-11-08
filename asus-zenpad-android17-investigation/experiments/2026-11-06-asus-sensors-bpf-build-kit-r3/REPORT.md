# r3 implementation report

The owned r3 kit now implements the missing sensor/platform-BPF/vold integration and final-product guards. It preserves the already composed r3 candidate and the original BMC156 kernel selection. No active integration, r6 full-image build, device operation, new cloud resource, or lifecycle change was performed.

The final seal is `a00ea8d7c944d45e3035296c81b31a369f13bde830f88a7165b0d7542960717c` over 90 scripts, inputs and test files. HANDOFF.md contains the exact parent command and failure-review protocol. All 40 final Linux tests passed (exit 0, 41.151 seconds, 40,048 KiB peak RSS). The final sealed real input audit passed (exit 0); actual PLAN_ONLY refused absent parent acceptance (exit 20). The failed-result description succeeded under the original lock (exit 0). Full evidence is in `evidence/linux-tests-sealed.*` and `evidence/final-sealed-readonly/`.

## Source integrity

The actual read-only input audit passed 61,976 original baseline files, 276 kernel postimages, 62,228 complete compiled-source files, 25 inherited radio changes, 41 total product changes, three input mappings, 12 sensor sources, three Connectivity files, two single-file platform changes and 201 qualified BPF supplement files. Staging remains `c168e1b13ad76b669655c071017f3ba038b06b1fc2b619df969aade441f7e17d`; the combined patch remains `e5b162f002753df8c8f3ba7e58939de38b2b5cab6361f51de7f68a1fb20dc893`.

The sensor package suffixes select the genuine existing ARM64 HIDL service and implementation. Product inheritance, BoardConfig policy/manifest inclusion and five ueventd additions must be exact suffixes of r2. Sensor source bytes are unchanged. Platform BPF accepts only `babbccf603e600a2b77f5c71cbf6b1b978f72c176fd33bfab610ff2ba8956250`; vold accepts only `c5147ca901fb1c4678b34c6727e63eb325e1ad21de2cdcbcb19b8cf9af1d49c9`, reconstructing its original solely by removing one `<algorithm>` include. Every destination is included in preservation and integrated verification.

Executable paths target r3. Remaining r2 references identify immutable ancestors, source-preimage inputs or the deliberately non-rerun composition implementation; they are not build/validation destinations. The original failed r5 terminal and unused r6 are retained. The parent's later native service build is independent and must release the same lock before any r6 integration.

## Host and fixture evidence

The final 40-test Linux suite passed under one CPU, a 1 GiB virtual-memory cap and serial execution. The additional native JNI test uses a copied real host ELF, proves debug stripping preserves allocated sections, and detects mutation of executable text. Those fixtures never become install inputs. Tests exercise real inherited flock contention, real /proc native identity, actual git preimages/new-source application, backups and partial failure, one-shot terminal/revision handling, sensor architecture/composition mutations, platform source hooks, supplement mutation, actual ext4 payload mutations, compiler-record freshness and graph traversal without invoking Ninja.

The bounded real host pass is `evidence/bounded-host-r3-v3/`. Both host_init_verifier commands exited 0. Existing split CIL and that CIL plus the mechanically translated pinned sensor policy/genfs declarations compiled with real secilc and no `-N` flag, both exit 0. Adding a conflicting neverallow exited 255 with the specific expected sensor permission violation. Actual checkfc accepted the sensor file contexts (exit 0). The source/tool hashes and full argv/stdout/stderr are retained. Native property_info_checker/checkvintf were missing; those checks were not claimed as run. No installed r3 policy or VINTF was fabricated.

The final sealed real `PLAN_ONLY` preflight returned exit 20 because the failed r5 result lacked explicit hash-bound parent acceptance. At 22:13:43 UTC there was no native build, no attempt, no parent-review file and no r6 marker. This is an observation at that time; a later parent native build must instead cause a live-process/lock refusal. No waiting or launch followed the refusal.

## Preserved errors and limits

Initial test output (`tests-initial.stderr`) records the old fixture seal failing on the newly nested r2 input directory; the fixture now hashes files recursively. A later local run records its old FileNotFoundError expectation failing when the stricter exact-file-set guard correctly refused a missing input; the test now requires that refusal. Both failures remain in evidence.

Bounded-host v1 stopped with an unsupported singleton allow statement in the fixture translator. V2 linked the existing CIL but rejected the candidate translation because new types lacked object_r role declarations. Both translator versions and all outputs are retained. V3 supplies those declarations and passes; the deliberately conflicting neverallow remains a required negative. These were fixture-translation errors, not suppressed policy failures.

A first graph inspection encountered absent `rg` on the builder; existing grep and streaming Python were used instead. Existing graph inspection confirms actual Ninja includes/fragments, .ninja_log v5, and supported NINJA_ARGS plumbing. No product Ninja command was run by this worker.

The final r3 product validator is implemented and covered by bounded component/mutation tests; it has not executed on actual r6 outputs because no such build exists. Its actual Soong compiler/linker/install graph and final SYSTEM/APEX claims must succeed during the parent's future build. Full runtime/physical/kernel/service readiness, calibration and device access remain unclaimed. No tests or qualified probe binaries are installed into active AOSP or the candidate.
