from __future__ import annotations

from aiogram import Router
from aiogram.filters import Command
from aiogram.types import Message

from app.client.api import PalladaClient
from app.data import ADMIN_HELP_TEXT, ADMIN_TEXT
from app.filters.default import IsAdminFilter


router = Router()
router.message.filter(IsAdminFilter())


def _parse_range_token(token: str) -> tuple[int, int] | None:
    t = token.strip()
    if not t:
        return None

    if "-" in t:
        left, right = (p.strip() for p in t.split("-", 1))
        if not left.isdigit() or not right.isdigit():
            return None
        a, b = int(left), int(right)
        if a > b:
            a, b = b, a
        return a, b

    if t.isdigit():
        v = int(t)
        return v, v

    return None


@router.message(Command("admin"))
async def admin_cmd(message: Message):
    await message.answer(ADMIN_TEXT)


@router.message(Command("admin_help"))
async def admin_help_cmd(message: Message):
    await message.answer(ADMIN_HELP_TEXT, parse_mode="HTML")


@router.message(Command("add_group"))
async def add_group_cmd(message: Message):
    """
    /add_group 13887
    /add_group 13887-13910
    /add_group БИЭ24-01 13900   (name is optional, fetched from site anyway)
    """
    parts = message.text.split(maxsplit=2)
    if len(parts) < 2:
        return await message.answer(
            "Использование:\n"
            "/add_group <pallada_id>\n"
            "/add_group <start-end>\n"
            "/add_group <name> <pallada_id|start-end>"
        )

    token = parts[1] if len(parts) == 2 else parts[2]
    parsed_range = _parse_range_token(token)
    if parsed_range is None:
        return await message.answer("Не понял id/диапазон. Пример: `/add_group 13887` или `/add_group 13887-13910`.")

    start_id, end_id = parsed_range
    client = PalladaClient()

    ok = 0
    failed: list[int] = []
    for pid in range(start_id, end_id + 1):
        res = await client.refresh_group_by_pallada_id(pid)
        if res is None:
            failed.append(pid)
        else:
            ok += 1

    if start_id == end_id:
        if ok:
            return await message.answer(f"Группа #{start_id} добавлена/обновлена.")
        return await message.answer(f"Не удалось добавить группу #{start_id} (сайт не ответил или парсинг упал).")

    msg = f"Диапазон {start_id}-{end_id}: добавлено/обновлено {ok}."
    if failed:
        tail = ", ".join(map(str, failed[:20]))
        more = "" if len(failed) <= 20 else f" (+{len(failed) - 20})"
        msg += f"\nНе удалось: {tail}{more}"
    return await message.answer(msg)

