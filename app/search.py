from dataclasses import dataclass
from typing import Any

import httpx

from .config import settings


@dataclass
class SearchResult:
    title: str
    url: str
    snippet: str


async def brave_search(query: str, count: int = 5) -> list[SearchResult]:
    if not settings.brave_search_api_key:
        return []
    async with httpx.AsyncClient(timeout=25) as client:
        r = await client.get('https://api.search.brave.com/res/v1/web/search',
                             params={'q': query, 'count': min(count, 10)},
                             headers={'X-Subscription-Token': settings.brave_search_api_key, 'Accept': 'application/json'})
        r.raise_for_status()
        items = (r.json().get('web') or {}).get('results') or []
    return [SearchResult(str(x.get('title') or ''), str(x.get('url') or ''), str(x.get('description') or '')) for x in items[:count]]


async def tavily_search(query: str, count: int = 5) -> list[SearchResult]:
    if not settings.tavily_api_key:
        return []
    async with httpx.AsyncClient(timeout=25) as client:
        r = await client.post('https://api.tavily.com/search', json={'api_key': settings.tavily_api_key, 'query': query, 'max_results': min(count, 10), 'search_depth': 'basic'})
        r.raise_for_status()
        items = r.json().get('results') or []
    return [SearchResult(str(x.get('title') or ''), str(x.get('url') or ''), str(x.get('content') or '')) for x in items[:count]]


async def web_search(query: str, count: int = 5) -> list[SearchResult]:
    if settings.brave_search_api_key:
        return await brave_search(query, count)
    if settings.tavily_api_key:
        return await tavily_search(query, count)
    return []


def search_status() -> str:
    if settings.brave_search_api_key:
        return 'brave'
    if settings.tavily_api_key:
        return 'tavily'
    return 'disabled'
