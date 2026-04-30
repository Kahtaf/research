# Browser-Local Coding Agents Research

## Question

Can full coding agents such as Claude Code, Codex CLI, Gemini CLI, or similar
tools run inside a browser sandbox using WebVM, CheerpX, BrowserPod,
WebContainers, or related technology?

## Short Answer

Yes, this is starting to happen, but it is very early. The strongest direct
example I found is **BrowserCode by Leaning Technologies**, which uses
BrowserPod to run an unmodified Gemini CLI client-side in the browser. Claude
Code is listed as next, and Codex/OpenCode are listed as coming soon.

Most other projects with “web”, “mobile”, or “browser” in the name do not run
the agent inside the browser. They run the agent on a local machine, Docker
sandbox, cloud VM, or remote server, then expose a browser UI.

## Strongest Match: BrowserCode

Repository:

- https://github.com/leaningtech/browsercode

Why it matters:

- README says BrowserCode is a browser runtime for AI coding CLIs.
- It is built as a working BrowserPod example.
- It includes Node.js v22 running in the browser via WebAssembly.
- It includes a browser-contained POSIX-like filesystem.
- It includes command-line tools such as `bash`, `git`, and `npm`.
- It exposes instant previews via BrowserPod portals.
- It says BrowserCode `0.1.0` launches with an unmodified Gemini CLI running
  completely client-side.

Current CLI roadmap in its README:

| CLI | Status |
| --- | --- |
| Gemini CLI | Beta open now |
| Claude Code | Next |
| Codex | Coming soon |
| OpenCode | Coming soon |

Source inspection:

- `package.json` depends on `@leaningtech/browserpod`.
- `static/project/package.json` depends on `@google/gemini-cli@0.27.3`.
- `src/lib/utils/main.ts` boots `BrowserPod`, loads a `gemini_20260429_2.ext2`
  image, creates a terminal, copies a project file, and runs `npm run gemini`
  inside the pod.

Limitations from the README:

- Native binaries are not supported yet.
- TCP networking is not available.
- Gemini may report that there is no sandbox.
- Chromium is recommended.
- Safari is currently not supported.

## BrowserPod / CheerpX Direction

BrowserPod is the most relevant foundation for this idea right now.

Official BrowserPod positioning:

- BrowserPod runs locally in the browser.
- It supports public URLs for services.
- It supports Node.js today.
- BrowserPod 2.0 adds `git`, `bash`, `curl`, and core Linux utilities.
- The project roadmap includes Python, Ruby, Go, Rust, and full Linux-class
  workloads powered by CheerpX later in 2026.

Important constraint:

- BrowserPod docs say npm packages that ship native binary components cannot
  currently run directly. They need WebAssembly alternatives or package
  overrides.

That makes Gemini CLI a better first target than Claude Code or Codex if it has
fewer hard native dependencies in the path being exercised. Claude Code’s npm
installation path currently pulls a platform-native binary, so it is harder
until BrowserPod’s native-binary/CheerpX story matures or Claude ships a
browser-compatible distribution.

## WebVM

Repository:

- https://github.com/leaningtech/webvm

WebVM is a mature browser-local Linux VM powered by CheerpX. It provides:

- x86-to-WebAssembly JIT.
- Virtual block filesystem.
- Linux syscall emulation.
- Safe client-side execution.
- xterm.js terminal.
- Tailscale networking.

It is highly relevant, but I did not find evidence that Codex CLI, Claude Code,
or Gemini CLI are already running inside WebVM as a polished product. WebVM has
a Claude AI integration, but that appears to be an API/panel integration rather
than Claude Code CLI itself running inside the VM.

## WebContainers

WebContainers are also relevant but less directly proven for full agent CLIs.

Official WebContainer material says the runtime executes Node.js applications
and operating system commands entirely inside the browser tab, and StackBlitz
positions it as an in-browser code execution layer for AI applications.

However, I did not find a strong GitHub project showing Codex CLI, Claude Code,
or Gemini CLI running fully inside WebContainers. WebContainers are strongest
for pure JavaScript/WASM Node workloads, not native binaries or broader Linux
toolchains.

## Browser UI Projects That Are Not Browser-Local Execution

These are useful comparables, but they do not prove the agent runtime is inside
the browser:

- https://github.com/siteboon/claudecodeui
- https://github.com/pugliatechs/polpo
- https://github.com/vultuk/claude-code-web

Common architecture:

- Browser/mobile UI.
- WebSocket terminal or chat interface.
- Agent process runs on host machine, Docker sandbox, microVM, or cloud.
- Browser is the control plane, not the compute sandbox.

CloudCLI is explicit about the options: self-hosted local agent sessions,
Docker sandbox, or CloudCLI Cloud. It supports Claude Code, Codex, and Gemini
CLI, but not as browser-local execution.

Claude Code on the web is also not browser-local. Anthropic’s docs say tasks run
on Anthropic-managed cloud infrastructure in fresh VMs with cloned repositories.

## Feasibility Assessment

### Feasible Today

- Browser-local MCP/data server.
- Browser-local Node-ish scripts.
- Browser-local npm package execution when packages are JS/WASM-compatible.
- Browser-local Gemini CLI in BrowserCode/BrowserPod, in beta.
- Browser-local dev server previews via BrowserPod portals or equivalent
  outbound relay.

### Feasible Soon / Experimental

- Claude Code in BrowserPod, if BrowserCode’s roadmap lands.
- Codex/OpenCode in BrowserPod, if native binary and terminal edge cases are
  solved.
- More Linux-like workflows as BrowserPod absorbs CheerpX-style x86 support.

### Hard Today

- Running current Codex CLI or Claude Code CLI unchanged in a mobile browser.
- Native binaries and `.node` modules.
- TCP-level networking.
- Full Playwright/Chromium inside the browser sandbox.
- Reliable long-running background jobs on mobile browsers.
- iOS Safari support for these heavy runtimes.

## Implications For Our PoC

Our current Cloudflare/browser-local MCP text server should stay lightweight.
It is good as a personal data/MCP server running in a mobile browser tab.

If we want a full agent-in-browser demo, the most realistic next path is not to
extend the current Worker-only PoC. It is to prototype against BrowserPod and
BrowserCode:

1. Start with BrowserCode as a reference.
2. Verify Gemini CLI boot/login/tool loop in Chromium desktop.
3. Add a small browser-local MCP server or MCP client path inside the same pod.
4. Test Android Chrome.
5. Treat iOS Safari as likely blocked until BrowserCode/BrowserPod supports it.

## Sources

- BrowserCode: https://github.com/leaningtech/browsercode
- BrowserCode source tree and package metadata inspected with GitHub CLI.
- BrowserPod homepage: https://browserpod.io/
- BrowserPod 2.0 announcement:
  https://labs.leaningtech.com/blog/browserpod-20
- BrowserPod native binaries docs:
  https://browserpod.io/docs/guides/natives
- BrowserPod beta architecture:
  https://labs.leaningtech.com/blog/browserpod-beta-announcement
- WebVM repository: https://github.com/leaningtech/webvm
- WebContainers AI page: https://webcontainers.io/ai
- WebContainer API docs:
  https://developer.stackblitz.com/platform/api/webcontainer-api
- WebContainers browser support:
  https://developer.stackblitz.com/platform/webcontainers/browser-support
- Claude Code on the web docs:
  https://code.claude.com/docs/en/claude-code-on-the-web
- CloudCLI UI: https://github.com/siteboon/claudecodeui
- Polpo: https://github.com/pugliatechs/polpo
- Claude Code Web Interface: https://github.com/vultuk/claude-code-web
