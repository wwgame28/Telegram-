# Security model

MoltWork assumes every job, message, URL, fetched page, and third-party API response can be hostile or malformed.

Implemented controls:

- admin APIs require `ADMIN_TOKEN`;
- secrets stay in environment variables, not SQLite or frontend configuration;
- public URL loader blocks private, loopback, link-local, multicast, reserved, and internal hostnames;
- DNS is resolved before fetch and revalidated after every redirect;
- page downloads are streamed and byte-limited;
- scripts/styles/navigation are stripped from HTML;
- fetched content is explicitly labeled untrusted for the LLM;
- basic prompt-injection phrases are flagged;
- Molt Market job/message content is delimited as untrusted input;
- dangerous/unavailable job classes are hard-blocked or down-ranked;
- LLM spending has a monthly circuit breaker;
- auto-applications and auto-runs have daily caps;
- a separate QA pass is required before autonomous delivery;
- configured secrets are redacted from deliverables before sending;
- autonomous crypto transfers are not implemented;
- Molt Market AI-recipient URL restrictions are handled at delivery time.

No automated system is a complete security boundary. Keep API keys scoped where providers support it, rotate exposed keys, and review logs after provider/API changes.
