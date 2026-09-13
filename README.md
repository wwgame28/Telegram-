# MoltWork 1.0

MoltWork is a mobile-first autonomous work agent for a deliberately narrow job class: public web research, public GitHub analysis, comparisons, and text reports. It is designed for Molt Market and can optionally expose an agent-to-agent intake API authenticated with Moltbook identity.

## Pipeline

`Discovery → heuristic filter → LLM preflight → application → status sync → planner → source collection → writer → independent QA → revision → delivery`

The system refuses or down-ranks jobs that require physical work, account compromise, impersonation, money transfers/trading, medical/legal professional decisions, or capabilities it does not actually have.

## What is implemented

- Molt Market job discovery and claim-aware API client.
- Daily application rate guard below the platform's published maximum.
- Accepted-application synchronization.
- Optional automatic execution after acceptance.
- Planner / researcher / writer / critic multi-agent pipeline.
- Up to `MAX_REVISION_ROUNDS` QA revision loops and minimum QA score.
- Safe public URL fetcher with DNS/IP SSRF blocking and redirect revalidation.
- Public GitHub repository enrichment through the GitHub REST API.
- Optional Brave Search or Tavily web search.
- Optional automatic delivery by Molt Market messages.
- Molt Market webhook configuration plus polling fallback.
- SQLite WAL database, event log, runs, deliveries, runtime settings, and cost ledger.
- Monthly LLM budget circuit breaker.
- Optional Telegram owner notifications.
- Optional Moltbook identity verification and agent-to-agent task intake foundation.
- PWA/mobile control panel for iPhone, including runtime controls and manual revenue ledger.
- Output secret redaction before delivery and Molt Market AI-recipient URL-policy fallback.
- Runtime autopilot toggles from the panel.
- Dockerfile and `/api/health` healthcheck for Amvera.

## Critical boundary

Molt Market currently documents direct crypto payments between counterparties rather than escrow. MoltWork **does not sign transactions, send crypto, or mark money as paid**. Payment remains a human-controlled operation. This avoids turning an autonomous research worker into an autonomous wallet with opinions.

## First deployment on Amvera

1. Upload this repository/archive to a Git repository used by Amvera.
2. Deploy with the included `Dockerfile`; expose port `8080`.
3. Attach persistent storage at `/data`.
4. Add at minimum:

```env
ADMIN_TOKEN=<long-random-secret>
MOLT_MARKET_API_KEY=<after agent registration + claim>
LLM_API_KEY=<your provider key>
LLM_BASE_URL=<OpenAI-compatible base URL>
LLM_MODEL=<model>
```

5. Recommended:

```env
PUBLIC_BASE_URL=https://YOUR-AMVERA-DOMAIN
WEBHOOK_SECRET=<random-secret>
BRAVE_SEARCH_API_KEY=<optional>
GITHUB_TOKEN=<optional, improves GitHub API limits>
TELEGRAM_BOT_TOKEN=<optional>
TELEGRAM_CHAT_ID=<optional>
```

6. Open the app on iPhone and enter `ADMIN_TOKEN`. Add the site to Home Screen to use it as a PWA.

## Registering a Molt Market agent

Before `MOLT_MARKET_API_KEY` exists, set `ADMIN_TOKEN`, deploy, open Settings → **Create Molt Market agent**. The registration response contains the claim URL and API key. The market documentation says the API key is shown once, so copy it directly into Amvera secrets and do not commit it.

## Autopilot modes

Safe default is all off. Toggle progressively:

- `auto_apply`: send qualified drafts automatically.
- `auto_execute`: execute only jobs whose application status becomes `accepted` or `in_progress`.
- `auto_deliver`: send QA-passed output to the job poster.
- `auto_reply`: handles routine incoming-message previews only; it refuses price/scope/financial commitments and escalates those to the operator.

Hard caps remain enforced by environment variables even when panel toggles are enabled.

## Research search

Explicit URLs in the job are always processed first. General web search is enabled only when `BRAVE_SEARCH_API_KEY` or `TAVILY_API_KEY` is configured. Without one of those, MoltWork does not pretend that an LLM's memory is live web research.

## Cost control

Set provider prices:

```env
LLM_INPUT_COST_PER_MILLION=...
LLM_OUTPUT_COST_PER_MILLION=...
MONTHLY_LLM_BUDGET_USD=25
```

When the tracked monthly LLM spend reaches the budget, new LLM work is blocked. If token prices are left at zero, token usage is still logged but cost accounting will stay zero.

## Moltbook agent-to-agent API

Moltbook's developer platform can verify temporary agent identity tokens. To expose the intake foundation:

```env
MOLTBOOK_APP_KEY=moltdev_...
PUBLIC_AGENT_API=true
```

A verified agent can `POST /api/public/tasks` with an `X-Moltbook-Identity` header and poll `GET /api/public/tasks/{task_id}`. The service also exposes `/skill.md` so another agent can read the machine-facing instructions. By default tasks queue for owner approval; `PUBLIC_AGENT_AUTO_EXECUTE=true` enables automatic execution. No payment is processed by these endpoints, so leave it off until you have a billing/contract layer.

## Tests

```bash
pytest -q
python -m compileall -q app
```
