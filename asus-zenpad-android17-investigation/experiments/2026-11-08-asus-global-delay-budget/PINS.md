# Exact actual pins

| Artifact | Bytes | SHA256 |
|---|---:|---|
| Recovery candidate | 3567616 | `578c1c5d57f607a3c93e49ae4bf2a8a2e9a56ed99f74de70bb895e64a9982f21` |
| Full p10 | 16740352 | `b3ff63a119f791e8d38ab75d2586aba52cf77086026cdfb7ff3fab706d1474c1` |
| Image.gz-dtb | 3241527 | `63e78b7c46f4125e11219bbfd5c38138b322b82ba2654e401619505f9a77b5e8` |
| Raw Image (inside gzip) | 7141888 | `b5a78dc28f3219d982e5211f4a0faf0b524df67a698b26c56bf46f8415fb5309` |
| Resolved config | 80695 | `01d6729f825798899e21192e6c33f96a80b47ccbedd5dc6cab10f78c1f9c7f31` |
| Compiled/runtime DT | 65873 | `156e92ec5d4f5c4bd20169128c8aed0a89b43636d945d648392aaaec8b9bf82e` |
| Reused /init | 772248 | `37e9e2a2d73447947fb33e57e9513fa6079517b571f5a41bc58fbb91f84633fc` |
| Reused wrapped ramdisk | 320474 | `69535be3b3b3bf160a05fb555078dd7eca239db55980fd8732f14ee7d6cc6082` |
| System.map | 2185714 | `f38f263bdd63846d5071777f13ba7981c79f08cb2d52b835614735c4425f00b8` |
| Native linked vmlinux (VM only) | 10261896 | `d0210eff6e1b5c98184905c2cbd08fe98f2f077cfabad25d12db2170c48357e1` |
| Installer | 16015 | `9a78c28ba9406f84b7d36d58c585ba59152302897d6f54e3f038bd01b12be7f2` |
| Exact profile | 5166 | `cdc86ab3f926ac39a74156fbe1d122496da285625188a082bcb7f072c690101c` |

Kernel UUID: `a4e847a5-f502-4562-8e6a-c9a358e3f22f`. Reused helper UUID: `a60fca94-e760-4ce5-a790-5c9a818ce406`. These are deliberately different. Full-image pin binds this exact kernel with that exact reused ramdisk.

`SHA256SUMS` pins all delivered artifacts, source, scripts and completed evidence (excluding itself). `source/kernel.diff` is against actual r3 source preimages; `source/install.diff` is against exact local r3 installer. Complete source manifest and the two file pre/post pins are in `evidence/final-preservation.json`.
