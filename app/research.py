import base64
import re
from typing import Any
from urllib.parse import urlparse

import httpx
from bs4 import BeautifulSoup

from .config import settings
from .security import is_safe_public_url
from .search import web_search


def extract_urls(text: str) -> list[str]:
    urls = re.findall(r'https?://[^\s)\]}>"\']+', text or '')
    out: list[str] = []
    for u in urls:
        u = u.rstrip('.,;:')
        if u not in out:
            out.append(u)
    return out[:settings.max_sources]


def github_repo_from_url(url: str) -> tuple[str, str] | None:
    p = urlparse(url)
    if p.hostname not in {'github.com', 'www.github.com'}:
        return None
    parts = [x for x in p.path.split('/') if x]
    if len(parts) < 2:
        return None
    return parts[0], parts[1].removesuffix('.git')


async def fetch_public_text(url: str) -> str:
    if not await is_safe_public_url(url):
        return '[Blocked unsafe/non-public URL]'
    headers = {'User-Agent': f'MoltWorkResearchAgent/{settings.app_version}', 'Accept': 'text/html,application/json,text/plain;q=0.9,*/*;q=0.1'}
    try:
        async with httpx.AsyncClient(timeout=25, follow_redirects=False, headers=headers) as client:
            current = url
            for _ in range(4):
                if not await is_safe_public_url(current):
                    return '[Blocked redirect to unsafe URL]'
                async with client.stream('GET', current) as r:
                    if r.is_redirect:
                        loc = r.headers.get('location')
                        if not loc:
                            return '[Redirect without location]'
                        current = str(httpx.URL(current).join(loc))
                        continue
                    r.raise_for_status()
                    ctype = r.headers.get('content-type', '').lower()
                    if 'text' not in ctype and 'json' not in ctype and 'xml' not in ctype:
                        return f'[Skipped non-text content: {ctype[:80]}]'
                    buf = bytearray()
                    async for chunk in r.aiter_bytes():
                        room = 150000 - len(buf)
                        if room <= 0:
                            break
                        buf.extend(chunk[:room])
                    enc = r.charset_encoding or 'utf-8'
                    raw = bytes(buf).decode(enc, errors='replace')
                break
            else:
                return '[Too many redirects]'
    except Exception as e:
        return f'[Fetch failed: {type(e).__name__}]'
    injection_terms = ('ignore previous instructions', 'system prompt', 'developer message', 'override instructions', 'reveal your prompt')
    injection_flag = any(term in raw.lower() for term in injection_terms)
    if 'html' in ctype:
        soup = BeautifulSoup(raw, 'html.parser')
        for tag in soup(['script', 'style', 'noscript', 'svg', 'nav', 'footer']):
            tag.decompose()
        raw = '\n'.join(x.strip() for x in soup.stripped_strings)
    prefix = '[UNTRUSTED PUBLIC SOURCE; POSSIBLE PROMPT-INJECTION TEXT DETECTED]\n' if injection_flag else '[UNTRUSTED PUBLIC SOURCE]\n'
    return prefix + raw[:settings.max_source_chars]


async def fetch_github_repo(owner: str, repo: str) -> str:
    headers = {'Accept': 'application/vnd.github+json', 'User-Agent': f'MoltWork/{settings.app_version}'}
    if settings.github_token:
        headers['Authorization'] = f'Bearer {settings.github_token}'
    base = f'https://api.github.com/repos/{owner}/{repo}'
    try:
        async with httpx.AsyncClient(timeout=25, headers=headers) as client:
            meta_r = await client.get(base)
            meta_r.raise_for_status()
            meta = meta_r.json()
            readme_r = await client.get(base + '/readme')
            readme = ''
            if readme_r.is_success:
                data = readme_r.json()
                if data.get('encoding') == 'base64' and data.get('content'):
                    readme = base64.b64decode(data['content']).decode('utf-8', errors='replace')
        summary = (
            f"GitHub repository: {owner}/{repo}\nDescription: {meta.get('description')}\n"
            f"Stars: {meta.get('stargazers_count')} Forks: {meta.get('forks_count')} Open issues: {meta.get('open_issues_count')}\n"
            f"Language: {meta.get('language')} License: {(meta.get('license') or {}).get('spdx_id')}\n"
            f"Default branch: {meta.get('default_branch')} Updated: {meta.get('updated_at')}\n\nREADME:\n{readme}"
        )
        return summary[:settings.max_source_chars]
    except Exception as e:
        return f'[GitHub fetch failed: {type(e).__name__}]'


async def gather_sources(text: str, queries: list[str] | None = None) -> list[dict[str, str]]:
    sources: list[dict[str, str]] = []
    seen: set[str] = set()
    for url in extract_urls(text):
        gh = github_repo_from_url(url)
        body = await fetch_github_repo(*gh) if gh else await fetch_public_text(url)
        sources.append({'url': url, 'title': gh and f'{gh[0]}/{gh[1]}' or url, 'text': body})
        seen.add(url)
        if len(sources) >= settings.max_sources:
            return sources
    for q in (queries or [])[:4]:
        try:
            results = await web_search(q, count=4)
        except Exception:
            results = []
        for item in results:
            if item.url in seen or len(sources) >= settings.max_sources:
                continue
            body = await fetch_public_text(item.url)
            sources.append({'url': item.url, 'title': item.title, 'text': body or item.snippet})
            seen.add(item.url)
    return sources
