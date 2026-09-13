import httpx
from .config import settings


async def notify_owner(text: str) -> None:
    if not settings.telegram_bot_token or not settings.telegram_chat_id:
        return
    try:
        async with httpx.AsyncClient(timeout=15) as client:
            await client.post(f'https://api.telegram.org/bot{settings.telegram_bot_token}/sendMessage',
                              json={'chat_id': settings.telegram_chat_id, 'text': text[:3900], 'disable_web_page_preview': True})
    except Exception:
        pass
