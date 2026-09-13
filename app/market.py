from typing import Any

import httpx

from .config import settings


class MoltMarketClient:
    def __init__(self, api_key: str | None = None):
        self.api_key = api_key if api_key is not None else settings.molt_market_api_key
        self.base = settings.molt_market_base_url.rstrip('/')

    def _headers(self, auth: bool = False) -> dict[str, str]:
        h = {'Content-Type': 'application/json', 'User-Agent': f'MoltWork/{settings.app_version}'}
        if auth:
            if not self.api_key:
                raise RuntimeError('MOLT_MARKET_API_KEY не настроен')
            h['Authorization'] = f'Bearer {self.api_key}'
        return h

    async def _get(self, path: str, *, auth: bool = False, params: dict[str, Any] | None = None) -> Any:
        async with httpx.AsyncClient(timeout=35) as client:
            r = await client.get(f'{self.base}/{path}', params=params, headers=self._headers(auth))
            if r.status_code == 429:
                raise RuntimeError(f'Molt Market rate limit; retry-after={r.headers.get("Retry-After", "unknown")}')
            r.raise_for_status()
            return r.json()

    async def _post(self, path: str, payload: dict[str, Any], *, auth: bool = False) -> Any:
        async with httpx.AsyncClient(timeout=35) as client:
            r = await client.post(f'{self.base}/{path}', json=payload, headers=self._headers(auth))
            if r.status_code == 429:
                raise RuntimeError(f'Molt Market rate limit; retry-after={r.headers.get("Retry-After", "unknown")}')
            r.raise_for_status()
            return r.json()

    async def register_agent(self, name: str, description: str, capabilities: list[str]) -> dict[str, Any]:
        return await self._post('register-agent', {'name': name, 'description': description, 'capabilities': capabilities}, auth=False)

    async def agent_status(self) -> Any:
        return await self._get('agent-status', auth=True)

    async def browse_jobs(self, status: str = 'open') -> Any:
        return await self._get('browse-jobs', params={'status': status})

    async def get_job(self, job_id: str) -> Any:
        return await self._get('get-job', params={'id': job_id})

    async def get_agent(self, agent_id: str) -> Any:
        return await self._get('get-agent', params={'id': agent_id})

    async def apply_job(self, job_id: str, cover_letter: str, proposed_rate: str = '') -> Any:
        payload: dict[str, Any] = {'job_id': job_id, 'cover_letter': cover_letter}
        if proposed_rate:
            payload['proposed_rate'] = proposed_rate
        return await self._post('apply-job', payload, auth=True)

    async def my_applications(self) -> Any:
        return await self._get('my-applications', auth=True)

    async def notifications(self, mark_read: bool = True) -> Any:
        return await self._get('check-notifications', auth=True, params={'unread_only': 'true', 'mark_read': str(mark_read).lower()})

    async def conversations(self) -> Any:
        return await self._get('get-conversations', auth=True)

    async def messages(self, conversation_id: str) -> Any:
        return await self._get('get-messages', auth=True, params={'conversation_id': conversation_id})

    async def send_message(self, recipient_id: str, content: str) -> Any:
        return await self._post('send-message', {'recipient_id': recipient_id, 'content': content[:10000]}, auth=True)

    async def update_profile(self, payload: dict[str, Any]) -> Any:
        return await self._post('update-profile', payload, auth=True)
