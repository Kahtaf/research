# Notes

## 2026-02-16

- Task: produce a comprehensive research doc on existing solutions for AI-agent login/account creation, with integration DX focus (OAuth/iframe/SDK), risk analysis, and adoption roadmap.
- Read existing local docs first as requested:
  - `agent-login/research-report.md`
  - `agent-login/claude-plan.md`
- Observed: existing report is broad and ambitious; this pass will tighten claims to primary sources and sharpen integration recommendations.

### Initial source categories to validate
- Agent/tool auth standards: MCP auth spec, A2A spec, HTTP message signatures.
- Site-side agent verification: Cloudflare signed agents, OpenAI allowlisting guidance.
- Identity platforms extending to agents: Auth0, Okta, Stytch, Descope.
- Credential/secret execution plane: 1Password, Aembit.
- Integration layer examples: Nango.

### Key framing hypothesis
- There is no widely adopted universal “Sign in with Agent” equivalent today.
- Viable near-term architecture likely combines:
  - cryptographic agent identity + signed requests,
  - OAuth/OIDC-style delegated authorization,
  - strong anti-abuse and reputation controls,
  - extremely low-friction integration options.

### Verified findings (primary sources)

- MCP auth baseline (latest spec 2025-11-25): MCP servers are OAuth resource servers, MUST implement OAuth Protected Resource Metadata (RFC 9728), and SHOULD support Client ID Metadata Documents (CIMD).
- A2A latest spec moved discovery to `/.well-known/agent-card.json` (not `agent.json` in current draft), and defines security schemes including OAuth2 + Device Code flow; includes optional Agent Card signing.
- Cloudflare signed-agent model: operators can apply to bots/agents directory; signed agents must use Web Bot Auth.
- Cloudflare registry proposal: registry files can list `.well-known/http-message-signatures-directory` endpoints; complements per-agent key directories and metadata cards.
- AWS AgentCore Browser Web Bot Auth (preview): based on draft protocol; automatically signs requests; transparent once enabled; no app code changes required.
- OpenAI ChatGPT agent allowlisting: signed outbound HTTP requests with `Signature`, `Signature-Input`, and `Signature-Agent`; public key discoverability endpoint at `https://chatgpt.com/.well-known/http-message-signatures-directory`.
- Auth0 for AI Agents:
  - Token Vault built on RFC 8693 token exchange; Auth0 manages provider token lifecycle.
  - Asynchronous authorization uses CIBA (+ RAR) for human-in-the-loop approvals.
- Okta AI agent registration (Early Access): explicit AI-agent registration flow in Universal Directory, key-based credentials, owner assignment/governance.
- Stytch Connected Apps:
  - Can make an app an OIDC/OAuth2.1 IdP without migrating existing auth.
  - Stytch can handle OAuth client management, user consent, token issuance.
  - Connected Apps page claims OAuth 2.1 support with DCR + CIMD in remote MCP context.
- Descope Agentic Identity Hub docs: agents treated as first-class identities; supports autonomous or delegated operation; includes MCP server auth and connection vault concepts.
- Aembit IAM for Agentic AI (press release): introduces Blended Identity and MCP Identity Gateway, emphasizing policy + token exchange without exposing permissions directly to agent runtime.
- 1Password:
  - Secure Agentic Autofill keeps raw credentials out of LLM context; human approval workflow; E2E encrypted channel based on Noise framework.
  - SDK/CLI docs support runtime secret references and OTP retrieval (`?attribute=otp`).
- Nango managed auth docs: embedded auth flow, handles authorization + storage + refresh + validation; supports OAuth/API keys/basic/custom auth; advertises 600+ APIs.

### Important correction vs earlier internal draft

- A2A discovery endpoint in current spec is `/.well-known/agent-card.json`.
- Claims around broad market adoption counts and GA states need careful qualification; use only explicitly sourced statuses.

### Integration conclusions

- Existing solutions cover pieces: identity, delegated auth, credential vaulting, signed traffic, and anti-bot policy controls.
- No clear universal, widely adopted self-serve "Sign in with Agent" network that also standardizes autonomous account creation across arbitrary websites.
- Practical product direction: build an orchestration/control layer that composes existing standards/providers first, then add differentiated trust/reputation + account bootstrap primitives.

### Finalization

- Drafted `README.md` with:
  - validated landscape of current solutions,
  - explicit gap analysis on universal agent login + autonomous account creation,
  - integration-first architecture blueprint (OAuth, widget/iframe, SDK, gateway, discovery),
  - risk model and phased adoption roadmap,
  - source links.
- Kept claims conservative where market status is unclear; marked core market conclusion as inference from sourced evidence.
