from aiogram import Router
from aiogram.filters import Command
from aiogram.types import Message

import httpx

from app.db.config import AppConfigService
from app.filters.default import IsAdminFilter
from app.settings import bot_settings
from app.utils.proxy import normalize_proxy


router = Router()
router.message.filter(IsAdminFilter())

async def _check_proxy(proxy_url: str) -> tuple[bool, str]:
    try:
        async with httpx.AsyncClient(
            base_url=bot_settings.timetable_url,
            proxy=proxy_url,
            follow_redirects=True,
            timeout=httpx.Timeout(8.0),
            trust_env=False,
        ) as client:
            # Empty path targets base_url itself (…/timetable).
            resp = await client.get("")
            return True, f"OK (HTTP {resp.status_code})"
    except Exception as e:
        return False, f"FAIL ({type(e).__name__}: {e})"


@router.message(Command("proxy"))
async def proxy_cmd(message: Message):
    """
    Admin command:
    - /proxy -> show current proxy
    - /proxy 212.113.107.128:36613 -> set proxy
    - /proxy off -> disable proxy
    """
    args = message.text.split(maxsplit=1)
    if len(args) == 1:
        current = bot_settings.timetable_proxy or "off"
        return await message.answer(f"TIMETABLE_PROXY: {current}")

    raw = args[1].strip()
    normalized = normalize_proxy(raw)

    svc = AppConfigService()
    if normalized is None:
        await svc.delete_key("timetable_proxy")
        bot_settings.timetable_proxy = None
        return await message.answer("TIMETABLE_PROXY отключен.")

    await svc.set_value("timetable_proxy", normalized)
    bot_settings.timetable_proxy = normalized
    ok, detail = await _check_proxy(normalized)
    suffix = "✅ " + detail if ok else "❌ " + detail
    return await message.answer(f"TIMETABLE_PROXY установлен: {normalized}\nПроверка подключения: {suffix}")
