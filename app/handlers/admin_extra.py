from __future__ import annotations

from datetime import datetime

from aiogram import F, Router
from aiogram.filters import Command
from aiogram.types import CallbackQuery, Message

import httpx
from sqlalchemy import func, select

from app.client.api import cache
from app.data import ADMIN_HELP_TEXT
from app.db.ban import BanService
from app.db.base import session_maker
from app.db.config import AppConfigService
from app.db.group import Group
from app.db.group_refresh import GroupRefreshService
from app.db.user import User
from app.db.group import GroupService
from app.filters.default import IsAdminFilter
from app.keyboards.kb import (
    AdminGroupsCallback,
    AdminGroupUsersCallback,
    create_admin_groups_kb,
    create_admin_group_users_kb,
)
from app.settings import bot_settings
from app.utils.proxy import normalize_proxy


router = Router()
router.message.filter(IsAdminFilter())
router.callback_query.filter(IsAdminFilter())


@router.message(Command("whereami"))
async def whereami_cmd(message: Message):
    chat_id = message.chat.id
    thread_id = getattr(message, "message_thread_id", None)
    await message.answer(
        "📍 <b>Контекст</b>\n\n"
        f"chat_id: <code>{chat_id}</code>\n"
        f"thread_id: <code>{thread_id}</code>\n"
        f"user_id: <code>{message.from_user.id}</code>\n",
        parse_mode="HTML",
    )


@router.message(Command("dump_config"))
async def dump_config_cmd(message: Message):
    await message.answer(
        "⚙️ <b>Конфиг</b>\n\n"
        f"TIMETABLE_URL: <code>{bot_settings.timetable_url}</code>\n"
        f"TIMETABLE_PROXY: <code>{bot_settings.timetable_proxy or 'off'}</code>\n"
        f"TIMETABLE_UPDATE_TIME_SECONDS: <code>{bot_settings.timetable_update_time_seconds}</code>\n"
        f"CACHE_URL: <code>{bot_settings.cache_url or 'off'}</code>\n"
        f"FSM_REDIS_URL: <code>{bot_settings.fsm_redis_url or 'off'}</code>\n",
        parse_mode="HTML",
    )


@router.message(Command("set_cache_ttl"))
async def set_cache_ttl_cmd(message: Message):
    parts = message.text.split(maxsplit=1)
    if len(parts) < 2 or not parts[1].strip().isdigit():
        return await message.answer("Использование: /set_cache_ttl <секунды>")

    ttl = int(parts[1].strip())
    if ttl < 60 or ttl > 60 * 60 * 24 * 30:
        return await message.answer("TTL должен быть в диапазоне 60..2592000 (30 дней).")

    bot_settings.timetable_update_time_seconds = ttl
    await AppConfigService().set_value("timetable_update_time_seconds", str(ttl))
    await message.answer(f"TIMETABLE_UPDATE_TIME_SECONDS установлен: {ttl}")


@router.message(Command("last_refresh"))
async def last_refresh_cmd(message: Message):
    parts = message.text.split(maxsplit=1)
    if len(parts) < 2:
        return await message.answer("Использование: /last_refresh <group_name|pallada_id>")

    token = parts[1].strip()
    if token.isdigit():
        pid = int(token)
    else:
        grp = await GroupService().get_one_by(name=token.upper())
        if grp is None:
            return await message.answer("Группа не найдена в БД.")
        pid = grp.pallada_id

    row = await GroupRefreshService().get_one_by(pallada_id=pid)
    if row is None:
        return await message.answer("Данных об обновлениях пока нет.")

    when = datetime.fromtimestamp(row.last_refresh_ts).isoformat(sep=" ", timespec="seconds") if row.last_refresh_ts else "never"
    status = "OK" if row.last_ok else "FAIL"
    await message.answer(
        "🕒 <b>Последнее обновление</b>\n\n"
        f"pallada_id: <code>{pid}</code>\n"
        f"when: <code>{when}</code>\n"
        f"status: <code>{status}</code>\n"
        f"error: <code>{row.last_error or '-'}</code>\n",
        parse_mode="HTML",
    )


@router.message(Command("health"))
async def health_cmd(message: Message):
    lines: list[str] = ["🩺 <b>Health</b>\n"]

    # SQLite
    try:
        async with session_maker() as session:
            await session.execute(select(1))
        lines.append("SQLite: ✅")
    except Exception as e:
        lines.append(f"SQLite: ❌ {type(e).__name__}")

    # Redis cache (best effort)
    try:
        await cache.get("__health__")
        lines.append("Cache(Redis): ✅")
    except Exception as e:
        lines.append(f"Cache(Redis): ❌ {type(e).__name__}")

    # Pallada via proxy
    try:
        proxy = normalize_proxy(bot_settings.timetable_proxy)
        async with httpx.AsyncClient(
            base_url=bot_settings.timetable_url,
            proxy=proxy,
            follow_redirects=True,
            timeout=httpx.Timeout(10.0),
            trust_env=False,
        ) as client:
            r = await client.get("")
        lines.append(f"Pallada: ✅ HTTP {r.status_code}")
    except Exception as e:
        lines.append(f"Pallada: ❌ {type(e).__name__}")

    await message.answer("\n".join(lines), parse_mode="HTML")


@router.message(Command("ban_user"))
async def ban_user_cmd(message: Message):
    parts = message.text.split(maxsplit=2)
    if len(parts) < 2 or not parts[1].isdigit():
        return await message.answer("Использование: /ban_user <tg_id> [reason]")
    tg_id = int(parts[1])
    reason = parts[2] if len(parts) >= 3 else ""

    existing = await BanService().get_one_by(tg_id=tg_id)
    if existing is None:
        await BanService().create(tg_id=tg_id, reason=reason)
    else:
        await BanService().update(existing.id, reason=reason)
    await message.answer(f"Пользователь {tg_id} забанен.")


@router.message(Command("unban_user"))
async def unban_user_cmd(message: Message):
    parts = message.text.split(maxsplit=1)
    if len(parts) < 2 or not parts[1].isdigit():
        return await message.answer("Использование: /unban_user <tg_id>")
    tg_id = int(parts[1])
    ok = await BanService().unban(tg_id)
    await message.answer("Разбанен." if ok else "Пользователь не в бан-листе.")


@router.message(Command("group_stats"))
async def group_stats_cmd(message: Message):
    parts = message.text.split(maxsplit=1)
    if len(parts) < 2:
        return await message.answer("Использование: /group_stats <group_name|pallada_id>")

    token = parts[1].strip()
    if token.isdigit():
        grp = await GroupService().get_one_by(pallada_id=int(token))
    else:
        grp = await GroupService().get_one_by(name=token.upper())

    if grp is None:
        return await message.answer("Группа не найдена в БД.")

    async with session_maker() as session:
        total = await session.scalar(select(func.count(User.id)).where(User.pallada_id == grp.pallada_id))
        subscribed = await session.scalar(
            select(func.count(User.id)).where(User.pallada_id == grp.pallada_id).where(User.subscribe.is_(True))
        )
        sg0 = await session.scalar(
            select(func.count(User.id)).where(User.pallada_id == grp.pallada_id).where(User.subgroup == 0)
        )
        sg1 = await session.scalar(
            select(func.count(User.id)).where(User.pallada_id == grp.pallada_id).where(User.subgroup == 1)
        )
        sg2 = await session.scalar(
            select(func.count(User.id)).where(User.pallada_id == grp.pallada_id).where(User.subgroup == 2)
        )

    await message.answer(
        "📌 <b>Group stats</b>\n\n"
        f"Группа: <b>{grp.name}</b> (<code>{grp.pallada_id}</code>)\n"
        f"Пользователей: {int(total or 0)} (подписка: {int(subscribed or 0)})\n"
        f"Подгруппы: *={int(sg0 or 0)}, 1={int(sg1 or 0)}, 2={int(sg2 or 0)}\n",
        parse_mode="HTML",
    )


@router.message(Command("admin_groups"))
async def admin_groups_cmd(message: Message):
    await _send_groups_page(message, page=0, edit=False)


async def _send_groups_page(message_or_cb, *, page: int, edit: bool):
    page_size = 10
    offset = page * page_size

    async with session_maker() as session:
        stmt = (
            select(Group.pallada_id, Group.name, func.count(User.id))
            .select_from(Group)
            .join(User, User.pallada_id == Group.pallada_id, isouter=True)
            .group_by(Group.id)
            .order_by(func.count(User.id).desc(), Group.name.asc())
            .offset(offset)
            .limit(page_size)
        )
        rows = (await session.execute(stmt)).all()

        total = await session.scalar(select(func.count(Group.id)))
        total = int(total or 0)

    text_lines = [f"👥 <b>Группы</b> (стр. {page + 1})", ""]
    if not rows:
        text_lines.append("Пусто.")
    else:
        for pid, name, cnt in rows:
            text_lines.append(f"<code>{pid}</code> {name} — {cnt}")

    text = "\n".join(text_lines)
    kb = create_admin_groups_kb(page=page, total=total, page_size=page_size, rows=rows)

    if isinstance(message_or_cb, CallbackQuery):
        await message_or_cb.message.edit_text(text, reply_markup=kb, parse_mode="HTML")
    else:
        func = message_or_cb.edit_text if edit else message_or_cb.answer
        await func(text, reply_markup=kb, parse_mode="HTML")


@router.callback_query(AdminGroupsCallback.filter())
async def admin_groups_cb(callback: CallbackQuery, callback_data: AdminGroupsCallback):
    await _send_groups_page(callback, page=callback_data.page, edit=True)


@router.callback_query(AdminGroupUsersCallback.filter())
async def admin_group_users_cb(callback: CallbackQuery, callback_data: AdminGroupUsersCallback):
    await _send_group_users_page(callback, pallada_id=callback_data.pallada_id, page=callback_data.page)


async def _send_group_users_page(callback: CallbackQuery, *, pallada_id: int, page: int):
    page_size = 10
    offset = page * page_size

    async with session_maker() as session:
        grp = await session.scalar(select(Group).where(Group.pallada_id == pallada_id))
        if grp is None:
            return await callback.message.edit_text("Группа не найдена.")

        stmt = (
            select(User.tg_id, User.subscribe, User.subgroup, User.notify_time)
            .where(User.pallada_id == pallada_id)
            .order_by(User.tg_id.asc())
            .offset(offset)
            .limit(page_size)
        )
        users = (await session.execute(stmt)).all()

        total = await session.scalar(select(func.count(User.id)).where(User.pallada_id == pallada_id))
        total = int(total or 0)

    lines = [f"👤 <b>{grp.name}</b> (<code>{pallada_id}</code>) стр. {page + 1}", ""]
    if not users:
        lines.append("Пусто.")
    else:
        for tg_id, sub, subgroup, nt in users:
            lines.append(f"<code>{tg_id}</code> sub={'Y' if sub else 'N'} sg={subgroup} nt={nt}")

    kb = create_admin_group_users_kb(pallada_id=pallada_id, page=page, total=total, page_size=page_size)
    await callback.message.edit_text("\n".join(lines), reply_markup=kb, parse_mode="HTML")
