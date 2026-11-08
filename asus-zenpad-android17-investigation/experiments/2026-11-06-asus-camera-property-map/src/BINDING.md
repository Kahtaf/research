# Private binding contract

This library exports exactly nine `android::AsusPropMap` methods. It exports **zero**
`android::PropertyMap`, String8, VectorImpl, template, RTTI, or vtable symbols. A modern
PropertyMap constructor, destructor, or clear call therefore cannot resolve to it.
`exports.map` and hidden visibility contain template/vtable definitions;
`-Bsymbolic` binds this DSO's internal definitions locally. The original class has
no PropertyMap vtable: its sole member owns the SortedVector vptr at offset zero.
The private class has the identical member and no added pointer, virtual method,
backend handle, or registry.

The real ARM32 `libcam_utils.so` witness was produced by **patchelf 0.18.0**, using
its `--rename-dynamic-symbols` support and an explicit `--add-needed` edge. The
map was derived from the ELF's nine undefined names, not a guessed API list.
Exact executed arguments and postconditions are in `../evidence/binding.json`.
The new `DT_NEEDED` is `libasus_camera_legacy_property_map.so`. The old imports are
all removed; non-PropertyMap symbol contracts, old DT_NEEDED entries, and `.text`,
`.rodata`, `.data` bytes are preserved. The original file remains unchanged.
This witness is not installable output and does not solve its unrelated imports.

Future integration must use the rewritten importer with this explicitly named
DT_NEEDED library in the camera process's isolated namespace. The adapter must be
available within that namespace's permitted paths. Generic SDK37 providers must
be the namespace's genuine providers, including a single compatible String8 and
VectorImpl implementation. Do not link an old libutils or libinput, rename a
whole system library, export any original PropertyMap aliases, or depend on
load order, LD_PRELOAD, RTLD_DEEPBIND, or interposing modern symbols. Changing only
DT_NEEDED or adding an unrenamed shim is unsafe. Every selected importer must
have all nine contracts remapped together; re-audit dynamic symbol use first.
The recorded ARM64 inventory has the same nine names, but no ARM64 importer was
rewritten because that binary was not retained in the supplied frozen set.

The direct SDK37 provider symbols are qualified, but a complete runtime namespace
configuration cannot yet be emitted: this frozen set lacks `libbase.so`,
`libvndksupport.so`, and `ld-android.so`. Their exact frontier edges are recorded
in `../evidence/provider-closure.json`. Further dependencies and symbol versions
of the two missing libraries and loader require fresh frozen receipts. No global
"all libraries" namespace link is a substitute. The module snippet intentionally
remains noninstallable. No live linker, provider service, or camera was run.
