# Architecture

## Worker loop

Every polling cycle:

1. Poll Molt Market notifications.
2. Synchronize application status.
3. For newly accepted work, optionally start the execution pipeline.
4. At the discovery interval, scan open jobs and generate qualified drafts.

## Execution pipeline

1. **Planner** decides whether the job is within supported capability and creates up to four search queries.
2. **Researcher** loads explicit public URLs, public GitHub metadata/README files, and optional Brave/Tavily search results.
3. **Writer** creates a source-aware deliverable.
4. **Critic** scores it against the job and success criteria.
5. **Editor** revises it when the critic fails it.
6. **Delivery** sends only a QA-passed result when auto-delivery is enabled.

## Control plane

FastAPI serves the iPhone-oriented PWA and protected admin endpoints. SQLite in `/data` stores jobs, application state, runs, events, deliveries, runtime toggles, inbound agent requests, and the cost/revenue ledger.

## External trust boundaries

- Molt Market: untrusted user-generated job/message content.
- Public web/GitHub: untrusted evidence.
- LLM provider: processing engine, not source of live truth.
- Moltbook: optional identity provider for inbound agent-to-agent requests.
- Telegram: optional one-way owner notifications.
