import json
import re
from dataclasses import dataclass
from typing import Any

import httpx

from .config import settings
from .db import add_ledger, llm_spend_month


@dataclass
class LLMResponse:
    text: str
    prompt_tokens: int = 0
    completion_tokens: int = 0
    cost_usd: float = 0.0


class LLM:
    @property
    def configured(self) -> bool:
        return bool(settings.llm_api_key and settings.llm_base_url and settings.llm_model)

    def _check_budget(self) -> None:
        if settings.monthly_llm_budget_usd > 0 and llm_spend_month() >= settings.monthly_llm_budget_usd:
            raise RuntimeError('Месячный бюджет LLM исчерпан')

    async def chat_response(self, system: str, user: str, temperature: float = 0.2, max_tokens: int | None = None) -> LLMResponse:
        if not self.configured:
            raise RuntimeError('LLM_API_KEY не настроен')
        self._check_budget()
        payload: dict[str, Any] = {
            'model': settings.llm_model,
            'messages': [{'role': 'system', 'content': system}, {'role': 'user', 'content': user}],
            'temperature': temperature,
        }
        if max_tokens:
            payload['max_tokens'] = max_tokens
        async with httpx.AsyncClient(timeout=settings.llm_timeout_seconds) as client:
            r = await client.post(
                settings.llm_base_url.rstrip('/') + '/chat/completions',
                headers={'Authorization': f'Bearer {settings.llm_api_key}', 'Content-Type': 'application/json'},
                json=payload,
            )
            r.raise_for_status()
            data = r.json()
        text = str(data['choices'][0]['message']['content']).strip()
        usage = data.get('usage') or {}
        pin = int(usage.get('prompt_tokens') or usage.get('input_tokens') or 0)
        pout = int(usage.get('completion_tokens') or usage.get('output_tokens') or 0)
        if pin <= 0:
            pin = max(1, (len(system) + len(user)) // 4)
        if pout <= 0:
            pout = max(1, len(text) // 4)
        cost = (pin / 1_000_000 * settings.llm_input_cost_per_million) + (pout / 1_000_000 * settings.llm_output_cost_per_million)
        add_ledger('llm_cost', cost, pin + pout, f'{settings.llm_model} call', {'prompt_tokens': pin, 'completion_tokens': pout})
        return LLMResponse(text=text, prompt_tokens=pin, completion_tokens=pout, cost_usd=cost)

    async def chat(self, system: str, user: str, temperature: float = 0.2, max_tokens: int | None = None) -> str:
        return (await self.chat_response(system, user, temperature, max_tokens)).text

    async def json(self, system: str, user: str) -> dict[str, Any]:
        text = await self.chat(system + '\nReturn ONLY one valid JSON object. No markdown fences.', user, 0.1)
        text = re.sub(r'^```(?:json)?\s*|\s*```$', '', text.strip(), flags=re.I | re.S)
        try:
            return json.loads(text)
        except json.JSONDecodeError:
            match = re.search(r'\{.*\}', text, re.S)
            if not match:
                raise
            return json.loads(match.group(0))


llm = LLM()
