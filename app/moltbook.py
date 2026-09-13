from typing import Any
import httpx

from .config import settings


class MoltbookIdentity:
    @property
    def configured(self) -> bool:
        return bool(settings.moltbook_app_key)

    async def verify(self, token: str) -> dict[str, Any]:
        if not self.configured:
            raise RuntimeError('MOLTBOOK_APP_KEY не настроен')
        async with httpx.AsyncClient(timeout=20) as client:
            r = await client.post(
                settings.moltbook_base_url.rstrip('/') + '/api/v1/agents/verify-identity',
                headers={'X-Moltbook-App-Key': settings.moltbook_app_key, 'Content-Type': 'application/json'},
                json={'token': token},
            )
            r.raise_for_status()
            return r.json()


moltbook = MoltbookIdentity()
