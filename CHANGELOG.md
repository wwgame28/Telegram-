# Changelog

## 1.0.0 MAX

Compared with v0.1:

- split execution into planner, researcher, writer, critic, and editor roles;
- added accepted-application synchronization and optional autonomous execution/delivery;
- added Molt Market webhook support with polling fallback;
- added controlled routine-message auto replies;
- added Brave/Tavily search adapters and public GitHub repository enrichment;
- added DNS/IP/redirect SSRF defenses, stream size caps, prompt-injection labeling, and output secret redaction;
- added Molt Market AI-recipient URL-policy delivery fallback;
- added SQLite WAL migrations, deliveries, events, runtime flags, inbound tasks, and cost/revenue ledger;
- added monthly LLM budget circuit breaker and token-usage fallback estimation;
- added optional Telegram owner notifications;
- added Moltbook identity verification and agent-to-agent task intake/polling API;
- added `/skill.md` for machine-readable service onboarding;
- added protected mobile PWA control panel with runtime autopilot controls;
- added Amvera configuration for port 8080 and `/data` persistence;
- added unit tests and API smoke tests;
- removed dead v0.1 executor code.
