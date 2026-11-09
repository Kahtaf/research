# On-demand Apps speaker check

Parent deployment and non-actuating smoke now PASSED. Apps → Speaker check is installed; original menu programs Terminal/Browser/Keyboard were preserved and JWM parsed/reloaded the new menu without restarting the desktop. Page and exact AAC served; no-store/DENY/nosniff/nonce-CSP verified. MissingCSRF, wrongOrigin and wrongHost returned403; malformednonce returned409. Launcher reused the exact stamped server. ZERO episodes spawned, mixer values unchanged. Server stopped and dashboard restored. The full new UI arm/play path subsequently PASSED one trusted-button cycle (see below); physical audibility remains unconfirmed and no permanent speaker route is enabled. Receipt: evidence/on-demand-speaker-check-smoke.json.

Deployment preimages are SD private/before-speaker-check-menu. An initial strict guard caught /etc/jwm mode0777 before replacing its template; that root-owned real directory was changed to0755, with original mode recorded privately, then exact-state installation resumed. No other existing directory permissions or helper code were changed.

2026-11-08. Prepared `overlay/goodix/bin/asus-goodix-speaker-check`; no deployment, menu/config/profile edits, tablet access, mixer calls, native PCM opens, packages or builds. The parent owns deployment and live smoke testing. This app does not enable normal desktop speakers or run at startup.

The proposed Apps entry invokes `/usr/local/bin/asus-goodix-speaker-check` (default mode `launch`). It starts/reuses a single protected server at **http://127.0.0.1:8089**, then navigates the current normal appliance Firefox window using the existing `goodix-open-url.py`. The page has one **Play quiet tone** button. Nothing plays or arms on launch, page GET, media preload or status polling.

## Deployment contract

Install these exact, root-owned files without group/other write permission:

- App: `/usr/local/bin/asus-goodix-speaker-check`, executable.
- Qualified prototype: `/usr/local/libexec/asus-speaker-route-prototype.py`, SHA256 `61ba304f778cad44a50e0338c1bf0e5a91cd9c6a6ed33572545fd2e7ed0897a1`. Its source and lifecycle contract are unchanged.
- Quiet fixture: `/usr/local/share/asus-goodix/sound.m4a`, SHA256 `2b304ffa302593d2bd2df9f0164f59ceba408f777247ce78a7d41a3cd0fe8888`. This is the existing three-second AAC containing one faded tone second, measured decoded peak −39.886 dBFS.

The installed `/usr/local/bin/asus-goodix-audio`, normal owned PulseAudio, ALSA fallback guard, Firefox profile `/root/.mozilla/asus-appliance`, and prototype's fixed `/run/asus-goodix-audio` lock root remain prerequisites. The app imports the actual helper's validation functions and privately bounds their read-only pactl subprocess to 500 ms. It never calls the helper's start/stop/amps_off functions.

The app pins the prototype and fixture digests on startup and again before every arm; fixture responses use immutable bytes held in memory. No alternate media, gain or volume parameters exist. The page explicitly sets volume 1/unmuted/no loop only for this quiet file; previous actual lifecycle qualification used volume 0.05, so this owner-operated check at volume 1 is a deliberately louder use of the same amplitude-verified quiet fixture. Physical browser audibility remains unconfirmed until the owner uses it. No physical result is recorded automatically and there is no promotion to a persistent route.

## Modes and ownership

```sh
/usr/local/bin/asus-goodix-speaker-check serve
/usr/local/bin/asus-goodix-speaker-check launch
/usr/local/bin/asus-goodix-speaker-check stop
```

`serve` binds the server/page only. It requires the existing qualified Firefox owner but neither navigates nor plays anything. This is the parent's non-actuating smoke-test mode. `launch` is the default Apps behavior. `stop` writes a private STOP request naming only the exact stamped server instance and waits up to 12 seconds; it never sends a signal to G. Exit with a “still protecting cleanup” message means it was deliberately left alive.

Runtime lives under protected tmpfs `/run/asus-speaker-check` (0700). Separate launch/server kernel locks serialize duplicate launches and direct serve invocations. `server.json` pins boot/PID/start/executable/command-tail/script digest and exact profile owner identity. Reuse requires all of these plus READY and adequate TTL; a changed profile or expiring instance is normally stopped before a replacement. The exact command tail must be [installed app, serve]; interpreter argv0 may be python3 for direct shebang invocation, while /proc/exe still must resolve to the same exact Python executable. A stale PID alone cannot allow reuse.

Each server creates a unique `session-*` folder; each click gets a fresh, empty 0700 `episode-*` child. `active.json` retains the exact guardian stamp/path. Existing session/episode logs are preserved; startup never deletes a prior guardian, history, profile or session. Prior live stamped guardians cause new arm requests to refuse, and the shared prototype kernel lock provides the final exclusion. `UNAVAILABLE` is a persistent RAM latch for unverified episode completion; the app never clears it automatically. Cooldown is also saved with boot/monotonic time so server restart cannot bypass it.

If Firefox is absent, Apps launch can use the existing `asus-goodix-browser` wrapper with its normal display/Xauthority/runtime/profile and native-touch/Onboard environment. It requires the desktop D-Bus environment; otherwise it asks the owner to open Firefox from Apps first. It refuses an existing live but unverifiable profile owner. It never removes a profile lock or profile/session data. The existing wrapper retains its ordinary configured behavior.

## Click and cleanup contract

1. The page accepts a trusted button event only. `/arm` requires exact `Host: 127.0.0.1:8089`, exact Origin, per-server CSRF header, application/json, one bounded Content-Length, no Transfer-Encoding, and a valid fresh nonce. No CORS headers are sent. Host checks cover every GET too; responses use no-store, DENY, CSP frame-ancestors none, nonce-bound inline script/style, and nosniff.
2. Server checks its boot, exact Firefox PID/start/executable/`--profile`/lock, unchanged fixture/prototype, helper-owned native serial PulseAudio, SUSPENDED plus PCM closed, no previous active guardian or preimage, and an acquirable shared route lock. Other audio gets: **Pause other audio, wait five seconds, then try again.** At least 20 seconds separates route attempts; a nonce cannot be replayed in the instance.
3. It spawns only the unchanged qualified prototype with cap 6 in that fresh episode directory and waits at most 3 seconds for matching READY guardian/boot stamps. Only then does it return the same nonce/armed acknowledgment. Only after that response does the page call audio.play once. Browser decode/play failures leave the independent prototype cap in charge.
4. The server watches status and normally SIGTERMs only the matching stamped controller, whose PPid must still be the spawned guardian, once OFF is observed. It then waits for G's normal cleanup. It never signals, kills or performs cleanup writes on behalf of G. Successful completion requires DONE/exit 0, no preimage and route-lock reacquisition. ERROR, abnormal exit or an unverified finish latches unavailable and prohibits future arms.
5. TTL is 15 minutes. TTL, STOP or server TERM stops accepting arms and requests normal C termination when identified, then waits for guardian completion before releasing server ownership. During the usual loop it continues serving a closed/unavailable status. A prototype ERROR/fail-stop may intentionally keep both guardian and server alive beyond TTL; there is no escalation to kill G. A fatal server exception also waits for its current guardian before closing, though HTTP service may then be unavailable.

The prototype alone performs all analog writes, Ext-before-Speaker shutdown, restoration, subprocess reaping and lock retention. The old `browser-sound-trial.py` route/guardian code is not called.

## Local verification and parent smoke gate

Syntax parsing and small pure boundary checks passed for valid/invalid Host, Origin, CSRF, path, duplicate Host, content type, transfer encoding and nonce/body shape. These checks imported the app without running its main entry point. No HTTP server, browser, audio/helper subprocess or hardware command ran locally. The prototype's earlier real A/B results remain in `speaker-lifecycle-result.md`; this app has no live qualification yet.

Parent's authorized non-actuating smoke gate can install the immutable files, run `serve`, fetch `/`, `/state`, `/sound.m4a`, verify headers/hash/plain UI, and reject `/arm` requests with missing/wrong auth, Host, Origin or nonce before the arm function. The initial smoke did not send a valid arm. A subsequent parent software check used one trusted click on the same amplitude-verified quiet fixture; owner absence does not prevent bounded software verification. It cannot establish physical audibility. Test duplicate `launch` only if navigation is desired, then `stop` and restore the dashboard through the existing navigation helper. Preserve protected logs and verify no prototype episode was spawned during smoke testing.

Port 8089 availability, exact installed file identities, Firefox navigation/user-activation behavior, live headers/auth rejection, TTL/STOP and physical audibility remain for the parent's scoped checks. No menu integration was changed in this implementation.

## Parent full-path software check

PASS after adding explicit button focus and a playback-finished title for keyboard accessibility/status. One trusted Enter on the focused Play quiet tone button armed exactly one prototype episode through the new Host/Origin/CSRF/nonce path. The page reported its actual ended event through the finished window title. The same3s AAC at volume1 has the already measured-39.886dBFS peak, with fade/silence; no arbitrary media or gain setting. Guardian/controller normal IDLE cleanup completed3.542963s after readiness, while PCM was still open. Class/gain restored to their preimage, route preimage removed, PulseAudio daemon unchanged, then PCM closed on idle. The app server stopped and the dashboard was restored. Physical audibility was not claimed. Receipt: evidence/on-demand-speaker-check-playback.json; raw runtime remains ignored.
