from __future__ import annotations

from aiogram import Router
from aiogram.filters import Command
from aiogram.types import Message

from sqlalchemy import func, select

from app.client.api import PalladaClient
from app.data import ADMIN_HELP_TEXT, ADMIN_TEXT
from app.db.base import session_maker
from app.db.group import Group
from app.db.user import User
from app.db.user import UserService
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


async def _refresh_range(message: Message, start_id: int, end_id: int, *, ok_word: str = "обновлена"):
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
            return await message.answer(f"Группа #{start_id} {ok_word}.")
        return await message.answer(f"Не удалось обработать группу #{start_id}.")

    msg = f"Диапазон {start_id}-{end_id}: обработано {ok}."
    if failed:
        tail = ", ".join(map(str, failed[:20]))
        more = "" if len(failed) <= 20 else f" (+{len(failed) - 20})"
        msg += f"\nНе удалось: {tail}{more}"
    return await message.answer(msg)


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
    return await _refresh_range(message, start_id, end_id, ok_word="добавлена/обновлена")


@router.message(Command("refresh_group"))
async def refresh_group_cmd(message: Message):
    """
    /refresh_group 13887
    /refresh_group 13887-13910
    """
    parts = message.text.split(maxsplit=1)
    if len(parts) < 2:
        return await message.answer("Использование: /refresh_group <pallada_id|start-end>")

    parsed_range = _parse_range_token(parts[1])
    if parsed_range is None:
        return await message.answer("Не понял id/диапазон. Пример: /refresh_group 13887-13910")

    start_id, end_id = parsed_range
    return await _refresh_range(message, start_id, end_id, ok_word="обновлена")


@router.message(Command("admin_stats"))
async def admin_stats_cmd(message: Message):
    async with session_maker() as session:
        total_users = await session.scalar(select(func.count(User.id)))
        subscribed_users = await session.scalar(select(func.count(User.id)).where(User.subscribe.is_(True)))
        total_groups = await session.scalar(select(func.count(Group.id)))
        groups_with_tt = await session.scalar(
            select(func.count(Group.id)).where(Group.timetable.is_not(None)).where(Group.timetable != "")
        )
        active_groups = await session.scalar(
            select(func.count(func.distinct(User.pallada_id))).where(User.pallada_id.is_not(None))
        )

    total_users = int(total_users or 0)
    subscribed_users = int(subscribed_users or 0)
    total_groups = int(total_groups or 0)
    groups_with_tt = int(groups_with_tt or 0)
    active_groups = int(active_groups or 0)

    await message.answer(
        "📊 <b>Статистика</b>\n\n"
        f"Пользователи: {total_users} (подписка: {subscribed_users})\n"
        f"Группы в БД: {total_groups}\n"
        f"Группы с расписанием: {groups_with_tt}\n"
        f"Активные группы (есть пользователи): {active_groups}\n\n"
        "Команды:\n"
        "/admin_help\n"
        "/add_group\n"
        "/proxy\n",
        parse_mode="HTML",
    )


@router.message(Command("admin_users"))
async def admin_users_cmd(message: Message):
    # Kept for backward compatibility; interactive view is in /admin_groups.
    groups = await UserService().get_user_groups()
    if not groups:
        return await message.answer("Пользователей с выбранной группой пока нет.")

    lines = ["👥 <b>Группы по пользователям</b>\n", "Интерактивно: /admin_groups\n"]
    for name, count in sorted(groups, key=lambda x: x[1], reverse=True)[:20]:
        lines.append(f"{name}: {count}")
    await message.answer("\n".join(lines), parse_mode="HTML")
