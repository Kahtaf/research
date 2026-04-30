# Browser Agent in Browser Sandbox Notes

## 2026-04-30

- Started investigation into whether full coding agents such as Codex CLI, Claude Code, Gemini CLI, or equivalents have been run inside browser-local sandboxes such as WebVM, CheerpX, BrowserPod, WebContainers, or similar.
- Initial web search found many browser UIs for CLI agents, but most run the actual CLI on a local/server backend and only use the browser as a terminal or session manager.
- Need distinguish:
  - True browser-local runtime: agent binary/runtime executes inside browser sandbox via WASM/VM.
  - Browser UI for remote/local runtime: UI is browser-based, but agent process runs on desktop/server/cloud.
- GitHub search found `leaningtech/browsercode` with description "Run AI Agent CLIs in your browser", updated 2026-04-30. This appears to be the closest direct match to the user's question.
- `leaningtech/browsercode` README says BrowserCode is a BrowserPod working example with Node.js v22 in the browser, POSIX-like filesystem, bash/git/npm, restricted outbound networking, BrowserPod portals, and beta support for an unmodified Gemini CLI running client-side. It lists Claude Code as "Next" and Codex/OpenCode as "Coming soon".
- BrowserCode source confirms `@leaningtech/browserpod` dependency and boots a BrowserPod with a `gemini_20260429_2.ext2` disk image, then runs `npm run gemini` inside `/home/user/project`. The inner project depends on `@google/gemini-cli@0.27.3`.
- `browser-use/browsercode` is unrelated naming collision: it is an opencode/browser-use fork that installs locally and requires Chrome/CDP, uv, bun, etc.; not a browser-local sandbox.
- WebVM is a mature browser-local Linux VM powered by CheerpX, with x86-to-WASM JIT, virtual block filesystem, Linux syscall emulator, xterm terminal, and Tailscale networking. It has a Claude AI integration, but that appears to be a panel/API integration, not Claude Code CLI running inside WebVM.
- BrowserPod 2.0 is now a stronger candidate than plain WebVM for coding-agent products because it exposes a Node/Bash/Git/npm environment and portals through a higher-level API.
- BrowserPod docs still state native npm binary components cannot run directly in BrowserPod today; packages need WASM alternatives/overrides. BrowserCode README echoes current limitations: native binaries unsupported, no TCP networking, Chromium recommended, Safari unsupported.
- Claude Code on the web is not browser-local execution. Official docs say it runs tasks on Anthropic-managed cloud infrastructure in fresh VMs with cloned repos.
- CloudCLI/claudecodeui, Polpo, claude-code-web, and similar projects are web/mobile UIs or session managers for agents running on local machines, Docker/microVMs, or cloud backends. They are useful comparables, but they do not prove full agent execution inside a browser sandbox.
- WebContainers are highly relevant for browser-side Node execution and AI code-execution sandboxes, but I did not find a strong GitHub example of full Codex/Claude/Gemini CLI running inside WebContainers. BrowserPod/BrowserCode is currently the strongest direct evidence.
