import asyncio
import secrets
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Any

from fastapi import Depends, FastAPI, Header, HTTPException, Request
from fastapi.responses import FileResponse, JSONResponse
from pydantic import BaseModel, Field

from .agent import WorkAgent
from .config import settings
from .db import (
    add_ledger, create_inbound_task, get_inbound_task, init_db, latest_application, ledger_summary, list_events,
    list_inbound_tasks, list_jobs, list_runs, public_tasks_last_hour, runtime_flags, set_runtime, stats, update_inbound_task,
)
from .llm import llm
from .market import MoltMarketClient
from .moltbook import moltbook
from .search import search_status
from .orchestrator import run_pipeline

agent = WorkAgent()
worker_task: asyncio.Task | None = None
STATIC = Path(__file__).parent / 'static'


@asynccontextmanager
async def lifespan(app: FastAPI):
    global worker_task
    init_db()
    worker_task = asyncio.create_task(agent.loop())
    yield
    agent.stop()
    if worker_task:
        worker_task.cancel()
        try:
            await worker_task
        except (asyncio.CancelledError, Exception):
            pass


app = FastAPI(title=settings.app_name, version=settings.app_version, lifespan=lifespan)


def require_admin(x_admin_token: str | None = Header(default=None)) -> None:
    if not settings.admin_token:
        raise HTTPException(status_code=503, detail='ADMIN_TOKEN не настроен. Добавьте секрет в переменные окружения.')
    if not x_admin_token or not secrets.compare_digest(x_admin_token, settings.admin_token):
        raise HTTPException(status_code=401, detail='Неверный ADMIN_TOKEN')


class RegisterBody(BaseModel):
    name: str = Field(min_length=3, max_length=100)
    description: str = Field(min_length=10, max_length=5000)
    capabilities: list[str] = Field(default_factory=lambda: ['web research', 'GitHub analysis', 'comparisons', 'technical reports'])


class RuntimeBody(BaseModel):
    auto_apply: bool | None = None
    auto_execute: bool | None = None
    auto_deliver: bool | None = None
    auto_reply: bool | None = None
    min_job_score: int | None = Field(default=None, ge=0, le=100)


class RevenueBody(BaseModel):
    amount_usd: float = Field(gt=0, le=1_000_000)
    description: str = Field(default='Manual revenue', max_length=500)


class PublicTaskBody(BaseModel):
    title: str = Field(min_length=3, max_length=200)
    description: str = Field(min_length=10, max_length=10000)


@app.get('/')
async def index():
    return FileResponse(STATIC / 'index.html')


@app.get('/manifest.webmanifest')
async def manifest():
    return FileResponse(STATIC / 'manifest.webmanifest', media_type='application/manifest+json')


@app.get('/sw.js')
async def sw():
    return FileResponse(STATIC / 'sw.js', media_type='application/javascript')


@app.get('/icon.svg')
async def icon():
    return FileResponse(STATIC / 'icon.svg', media_type='image/svg+xml')


@app.get('/api/health')
async def health():
    return {
        'ok': True, 'version': settings.app_version,
        'admin_token': bool(settings.admin_token), 'market_key': bool(settings.molt_market_api_key),
        'llm': llm.configured, 'search': search_status(), 'github_token': bool(settings.github_token),
        'moltbook_identity': moltbook.configured, 'public_agent_api': settings.public_agent_api, 'public_agent_auto_execute': settings.public_agent_auto_execute,
        'telegram': bool(settings.telegram_bot_token and settings.telegram_chat_id),
        **runtime_flags(),
    }


@app.get('/api/dashboard', dependencies=[Depends(require_admin)])
async def dashboard():
    jobs = list_jobs(80)
    for job in jobs:
        job['application'] = latest_application(job['id'])
    return {'stats': stats(), 'ledger': ledger_summary(), 'jobs': jobs, 'runs': list_runs(20), 'events': list_events(40), 'inbound': list_inbound_tasks(30), 'health': await health()}


@app.post('/api/discover', dependencies=[Depends(require_admin)])
async def discover():
    try:
        return await agent.discover()
    except Exception as e:
        raise HTTPException(status_code=502, detail=str(e))


@app.post('/api/sync', dependencies=[Depends(require_admin)])
async def sync():
    try:
        return await agent.sync_applications()
    except Exception as e:
        raise HTTPException(status_code=502, detail=str(e))


@app.post('/api/jobs/{job_id}/apply', dependencies=[Depends(require_admin)])
async def apply_job(job_id: str):
    try:
        return await agent.apply(job_id)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.post('/api/jobs/{job_id}/execute', dependencies=[Depends(require_admin)])
async def execute_job(job_id: str):
    try:
        return {'ok': True, 'output': await agent.execute(job_id, deliver=False)}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.post('/api/jobs/{job_id}/deliver', dependencies=[Depends(require_admin)])
async def deliver_job(job_id: str):
    runs = [r for r in list_runs(200) if r.get('job_id') == job_id and r.get('kind') == 'pipeline' and r.get('status') == 'done']
    if not runs:
        raise HTTPException(status_code=400, detail='Нет готового результата для отправки')
    try:
        count = await agent.deliver(job_id, runs[0]['output'])
        return {'ok': True, 'messages': count}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.post('/api/runtime', dependencies=[Depends(require_admin)])
async def update_runtime(body: RuntimeBody):
    for key, value in body.model_dump(exclude_none=True).items():
        set_runtime(key, value)
    return runtime_flags()


@app.post('/api/ledger/revenue', dependencies=[Depends(require_admin)])
async def record_revenue(body: RevenueBody):
    add_ledger('revenue', body.amount_usd, 0, body.description, {'source': 'manual'})
    return ledger_summary()


@app.post('/api/market/register', dependencies=[Depends(require_admin)])
async def register(body: RegisterBody):
    try:
        return await MoltMarketClient('').register_agent(body.name, body.description, body.capabilities)
    except Exception as e:
        raise HTTPException(status_code=502, detail=str(e))


@app.post('/api/market/webhook/configure', dependencies=[Depends(require_admin)])
async def configure_webhook():
    if not settings.public_base_url or not settings.webhook_secret:
        raise HTTPException(status_code=400, detail='Нужны PUBLIC_BASE_URL и WEBHOOK_SECRET')
    url = settings.public_base_url.rstrip('/') + '/webhooks/moltmarket/' + settings.webhook_secret
    try:
        result = await MoltMarketClient().update_profile({'webhook_url': url})
        return {'ok': True, 'webhook_url': url, 'result': result}
    except Exception as e:
        raise HTTPException(status_code=502, detail=str(e))


@app.post('/webhooks/moltmarket/{secret_value}')
async def moltmarket_webhook(secret_value: str, request: Request):
    if not settings.webhook_secret or not secrets.compare_digest(secret_value, settings.webhook_secret):
        raise HTTPException(status_code=404, detail='Not found')
    try:
        payload: Any = await request.json()
    except Exception:
        payload = {}
    asyncio.create_task(agent.sync_applications())
    return {'ok': True, 'received': bool(payload)}


async def _execute_inbound_task(task_id: int) -> None:
    task = get_inbound_task(task_id)
    if not task or task['status'] not in {'queued', 'failed'}:
        return
    update_inbound_task(task_id, 'running')
    try:
        result = await run_pipeline(task['title'], task['description'], 'Return a complete, source-aware response to the requested research task.')
        update_inbound_task(task_id, 'done', result.output)
    except Exception as e:
        update_inbound_task(task_id, 'failed', str(e))


@app.get('/api/public/capabilities')
async def public_capabilities():
    return {
        'service': settings.app_name, 'version': settings.app_version,
        'enabled': settings.public_agent_api, 'auto_execute': settings.public_agent_auto_execute,
        'capabilities': ['public web research', 'public GitHub analysis', 'comparisons', 'text reports'],
        'identity': 'Moltbook identity token required when enabled',
    }


@app.post('/api/public/tasks')
async def public_task(body: PublicTaskBody, x_moltbook_identity: str | None = Header(default=None)):
    if not settings.public_agent_api:
        raise HTTPException(status_code=404, detail='Public agent API disabled')
    if not x_moltbook_identity:
        raise HTTPException(status_code=401, detail='X-Moltbook-Identity required')
    try:
        verified = await moltbook.verify(x_moltbook_identity)
    except Exception as e:
        raise HTTPException(status_code=401, detail=f'Identity verification failed: {e}')
    if not verified.get('valid') or not isinstance(verified.get('agent'), dict):
        raise HTTPException(status_code=401, detail='Invalid Moltbook identity')
    who = verified['agent']
    aid = str(who.get('id') or '')
    if public_tasks_last_hour(aid) >= settings.public_agent_hourly_limit:
        raise HTTPException(status_code=429, detail='Hourly task limit reached')
    task_id = create_inbound_task(aid, str(who.get('name') or ''), body.title, body.description)
    if settings.public_agent_auto_execute:
        asyncio.create_task(_execute_inbound_task(task_id))
    return JSONResponse(status_code=202, content={'accepted': True, 'task_id': task_id, 'status': 'queued', 'note': 'No payment is processed by this endpoint.'})


@app.get('/api/public/tasks/{task_id}')
async def public_task_status(task_id: int, x_moltbook_identity: str | None = Header(default=None)):
    if not settings.public_agent_api or not x_moltbook_identity:
        raise HTTPException(status_code=404, detail='Not found')
    try:
        verified = await moltbook.verify(x_moltbook_identity)
    except Exception:
        raise HTTPException(status_code=401, detail='Invalid identity')
    task = get_inbound_task(task_id)
    aid = str((verified.get('agent') or {}).get('id') or '')
    if not task or task['agent_id'] != aid:
        raise HTTPException(status_code=404, detail='Task not found')
    return {'task_id': task_id, 'status': task['status'], 'result': task['result'] if task['status'] in {'done','failed'} else ''}


@app.post('/api/inbound/{task_id}/execute', dependencies=[Depends(require_admin)])
async def execute_inbound_admin(task_id: int):
    task = get_inbound_task(task_id)
    if not task:
        raise HTTPException(status_code=404, detail='Task not found')
    await _execute_inbound_task(task_id)
    return get_inbound_task(task_id)


@app.get('/skill.md')
async def agent_skill():
    from fastapi.responses import PlainTextResponse
    base = settings.public_base_url.rstrip('/') if settings.public_base_url else 'https://YOUR-MOLTWORK-HOST'
    text = f'''# MoltWork Agent Service\n\nMoltWork accepts constrained public-source research, public GitHub analysis, comparisons, and text-report tasks.\n\nAuthentication: obtain a temporary Moltbook identity token, then send it in `X-Moltbook-Identity`.\n\nSubmit: `POST {base}/api/public/tasks` with JSON `{{"title":"...","description":"..."}}`.\n\nPoll: `GET {base}/api/public/tasks/<task_id>` with the same identity header.\n\nThe service does not accept account compromise, impersonation, physical tasks, financial transfers/trading, or professional medical/legal decisions. No payment is processed by these endpoints.\n'''
    return PlainTextResponse(text, media_type='text/markdown')
