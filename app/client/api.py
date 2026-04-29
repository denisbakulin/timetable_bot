import asyncio
from json import loads

from httpx import AsyncClient, HTTPError

try:
    from redis import asyncio as aioredis  # type: ignore
except Exception:  # redis is optional (no-redis mode)
    aioredis = None

from app.client.formatter import format_day,  weekdays
from app.client.parser import parse_timetable
from app.client.serialize import TimeTableResponse, Week, Day
from app.db.user import UserService, UserSchema
from app.db.group import GroupService


from app.settings import bot_settings
from app.utils.proxy import normalize_proxy
from datetime import datetime


class _NullCache:
    async def get(self, key: str):  # noqa: ANN001
        return None

    async def set(self, key: str, value: str, ex: int | None = None):  # noqa: ANN001
        return None


def _build_cache():
    if aioredis is None:
        return _NullCache()

    if not bot_settings.cache_url:
        return _NullCache()

    try:
        # Prefer full URL (e.g. redis://localhost:6379/0). Port in URL is enough.
        return aioredis.from_url(bot_settings.cache_url, decode_responses=True)
    except Exception:
        return _NullCache()


cache = _build_cache()




def get_current_week(tt: TimeTableResponse) -> Week:
    today = datetime.now().weekday()

    pallada_today = datetime.strptime(tt.date_, "%d.%m.%Y").weekday()

    if pallada_today == 6 and today == 0:
        return next((week for week in tt.weeks if not week.current), None)

    return next((week for week in tt.weeks if week.current), None)


def get_today(tt: TimeTableResponse) -> Day | None:
    current_week = get_current_week(tt)
    if not current_week:
        return None
    today_week_name = weekdays[datetime.now().weekday()]
    return next((day for day in current_week.days if day.name == today_week_name), None)


def get_tomorrow(tt: TimeTableResponse) -> Day | None:
    tomorrow = datetime.now().weekday() + 1

    if tomorrow == 7:
        next_week = next((week for week in tt.weeks if not week.current), None)
        if next_week is None:
            return None
        return next((day for day in next_week.days if day.name == weekdays[0]), None)

    week = get_current_week(tt)

    if week is None:
        return None

    return next((day for day in week.days if day.name == weekdays[tomorrow]), None)


START_PARSE_GROUP_ID = 13_000
END_PARSE_GROUP_ID = 15_000

class PalladaClient:

    def _make_client(self) -> AsyncClient:
        # Explicit proxy config: we only proxy requests to Pallada, not Telegram.
        return AsyncClient(
            base_url=bot_settings.timetable_url,
            proxy=normalize_proxy(bot_settings.timetable_proxy),
            follow_redirects=True,
        )


    @staticmethod
    async def init():
        groups = await GroupService().get_any_by()

        if not groups:
            await PalladaClient().setup_groups(
                START_PARSE_GROUP_ID, END_PARSE_GROUP_ID
            )

    async def request(
            self,
            uri: str,
            params: dict | None = None,
            client: AsyncClient | None = None
    ):
        uri = uri.lstrip("/")  # keep relative to /timetable

        own_client = client is None
        if own_client:
            client = self._make_client()
        try:
            request_ = await client.get(uri, params=params)
            if request_.status_code != 200:
                return None
            return request_
        except HTTPError:
            return None
        finally:
            if own_client:
                await client.aclose()

    async def _refresh_group_timetable(self, group_name: str) -> TimeTableResponse | None:
        group_name = group_name.upper()
        group = await GroupService().get_one_by(name=group_name)
        if group is None:
            return None

        res = await self.request(f"group/{group.pallada_id}")
        if res is None:
            return None

        try:
            parsed = parse_timetable(res.text)
        except Exception:
            return None
        timetable_json = parsed.model_dump_json()

        await GroupService().update(group.id, timetable=timetable_json)
        try:
            await cache.set(group_name, timetable_json, ex=bot_settings.timetable_update_time_seconds)
        except Exception:
            pass
        return parsed

    async def refresh_group_by_pallada_id(self, pallada_id: int) -> TimeTableResponse | None:
        """
        Fetch timetable from site by pallada_id, upsert Group row (name + timetable),
        and update cache snapshot.
        """
        res = await self.request(f"group/{pallada_id}")
        if res is None:
            return None

        try:
            parsed = parse_timetable(res.text)
        except Exception:
            return None

        timetable_json = parsed.model_dump_json()
        group_service = GroupService()

        group_by_pid = await group_service.get_one_by(pallada_id=pallada_id)
        group_by_name = await group_service.get_one_by(name=parsed.group_name)

        if group_by_pid is not None:
            await group_service.update(group_by_pid.id, name=parsed.group_name, timetable=timetable_json)
        elif group_by_name is not None:
            # Name is the main key used by the bot in many places; keep it consistent.
            await group_service.update(group_by_name.id, pallada_id=pallada_id, timetable=timetable_json)
        else:
            await group_service.create(pallada_id=pallada_id, name=parsed.group_name, timetable=timetable_json)

        try:
            await cache.set(parsed.group_name.upper(), timetable_json, ex=bot_settings.timetable_update_time_seconds)
        except Exception:
            pass

        return parsed

    def update_timetable_task(self, all_: bool = False, inactive: bool = False):
        async def wrapper():
            # Returns tuples: (group_name, users_count)
            active = await UserService().get_user_groups()
            active = [group_name for group_name, _ in active]

            if inactive:
                all_groups = await GroupService().get_any_by()
                all_groups = [g.name for g in all_groups]
                active_set = set(active)
                groups = [g for g in all_groups if g not in active_set]
            elif all_:
                groups = await GroupService().get_any_by()
                groups = [group.name for group in groups]
            else:
                groups = active

            for group in groups:
                # Force refresh from Pallada so the DB/Redis stay up-to-date.
                await self._get_timetable(group, force_refresh=True)
                await asyncio.sleep(1)
        return wrapper

    def process_subgroup(self, user, timetable) -> bool:
        if timetable == "*" or timetable is None or user == 0:
            return True
        return str(user) == timetable

    def user_timetable(self, user: UserSchema, tt: TimeTableResponse) -> TimeTableResponse | None:
        if not tt:
            return None

        for week in tt.weeks:
            for day in week.days:
                for lesson in day.lessons:
                    lesson.sub_lessons = [
                        sub_lesson
                        for sub_lesson in lesson.sub_lessons
                        if self.process_subgroup(user.subgroup, sub_lesson.subgroup)
                    ]
        return tt



    async def _get_timetable(self, group_name: str, force_refresh: bool = False) -> TimeTableResponse | None:
        group_name = group_name.upper()
        try:
            cached = await cache.get(group_name)
        except Exception:
            cached = None

        # 1) Cache
        if cached and not force_refresh:
            return TimeTableResponse(**loads(cached))

        group = await GroupService().get_one_by(name=group_name)

        if not group:
            return None

        # 2) DB snapshot (populate cache for next time)
        if group.timetable and not force_refresh:
            try:
                await cache.set(group_name, group.timetable, ex=bot_settings.timetable_update_time_seconds)
            except Exception:
                pass
            return TimeTableResponse(**loads(group.timetable))

        # 3) Site (only if DB is empty or we force refresh)
        refreshed = await self._refresh_group_timetable(group_name)
        if refreshed is not None:
            return refreshed

        # If we couldn't refresh from the site, fall back to DB if any.
        if group.timetable:
            return TimeTableResponse(**loads(group.timetable))
        return None


    async def setup_groups(self, start_group_id: int, end_group_id: int):

        for group_id in range(start_group_id, end_group_id):
            res = await self.request(f"group/{group_id}")

            if res is not None:

                group_service = GroupService()
                group = await group_service.get_one_by(pallada_id=group_id)

                try:
                    parse = parse_timetable(res.text)
                except Exception:
                    await asyncio.sleep(0.5)
                    continue

                if group is None:
                    await group_service.create(pallada_id=group_id, name=parse.group_name)

            await asyncio.sleep(0.5)


    async def get_today_timetable(self, user: UserSchema):
        timetable = await self._get_timetable(user.group.name)
        timetable = self.user_timetable(user, timetable)

        if not timetable:
            return "Расписание сейчас недоступно 😬"

        today = get_today(timetable)

        if not today or not self.day_have_lessons(today):
            return "❌ На сегодняшний день занятий нет"

        return format_day(today, today=True)

    def day_have_lessons(self, day: Day) -> bool:
        for lesson in day.lessons:
            for _ in lesson.sub_lessons:
                return True
        return False


    async def get_tomorrow_timetable(self, user: UserSchema):
        timetable = await self._get_timetable(user.group.name)
        timetable = self.user_timetable(user, timetable)

        if not timetable:
            return "Расписание сейчас недоступно 😬"

        tomorrow = get_tomorrow(timetable)

        if not tomorrow or not self.day_have_lessons(tomorrow):
            return "❌ На завтрашний день занятий нет"

        return format_day(tomorrow)

