# Next product build input

The original r5 supervisor ended with exit 1 at 2026-11-06T21:15:32Z. Its actual
single failed action uses `std::replace` without `<algorithm>` in
`system/vold/model/PublicVolume.cpp`. Full images were not completed.

Parent reproduced that exact compiler failure in the new isolated builder
fixture `/srv/android/asus-vold-build-include-fix`. The original source fails;
the sole added include compiles with the same genuine SDK37 compiler/flags.
Only source/output locations and a read-only original model-header include path
are redirected for isolation. Both action vectors and diagnostics are preserved.
One CPU and a 1 GiB address-space cap apply. No active source or output changed.

Exact pins:

- Preimage: `0e17fccedefabb20e2d8650252af8c765af68378a1d853e0fbaa6a8bd1ea67fd`.
- Postimage: `c5147ca901fb1c4678b34c6727e63eb325e1ad21de2cdcbcb19b8cf9af1d49c9`.
- Patch: `98e923b851c0de58d4ca7787628f2fb4ea6471fd1cf2a36fe44c6482061168af`.
- Successful object: `953c20dcd3015ee81c3f134840c2d08eee70b8f13bb233986fd0b0b9e103674e`,
  314,376 bytes, actual ThinLTO bitcode; not linked/runtime proof.

Bind this one exact source addition into a new reviewed integration kit alongside
the qualified new product inputs. The sealed r1/r2 kits remain unchanged. Retain
the real terminal result and hash-bound failed-result parent review; never treat
this as authorization for an automatic retry, installclean or overwrite of r5.

The future full build must compile and link the actual product's vold from this
postimage. The isolated object is evidence, not a shipping prebuilt substitute.
