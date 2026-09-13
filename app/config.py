from functools import lru_cache
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file='.env', env_file_encoding='utf-8', extra='ignore')

    app_name: str = 'MoltWork'
    app_version: str = '1.0.0'
    admin_token: str = ''
    public_base_url: str = ''
    database_path: str = '/data/moltwork.db'

    molt_market_api_key: str = ''
    molt_market_base_url: str = 'https://uzqzlfvfbkhvradsqdls.supabase.co/functions/v1'
    webhook_secret: str = ''

    moltbook_app_key: str = ''
    moltbook_base_url: str = 'https://www.moltbook.com'
    public_agent_api: bool = False
    public_agent_hourly_limit: int = 10
    public_agent_auto_execute: bool = False

    llm_base_url: str = 'https://api.openai.com/v1'
    llm_api_key: str = ''
    llm_model: str = 'gpt-5-mini'
    llm_timeout_seconds: int = 120
    llm_input_cost_per_million: float = 0.0
    llm_output_cost_per_million: float = 0.0
    monthly_llm_budget_usd: float = 25.0

    brave_search_api_key: str = ''
    tavily_api_key: str = ''
    github_token: str = ''

    auto_apply: bool = False
    auto_execute: bool = False
    auto_deliver: bool = False
    auto_reply: bool = False
    min_job_score: int = 70
    max_applications_per_day: int = 5
    max_auto_runs_per_day: int = 5
    max_revision_rounds: int = 2
    min_qa_score: int = 82
    poll_seconds: int = 600
    discovery_seconds: int = 1800
    max_sources: int = 8
    max_source_chars: int = 12000

    telegram_bot_token: str = ''
    telegram_chat_id: str = ''


@lru_cache

def get_settings() -> Settings:
    return Settings()


settings = get_settings()
