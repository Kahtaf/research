# Exact public source baseline pins

All paths below are relative to `../2026-11-06-asus-stock-only-ram-rescue-build/`. Local SHA256 values match its delivered SOURCE_PINS.json. No source was edited. Artifact identities in CONTRACT.md come from public receipts; images/binaries were not opened or rehashed here.

| Path | SHA256 |
| --- | --- |
| `scripts/assemble_core.py` | `2aace148e31efc447b66efb615b7f1ada416bc3c46fc8aeb30c8d7081907db30` |
| `scripts/assemble_final.py` | `2328aa79b6d317d973cc6cbb7b9b2aab27cef76736f154e2672370c560ac1db5` |
| `scripts/build_remote.py` | `9978b4cf5c202e38b6476d86f973bd48627650d5395ae90aa70e89429e41d019` |
| `scripts/collect.py` | `b4c4b8fc690ce8654301ff1f78b3ea0c996b48677a8ef21bcd90f270ff016c91` |
| `scripts/postflight.py` | `fbb94dc550ace497fc9dab982a948ac5cb6ad6c00561140e4aa245aab34fa224` |
| `scripts/postflight_resume.py` | `a61a9d5e99dad4594708ac5beaa76135f41472d3de9088ad82f8f5ba6ec79733` |
| `scripts/remote.py` | `d7246fe2ac1bb9a9ef73d1520703911dc782673432888f3aa2b1dce0197569cc` |
| `scripts/run_build.py` | `36027513eb7c5dc7493a03bba2ff7b20dbcdb686d6aa8a5d102b37508ad90262` |
| `scripts/verify_compact.py` | `a08988ea95097a518562dbf1c9c0f681c46104b2a188e4d39ceb340e2b95277e` |
| `scripts/verify_container.py` | `3f3c38f9636f12e4e17ce390d2c5d464d179e121717971c17b947029035b2b95` |
| `source/bootformat.py` | `3207680c9c4fdee2c2dc3704cb3564e5c3736c0eb3cae63edb17f6d5fa958017` |
| `source/client.py` | `0072398a0aa2da83bdf176d672e7ec767b6aaf034892fb603054a22549c5bf69` |
| `source/common.h` | `90fe60e79b3cc3932dab7e824bc803bb18ba086ea079beca8298c34ccf2a53c3` |
| `source/core_binding.h` | `c4040fd7bef4453f44b655ebf5e06fd88e7e3698ca6ad43e2ea87f1ac814c6e0` |
| `source/file_contexts.py` | `012a4f0a71f49772a12e537721b5aca3e5de1b201b2dc5aaa07a26e07cdb650c` |
| `source/generated_host_binding.py` | `2962d493872ae4fb1b3f02204e583c6436d1cf97d4e9629f375a32f2e979f468` |
| `source/handoff.h` | `7281fcf20343f8e6fbd95fa70c73b0c753f42f91e7230fc84014f02ee68af908` |
| `source/host.py` | `2d6acd11f5b46585bec820188463e4ecb863ec19a6f106a83320f14c24c479d9` |
| `source/manifest.py` | `c9a40f5e1029e8252abc9a8256d63d9fae0d4e1c5373eb247dc76e2e06c52ae2` |
| `source/p10_restore.c` | `cddda42708f1444b7d773d57cb7e750a8a34d32e7a78b2c791a096a0a420b943` |
| `source/policy_audit.c` | `a8419a1ff771646dc28c96fa342f87ce4d949ee6368660bcd962f4d3053d9333` |
| `source/policy_build.c` | `1fbb9b714f630c7d058f583b3d42242814413988ee41b188463c1291dda56fdf` |
| `source/prior_container.h` | `ef0b9c351e4ffb33e0d9159c192a479ec426b1d332f27f9000598d0cf8160df4` |
| `source/rescue.c` | `23b0af1a8c813ae925459bf4614f768a5f90e5a76efb49bf8523135159c72c49` |
| `source/restore_core.h` | `152d83f4110bc1eb4f1ab5d285ae4c322cd9e8a87937c96ea332489429c26c8f` |
| `source/sha1.h` | `ef1b62f9220f23b953833d4066e2fc154b25abe4780b867feeba45dc6012cbce` |
| `source/sha256.h` | `4011564ce3516f8cc8e6e375cdd2923e72e9f9e74e77dc6e7db0637bda52efe0` |
| `source/stock_binding.h` | `e85c82f2357850cd438766fb775033e9f0d52aa25a4f387db0ce61e51c86c140` |

The proposal is based on handoff.h `7281fc…`, p10_restore.c `cddda4…`, unchanged rescue.c `23b0af…`, immutable-container predicate `ef0b9c…`, restore core `152d83…`, and corrected host `2d6acd…`. Complete hashes are above. Future final5role source/artifact hashes cannot be known until implementation/admission; none is fabricated.

Public report/admission/host/source-adapter input files and their exact current hashes are recorded by full relative path in [INPUT_PINS.json](evidence/INPUT_PINS.json). Key remote-source and host-overlay file hashes follow.

| Path relative to ideas | SHA256 |
| --- | --- |
| `2026-11-06-asus-ram-restorer-host-contract-fix/HANDOFF.md` | `bba040bb7cae23090aee66d1991ad86008d0722322054ef5ea2479c37acde2cd` |
| `2026-11-06-asus-ram-restorer-host-contract-fix/evidence/parent-result.json` | `60c3184a5d4b3ad06351fef20449a842f17d972ecdf6ac03caea20ca01932d6c` |
| `2026-11-06-asus-ram-restorer-host-contract-fix/source/generated_host_binding.py` | `ad07c65143a15699012716ecc8d78606ea2a18aa870ae2d9d288ea1e316cec67` |
| `2026-11-06-asus-ram-restorer-host-contract-fix/source/host.py` | `2d6acd11f5b46585bec820188463e4ecb863ec19a6f106a83320f14c24c479d9` |
| `2026-11-06-asus-rescue-remote-source/HANDOFF.json` | `01aec9117d8d6ce4f0dbbe81a2976df8ff6d99772582327212bf978d73ed9b68` |
| `2026-11-06-asus-rescue-remote-source/REPORT.md` | `d5d8b1214e58884445c3d5e0dcb134ca7fde71f7754f9f4c0fe13792387dddfe` |
| `2026-11-06-asus-rescue-remote-source/SOURCE_PINS.json` | `ff4b9798ea0238e963153952f31143fe5f6aa9dd4031ca6ff0b745e1209c8b74` |
| `2026-11-06-asus-rescue-remote-source/profiles/fixed.json` | `8b4bee1d648b581468a902cb4dcfd10f3d67c6178654c0d5b7a070ec8654b6a7` |
| `2026-11-06-asus-rescue-remote-source/profiles/local-fixed.json` | `f45d6b3ae3858e2e0cef3a726f4f6a6196b083e3164f2eca6a28189adb7cad75` |
| `2026-11-06-asus-rescue-remote-source/source/build_manifest.py` | `a00c55bf788b15a5d042b64917782c3b0076cc60ae11cd58e293290cae0388aa` |
| `2026-11-06-asus-rescue-remote-source/source/parent_remote.py` | `9ee2f38683728ff93aaf62b2b28eabe8afa71a969fd2f390df8ecd9765d5271b` |
| `2026-11-06-asus-rescue-remote-source/source/pinned.py` | `76f591977c7fc444dd3e252e258abae8de6291db8295cca5072293aaa059a6ae` |
| `2026-11-06-asus-rescue-remote-source/source/source_client.py` | `ec6935d41aae8c3cb5fd71be05e087af58154adced56a7746637dfe9b012fcc8` |
| `2026-11-06-asus-rescue-remote-source/source/source_manifest.py` | `23f681756e4624e78857832540693b5d472b35e705a6554c372e478169d3027a` |
| `2026-11-06-asus-rescue-remote-source/source/sources.py` | `b76600d02008aa5c211bdc6d417226cb5539a708eef57f45b433a6b7f226ac65` |
| `2026-11-06-asus-rescue-remote-source/source/worker.py` | `10a4d1d1ee399d2565bacec10a26450f2df5e23b1666155cd895d42a2edc6629` |
