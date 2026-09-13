import json
import sqlite3
from contextlib import contextmanager
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from .config import settings


def utcnow() -> str:
    return datetime.now(timezone.utc).isoformat()


def _ensure_parent() -> None:
    Path(settings.database_path).parent.mkdir(parents=True, exist_ok=True)


@contextmanager
def conn():
    _ensure_parent()
    db = sqlite3.connect(settings.database_path, check_same_thread=False, timeout=20)
    db.row_factory = sqlite3.Row
    db.execute('PRAGMA journal_mode=WAL')
    db.execute('PRAGMA foreign_keys=ON')
    db.execute('PRAGMA busy_timeout=5000')
    try:
        yield db
        db.commit()
    finally:
        db.close()


def _columns(db: sqlite3.Connection, table: str) -> set[str]:
    return {r['name'] for r in db.execute(f'PRAGMA table_info({table})').fetchall()}


def _add_column(db: sqlite3.Connection, table: str, name: str, ddl: str) -> None:
    if name not in _columns(db, table):
        db.execute(f'ALTER TABLE {table} ADD COLUMN {name} {ddl}')


def init_db() -> None:
    with conn() as db:
        db.executescript('''
        CREATE TABLE IF NOT EXISTS jobs (
            id TEXT PRIMARY KEY, title TEXT NOT NULL, description TEXT DEFAULT '', budget TEXT DEFAULT '',
            skills TEXT DEFAULT '[]', raw TEXT DEFAULT '{}', score INTEGER DEFAULT 0,
            status TEXT DEFAULT 'discovered', fit_reason TEXT DEFAULT '', risk TEXT DEFAULT '',
            created_at TEXT NOT NULL, updated_at TEXT NOT NULL
        );
        CREATE TABLE IF NOT EXISTS applications (
            id INTEGER PRIMARY KEY AUTOINCREMENT, job_id TEXT NOT NULL, external_id TEXT DEFAULT '',
            cover_letter TEXT NOT NULL, status TEXT DEFAULT 'draft', proposed_rate TEXT DEFAULT '',
            created_at TEXT NOT NULL, updated_at TEXT DEFAULT ''
        );
        CREATE TABLE IF NOT EXISTS runs (
            id INTEGER PRIMARY KEY AUTOINCREMENT, job_id TEXT, kind TEXT NOT NULL, status TEXT NOT NULL,
            output TEXT DEFAULT '', meta TEXT DEFAULT '{}', created_at TEXT NOT NULL, updated_at TEXT DEFAULT ''
        );
        CREATE TABLE IF NOT EXISTS deliveries (
            id INTEGER PRIMARY KEY AUTOINCREMENT, job_id TEXT NOT NULL, recipient_id TEXT DEFAULT '',
            status TEXT NOT NULL, message_count INTEGER DEFAULT 0, preview TEXT DEFAULT '', created_at TEXT NOT NULL
        );
        CREATE TABLE IF NOT EXISTS events (
            id INTEGER PRIMARY KEY AUTOINCREMENT, level TEXT NOT NULL, message TEXT NOT NULL,
            data TEXT DEFAULT '{}', created_at TEXT NOT NULL
        );
        CREATE TABLE IF NOT EXISTS ledger (
            id INTEGER PRIMARY KEY AUTOINCREMENT, kind TEXT NOT NULL, amount_usd REAL DEFAULT 0,
            units INTEGER DEFAULT 0, description TEXT DEFAULT '', data TEXT DEFAULT '{}', created_at TEXT NOT NULL
        );
        CREATE TABLE IF NOT EXISTS runtime_settings (
            key TEXT PRIMARY KEY, value TEXT NOT NULL, updated_at TEXT NOT NULL
        );
        CREATE TABLE IF NOT EXISTS inbound_tasks (
            id INTEGER PRIMARY KEY AUTOINCREMENT, agent_id TEXT NOT NULL, agent_name TEXT DEFAULT '',
            title TEXT NOT NULL, description TEXT NOT NULL, status TEXT DEFAULT 'queued',
            result TEXT DEFAULT '', created_at TEXT NOT NULL, updated_at TEXT NOT NULL
        );
        CREATE INDEX IF NOT EXISTS idx_jobs_score ON jobs(score DESC);
        CREATE INDEX IF NOT EXISTS idx_applications_job ON applications(job_id, id DESC);
        CREATE INDEX IF NOT EXISTS idx_events_id ON events(id DESC);
        ''')
        _add_column(db, 'jobs', 'fit_reason', "TEXT DEFAULT ''")
        _add_column(db, 'jobs', 'risk', "TEXT DEFAULT ''")
        _add_column(db, 'applications', 'external_id', "TEXT DEFAULT ''")
        _add_column(db, 'applications', 'proposed_rate', "TEXT DEFAULT ''")
        _add_column(db, 'applications', 'updated_at', "TEXT DEFAULT ''")
        _add_column(db, 'runs', 'meta', "TEXT DEFAULT '{}'")
        _add_column(db, 'runs', 'updated_at', "TEXT DEFAULT ''")


def _json(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, default=str)


def upsert_job(job: dict[str, Any], score: int, fit_reason: str = '', risk: str = '') -> None:
    job_id = str(job.get('id') or job.get('job_id') or '')
    if not job_id:
        return
    now = utcnow()
    title = str(job.get('title') or 'Untitled')
    description = str(job.get('description') or '')
    budget_obj = job.get('budget') or job.get('budget_range') or job.get('price') or job.get('compensation') or ''
    budget = _json(budget_obj) if isinstance(budget_obj, (dict, list)) else str(budget_obj)
    skills = _json(job.get('skills') or [])
    raw = _json(job)
    with conn() as db:
        db.execute('''
        INSERT INTO jobs(id,title,description,budget,skills,raw,score,status,fit_reason,risk,created_at,updated_at)
        VALUES(?,?,?,?,?,?,?,'discovered',?,?,?,?)
        ON CONFLICT(id) DO UPDATE SET title=excluded.title,description=excluded.description,
          budget=excluded.budget,skills=excluded.skills,raw=excluded.raw,score=excluded.score,
          fit_reason=excluded.fit_reason,risk=excluded.risk,updated_at=excluded.updated_at
        ''', (job_id, title, description, budget, skills, raw, score, fit_reason, risk, now, now))


def update_job_status(job_id: str, status: str) -> None:
    with conn() as db:
        db.execute('UPDATE jobs SET status=?, updated_at=? WHERE id=?', (status, utcnow(), job_id))


def list_jobs(limit: int = 100) -> list[dict[str, Any]]:
    with conn() as db:
        rows = db.execute('SELECT * FROM jobs ORDER BY score DESC, updated_at DESC LIMIT ?', (limit,)).fetchall()
    return [dict(r) for r in rows]


def get_job(job_id: str) -> dict[str, Any] | None:
    with conn() as db:
        row = db.execute('SELECT * FROM jobs WHERE id=?', (job_id,)).fetchone()
    return dict(row) if row else None


def save_application(job_id: str, cover_letter: str, status: str = 'draft', external_id: str = '', proposed_rate: str = '') -> int:
    now = utcnow()
    with conn() as db:
        cur = db.execute('''INSERT INTO applications(job_id,external_id,cover_letter,status,proposed_rate,created_at,updated_at)
                          VALUES(?,?,?,?,?,?,?)''', (job_id, external_id, cover_letter, status, proposed_rate, now, now))
        return int(cur.lastrowid)


def latest_application(job_id: str) -> dict[str, Any] | None:
    with conn() as db:
        row = db.execute('SELECT * FROM applications WHERE job_id=? ORDER BY id DESC LIMIT 1', (job_id,)).fetchone()
    return dict(row) if row else None


def sync_application(job_id: str, status: str, external_id: str = '', proposed_rate: str = '') -> None:
    now = utcnow()
    with conn() as db:
        row = db.execute('SELECT id FROM applications WHERE job_id=? ORDER BY id DESC LIMIT 1', (job_id,)).fetchone()
        if row:
            db.execute('''UPDATE applications SET status=?, external_id=CASE WHEN ?<>'' THEN ? ELSE external_id END,
                          proposed_rate=CASE WHEN ?<>'' THEN ? ELSE proposed_rate END, updated_at=? WHERE id=?''',
                       (status, external_id, external_id, proposed_rate, proposed_rate, now, row['id']))
        else:
            db.execute('''INSERT INTO applications(job_id,external_id,cover_letter,status,proposed_rate,created_at,updated_at)
                          VALUES(?,?,?, ?,?,?,?)''', (job_id, external_id, '[synced from market]', status, proposed_rate, now, now))
        db.execute('UPDATE jobs SET status=?, updated_at=? WHERE id=?', (status, now, job_id))


def mark_application(job_id: str, status: str) -> None:
    sync_application(job_id, status)


def count_applications_today() -> int:
    today = datetime.now(timezone.utc).date().isoformat()
    with conn() as db:
        row = db.execute("SELECT COUNT(*) c FROM applications WHERE status NOT IN ('draft','rejected') AND substr(CASE WHEN updated_at<>'' THEN updated_at ELSE created_at END,1,10)=?", (today,)).fetchone()
    return int(row['c'])


def save_run(job_id: str | None, kind: str, status: str, output: str = '', meta: dict[str, Any] | None = None) -> int:
    now = utcnow()
    with conn() as db:
        cur = db.execute('INSERT INTO runs(job_id,kind,status,output,meta,created_at,updated_at) VALUES(?,?,?,?,?,?,?)',
                         (job_id, kind, status, output, _json(meta or {}), now, now))
        return int(cur.lastrowid)


def update_run(run_id: int, status: str, output: str = '', meta: dict[str, Any] | None = None) -> None:
    with conn() as db:
        db.execute('UPDATE runs SET status=?,output=?,meta=?,updated_at=? WHERE id=?',
                   (status, output, _json(meta or {}), utcnow(), run_id))


def has_successful_run(job_id: str) -> bool:
    with conn() as db:
        row = db.execute("SELECT 1 FROM runs WHERE job_id=? AND kind='pipeline' AND status='done' LIMIT 1", (job_id,)).fetchone()
    return bool(row)


def count_runs_today() -> int:
    today = datetime.now(timezone.utc).date().isoformat()
    with conn() as db:
        row = db.execute("SELECT COUNT(*) c FROM runs WHERE kind='pipeline' AND substr(created_at,1,10)=?", (today,)).fetchone()
    return int(row['c'])


def list_runs(limit: int = 30) -> list[dict[str, Any]]:
    with conn() as db:
        rows = db.execute('SELECT * FROM runs ORDER BY id DESC LIMIT ?', (limit,)).fetchall()
    return [dict(r) for r in rows]


def save_delivery(job_id: str, recipient_id: str, status: str, message_count: int, preview: str) -> int:
    with conn() as db:
        cur = db.execute('INSERT INTO deliveries(job_id,recipient_id,status,message_count,preview,created_at) VALUES(?,?,?,?,?,?)',
                         (job_id, recipient_id, status, message_count, preview[:1000], utcnow()))
        return int(cur.lastrowid)


def has_delivery(job_id: str) -> bool:
    with conn() as db:
        row = db.execute("SELECT 1 FROM deliveries WHERE job_id=? AND status='sent' LIMIT 1", (job_id,)).fetchone()
    return bool(row)


def log_event(level: str, message: str, data: dict[str, Any] | None = None) -> None:
    with conn() as db:
        db.execute('INSERT INTO events(level,message,data,created_at) VALUES(?,?,?,?)',
                   (level, message, _json(data or {}), utcnow()))


def list_events(limit: int = 100) -> list[dict[str, Any]]:
    with conn() as db:
        rows = db.execute('SELECT * FROM events ORDER BY id DESC LIMIT ?', (limit,)).fetchall()
    return [dict(r) for r in rows]


def add_ledger(kind: str, amount_usd: float = 0.0, units: int = 0, description: str = '', data: dict[str, Any] | None = None) -> int:
    with conn() as db:
        cur = db.execute('INSERT INTO ledger(kind,amount_usd,units,description,data,created_at) VALUES(?,?,?,?,?,?)',
                         (kind, float(amount_usd), int(units), description, _json(data or {}), utcnow()))
        return int(cur.lastrowid)


def llm_spend_month() -> float:
    month = datetime.now(timezone.utc).strftime('%Y-%m')
    with conn() as db:
        row = db.execute("SELECT COALESCE(SUM(amount_usd),0) s FROM ledger WHERE kind='llm_cost' AND substr(created_at,1,7)=?", (month,)).fetchone()
    return float(row['s'])


def ledger_summary() -> dict[str, float]:
    month = datetime.now(timezone.utc).strftime('%Y-%m')
    with conn() as db:
        cost = db.execute("SELECT COALESCE(SUM(amount_usd),0) s FROM ledger WHERE kind='llm_cost' AND substr(created_at,1,7)=?", (month,)).fetchone()['s']
        revenue = db.execute("SELECT COALESCE(SUM(amount_usd),0) s FROM ledger WHERE kind='revenue' AND substr(created_at,1,7)=?", (month,)).fetchone()['s']
    return {'cost_usd': round(float(cost), 4), 'revenue_usd': round(float(revenue), 2), 'profit_usd': round(float(revenue)-float(cost), 2)}


def set_runtime(key: str, value: Any) -> None:
    with conn() as db:
        db.execute('INSERT INTO runtime_settings(key,value,updated_at) VALUES(?,?,?) ON CONFLICT(key) DO UPDATE SET value=excluded.value,updated_at=excluded.updated_at',
                   (key, _json(value), utcnow()))


def get_runtime(key: str, default: Any = None) -> Any:
    with conn() as db:
        row = db.execute('SELECT value FROM runtime_settings WHERE key=?', (key,)).fetchone()
    if not row:
        return default
    try:
        return json.loads(row['value'])
    except Exception:
        return default


def runtime_flags() -> dict[str, Any]:
    return {
        'auto_apply': get_runtime('auto_apply', settings.auto_apply),
        'auto_execute': get_runtime('auto_execute', settings.auto_execute),
        'auto_deliver': get_runtime('auto_deliver', settings.auto_deliver),
        'auto_reply': get_runtime('auto_reply', settings.auto_reply),
        'min_job_score': int(get_runtime('min_job_score', settings.min_job_score)),
    }


def create_inbound_task(agent_id: str, agent_name: str, title: str, description: str) -> int:
    now = utcnow()
    with conn() as db:
        cur = db.execute('INSERT INTO inbound_tasks(agent_id,agent_name,title,description,status,result,created_at,updated_at) VALUES(?,?,?,?,\'queued\',\'\',?,?)',
                         (agent_id, agent_name, title, description, now, now))
        return int(cur.lastrowid)


def get_inbound_task(task_id: int) -> dict[str, Any] | None:
    with conn() as db:
        row = db.execute('SELECT * FROM inbound_tasks WHERE id=?', (task_id,)).fetchone()
    return dict(row) if row else None


def list_inbound_tasks(limit: int = 50) -> list[dict[str, Any]]:
    with conn() as db:
        rows = db.execute('SELECT * FROM inbound_tasks ORDER BY id DESC LIMIT ?', (limit,)).fetchall()
    return [dict(r) for r in rows]


def update_inbound_task(task_id: int, status: str, result: str = '') -> None:
    with conn() as db:
        db.execute('UPDATE inbound_tasks SET status=?, result=?, updated_at=? WHERE id=?', (status, result, utcnow(), task_id))


def public_tasks_last_hour(agent_id: str) -> int:
    with conn() as db:
        row = db.execute("SELECT COUNT(*) c FROM inbound_tasks WHERE agent_id=? AND julianday(created_at)>=julianday('now','-1 hour')", (agent_id,)).fetchone()
    return int(row['c'])


def stats() -> dict[str, Any]:
    flags = runtime_flags()
    with conn() as db:
        jobs = db.execute('SELECT COUNT(*) c FROM jobs').fetchone()['c']
        good = db.execute('SELECT COUNT(*) c FROM jobs WHERE score>=?', (flags['min_job_score'],)).fetchone()['c']
        drafts = db.execute("SELECT COUNT(*) c FROM applications WHERE status='draft'").fetchone()['c']
        applied = db.execute("SELECT COUNT(*) c FROM applications WHERE status IN ('applied','pending')").fetchone()['c']
        accepted = db.execute("SELECT COUNT(*) c FROM applications WHERE status IN ('accepted','in_progress')").fetchone()['c']
        completed = db.execute("SELECT COUNT(*) c FROM runs WHERE kind='pipeline' AND status='done'").fetchone()['c']
    return {'jobs': jobs, 'qualified': good, 'drafts': drafts, 'applied': applied, 'accepted': accepted, 'completed': completed}
