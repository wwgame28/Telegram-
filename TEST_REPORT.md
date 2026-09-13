# Validation report

Validated before packaging:

- `python -m compileall -q app` — passed.
- `pytest -q` — 6 tests passed.
- FastAPI smoke test — `/api/health` returned 200.
- Admin auth smoke test — `/api/dashboard` rejected missing token and accepted a valid token.
- Runtime settings smoke test — persisted successfully.
- Revenue ledger smoke test — persisted and summarized successfully.
- PWA manifest smoke test — returned the correct manifest content type.
- Public agent API disabled-by-default check — returned 404 while disabled.
- `amvera.yml` parsed successfully and declares Docker, port 8080, and `/data` persistence.
- Static audit removed old unused v0.1 executor module.

Not live-tested because no real credentials are embedded in the archive:

- claimed Molt Market authenticated writes;
- real LLM provider calls;
- Brave/Tavily/GitHub authenticated calls;
- Moltbook developer identity verification;
- Telegram notifications;
- actual Amvera build environment.

Those integrations fail closed or remain disabled until their environment variables are configured.
