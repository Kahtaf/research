# Research Notes: Random Scheduling Service Pivot

## Research Process

### Phase 1: Understanding the Current Product
- Fetched untimely.app homepage to understand current features
- Untimely is a consumer-facing app for scheduling randomly recurring, spontaneous events
- Users define events with customizable frequencies (daily, weekly, monthly, yearly) and optional time windows
- Notification channels: Email, SMS, Slack, Zapier
- Use cases shown on homepage: team appreciation, wellness reminders, social connection prompts
- Built with Next.js
- GitHub repo at github.com/Kahtaf/untimely (returned 404 — likely private)

### Phase 2: Competitive Landscape Research
Researched every major scheduling service to determine if any offer random/stochastic scheduling:

1. **cron-job.org** — Free, donation-funded. REST API with bearer token auth. Job model with schedule arrays for hours/minutes/days/months. Up to 60 executions/hour. Entirely deterministic. No random timing.
2. **Cronhub** — Developer-focused monitoring + scheduling. No random.
3. **Crontap** — Human-readable cron syntax builder. No API focus. No random.
4. **EasyCron** — Simple web-based cron with execution logs. No random.
5. **Google Cloud Scheduler** — Enterprise-grade. Cron expressions + HTTP/Pub-Sub/App Engine targets. No random.
6. **Posthook** — Task scheduling API. One-time or sequenced HTTP callbacks at precise times. API key auth. 500 free scheduled requests. No random.
7. **Cronhooks** — Webhook-native scheduling. Cron expressions or one-time timestamps. Free tier: 5 schedules. Security signatures for webhook verification. No random.
8. **HookPulse** — Elixir/OTP-based webhook scheduler. Cron, interval, clocked, and solar event scheduling. Usage-based pricing from $5.88/month. FIFO queues, idempotency keys, retry logic. No random.

**Key finding: Zero competitors offer random/stochastic scheduling. Every single one is deterministic.**

### Phase 3: AI-Native Design Research
- Researched /llms.txt convention: adopted by 844,000+ websites including Stripe, Anthropic, Cloudflare
- Structure: H1 title, blockquote description, sections with links, optional advanced topics
- Companion /llms-full.txt for complete documentation export
- MCP (Model Context Protocol): universal standard for AI-to-service communication
- Adopted by both OpenAI and Anthropic
- Supports tools, resources, and prompts as primitives
- Streamable HTTP transport for remote servers
- TypeScript and Python SDKs available at modelcontextprotocol.io

### Phase 4: Integration Patterns Research
- Webhook best practices: HMAC-SHA256 signing (Stripe pattern), retry with exponential backoff, delivery status logging
- Slack: incoming webhooks with Block Kit formatting
- Discord: webhook URLs with rich embed support
- Zapier: REST hooks (polling or webhook-based triggers)
- Make/n8n: generic webhook trigger compatibility

### Key Insights Discovered
1. The market gap is genuinely unoccupied — nobody does random scheduling as a service
2. The scheduling SaaS market is small and low-margin (donation-funded to ~$9/mo)
3. The strongest use cases are where unpredictability is a core requirement, not a nice-to-have
4. AI-native design (/llms.txt + MCP) is a genuine timing advantage — no scheduling service has this yet
5. The biggest risk is that random scheduling is easy enough to DIY that developers won't pay for it
6. cron-job.org's API design (RESTful, bearer auth, simple job model) is the right pattern to follow

### Phase 5: Source-of-Truth Audit Against Untimely Codebase (2026-02-16)
- Checked out PR #11 branch locally to edit the exact folder contents.
- Reviewed actual implementation in `/Users/kahtaf/Documents/workspace_kahtaf/untimely` instead of relying on homepage assumptions.

#### What I validated in code
1. **Data model exists already for random scheduling primitives**
   - `events`, `event_rules`, `event_schedules`, `event_actions` are implemented in Drizzle schema.
   - Schedules are persisted (`event_schedules.triggers_at`) and materialized ahead of execution.
2. **Auth model today is not API-key based**
   - User routes rely on JWT cookie session (`getCurrentUser`).
   - Admin machine routes compare `Authorization` header to `ADMIN_API_KEY`.
3. **Existing API routes are app/internal-focused**
   - CRUD-like behavior exists for create/update/delete event.
   - No public versioned API (`/v1`) and no dedicated list/get event API for external clients.
4. **Trigger worker exists and is non-trivial**
   - `/api/batch/trigger-events` handles due triggers, stale rows, and schedule renewal.
   - Performance-related query helpers and indexes are already present.
5. **Action support is partial**
   - EMAIL and SMS execution paths exist.
   - WEBHOOK and SLACK are present in enum/UI placeholders but are not implemented in trigger execution.
6. **Timezone handling is currently app-centric**
   - UI converts local time to UTC `HH:mm` before persistence.
   - Rule model does not store IANA timezone, which is required for strong API contracts.

#### Documentation changes made from this audit
- Replaced `random-scheduling-service/README.md` with a code-validated summary.
- Added `random-scheduling-service/research-doc.md` with detailed architecture/API/schema/gap analysis.
- Updated conclusions from "greenfield service design" to "productize existing scheduler core".

#### Key correction to prior assumptions
- Prior draft treated Untimely pivot mostly as a fresh API design exercise.
- Code audit shows this should be approached as an incremental migration with major reuse of existing scheduling and trigger infrastructure.

### Phase 6: README Surgical Revision After User Feedback (2026-02-16)
- Reverted `random-scheduling-service/README.md` to the original PR version.
- Applied targeted edits only where assumptions were incorrect after source review.
- Updated sections: 1 (Executive Summary), 4 (Proposed API Design context), 6 (integration claims around webhook readiness), 8 (migration/infra assumptions), and 9 (codebase head-start claim).
- Preserved the rest of the original narrative and appendices intact.
