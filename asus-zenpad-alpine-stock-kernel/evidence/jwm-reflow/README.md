**Source-only archive note:** The fetched release tarball, APKBUILD and full extracted/QA source trees are intentionally excluded from Git. Retained provenance, authored patch/build code and small check outputs are sufficient to identify the external inputs; see ../../BUILD-INPUTS.md. Native runtime results below remain historical evidence, not a fresh build.

# JWM workarea reflow

Question: can stock JWM 2.4.6 resize existing maximized windows when Onboard
changes its dock reservation, while preserving focus and restore geometry?

Status: candidate compiled on the actual tablet, deployed separately and real Onboard/Firefox show/hide/restore/typing checks passed. Packaged JWM remains unchanged. See ../../reports/automatic-keyboard.md and ../automatic-keyboard-physical.json. The preflight account below describes preparation.
The patch cleanly applies with fuzz=0. Both modified C translation units passed
local clang syntax checking against the original headers and host X11 headers.
That check used a small generated config header, not Alpine's native configure
result; host alloca macro warnings are recorded in `qa/c-syntax.txt`.

## Inputs and outputs

- `provenance.json`: official release URL, archive hashes and retrieved APKBUILD hash.
- `jwm-2.4.6.tar.xz`: exact official archive; its SHA-512 matches stable Alpine's APKBUILD.
- `APKBUILD.alpine-3.24`: current stable native build dependencies and configure recipe.
- `../../sources/jwm-2.4.6`: pristine extracted release; LICENSE and source notices retained.
- `../../overlay/goodix/jwm-workarea.patch`: focused patch for placement and desktop changes.
- `../../scripts/build-jwm-workarea.sh`: inert native candidate build, no package install or WM launch.
- `qa/patch-application.txt`, `qa/c-syntax.txt`: local preflight evidence.

The actual JWM release is MIT licensed. The adjacent touch bridge's GPL license
does not replace JWM's own license. No upstream notices were removed or rewritten.

## Patch behavior

Upstream `ReadClientStrut()` publishes workarea changes but never reflows existing
clients. The patch recalculates maximized geometry on the current desktop,
including sticky windows, without calling `MaximizeClient()` (which raises and
focuses). It preserves all four saved restore fields, and restores status after
temporarily clearing SHADED for the geometry calculation. This keeps unshaded
client height correct even when its visible frame is currently shaded.

Minimized/hidden clients can have their stored geometry updated; the patch does
not map or unminimize them. Fullscreen clients are excluded. Inactive desktops
are excluded because upstream strut subtraction uses the current desktop; after
a desktop switch, `SetWorkarea()` runs using the new desktop and then reflows its
clients. Existing maximization flags, mapping state and focus are preserved.

Unchanged geometry produces no border reset, ConfigureNotify or pager update.
The patch does not modify strut properties, and none of the resize operations
call `SetWorkarea()`, so it adds no recursive property/resize loop. Root workarea
publication retains upstream behavior.

## Native build and continuation

Use a reviewed copy of the whole spike layout on the tablet, or copy the script,
patch and evidence archive while preserving their relative locations. The script
requires Alpine 3.24 aarch64. It prints dependency commands if prerequisites are
missing; it does not execute package installation. To assess the actual delta:

```sh
apk add --simulate --virtual .asus-jwm-build build-base pkgconf patch xz gettext gettext-dev libjpeg-turbo-dev libpng-dev librsvg-dev libx11-dev libxext-dev libxft-dev libxinerama-dev libxmu-dev libxpm-dev libxrender-dev pango-dev
```

The corresponding explicit `apk add --virtual .asus-jwm-build ...` is a separate
operator action. Native tools and headers cost substantially more space than JWM
itself: official stable package metadata lists gcc at 136,602,107 installed bytes,
g++ at 42,057,144, binutils at 14,902,498 and musl-dev at 11,683,508, before their
other dependencies and optional-library headers. These are package sizes, not the
device's incremental installation size; use the simulation against its actual
installed set. Existing packaged JWM retains its required runtime libraries.

Run `sh scripts/build-jwm-workarea.sh`. It builds only in a unique
`/var/tmp/asus-jwm-build.*` directory on the SD root, checks the source SHA-256,
applies the patch with fuzz=0, and runs native configure plus `make -j2` under one
120-second deadline. Its supervisor sends TERM to the owned build process group
on timeout/interruption, then KILL after five seconds if necessary. No build
duration or old-kernel compiler compatibility is claimed before execution.

The recipe keeps the stable APKBUILD's default optional features rather than
disabling libraries to reduce build cost. It explicitly checks icons, JPEG, NLS,
Pango, PNG, Shape, SVG, XBM, Xft, Xinerama, XPM and XRender in generated `config.h`.
It stages `asus-jwm`, `LICENSE.jwm` and the patch beside `build.log`, and prints the
candidate path and executable hash. It never calls `make install`, replaces
`/usr/bin/jwm`, launches a WM, or touches a browser profile.

After preserving a successful candidate and logs, remove the temporary dependency
group with `apk del .asus-jwm-build` as a separate operator action. Review dynamic
dependencies and verify the candidate still starts before deleting the build tree.
If promoted later, use `/usr/local/bin/asus-jwm`; retain `/usr/bin/jwm` for rollback.

The next acceptance gate is real Xorg/JWM/Firefox behavior: show the keyboard,
verify the browser's complete frame ends above it, type without losing the input
focus, hide the keyboard and verify browser expansion, then unmaximize to verify
the original restore geometry. Check repeated show/hide for stability and ensure
the packaged JWM binary is unchanged. Desktop switching, minimized and shaded
states are source-covered but remain additional unqualified runtime behavior.

Primary sources:

- https://github.com/joewing/jwm/releases/tag/v2.4.6
- https://github.com/joewing/jwm/blob/v2.4.6/src/place.c
- https://github.com/joewing/jwm/blob/v2.4.6/src/client.c
- https://github.com/joewing/jwm/blob/v2.4.6/src/desktop.c
- https://gitlab.alpinelinux.org/alpine/aports/-/blob/3.24-stable/community/jwm/APKBUILD
- https://dl-cdn.alpinelinux.org/alpine/v3.24/main/aarch64/APKINDEX.tar.gz
