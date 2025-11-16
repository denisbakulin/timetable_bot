import asyncio
from json import dumps, loads

from httpx import AsyncClient, ConnectError
from redis import asyncio as aioredis

from app.client.formatter import format_day,  weekdays, format_week
from app.client.parser import parse_timetable
from app.client.serialize import TimeTableResponse, Week, Day
from app.db.user import UserService, UserSchema
from app.db.group import GroupService


from app.settings import bot_settings


cache = aioredis.from_url(
    url=bot_settings.cache_url,
    port=bot_settings.cache_port,
    decode_responses=True
)

from datetime import datetime


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


class PalladaClient:

    async def request(
            self,
            uri: str,
            params: dict | None = None,
            client: AsyncClient | None = None
    ):
        if client is None:
            client = AsyncClient()
        client.base_url = bot_settings.timetable_url

        if params is not None:
            client.params = params
        try:
            async with client as client:
                request_ = await client.get(uri)
                if request_.status_code != 200:
                    return None

                return request_

        except ConnectError as e:
            return None

        except Exception as e:
            return None

    def update_timetable_task(self, all_: bool = False):
        async def wrapper():
            if all_:
                groups = await GroupService().get_any_by()
                groups = [group.name for group in groups]
            else:
                groups = await UserService().get_user_groups()

            for group in groups:
                await self._get_timetable(group, force=True)
                await asyncio.sleep(0.5)
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



    async def _get_timetable(self, group_name: str, force: bool = False) -> TimeTableResponse | None:
        group_name = group_name.upper()
        cached = await cache.get(group_name)

        if cached and not force:
            return TimeTableResponse(**loads(cached))

        group = await GroupService().get_one_by(name=group_name)

        if not group:
            return None

        response = await self.request(f"/group/{group.pallada_id}")

        if response is None:
            if group.timetable is not None:
                return TimeTableResponse(**loads(group.timetable))
            return None

        timetable = parse_timetable(response.text)

        if not force:
            await cache.set(
                group_name, dumps(timetable.model_dump()),
                ex=bot_settings.timetable_update_time_seconds
            )

        await GroupService().update(group.id, timetable=dumps(timetable.model_dump()))


        return timetable


    async def setup_groups(self, start_group_id: int, end_group_id: int):

        count = 0
        for group_id in range(start_group_id, end_group_id):
            client = AsyncClient()
            res = await self.request(f"/group/{group_id}", client=client)

            if res is not None:


                group_service = GroupService()
                group = await group_service.get_one_by(pallada_id=group_id)

                parse = parse_timetable(res.text)

                if group is None:
                    count += 1
                    await group_service.create(pallada_id=group_id, name=parse.group_name)

            await asyncio.sleep(0.5)

        return count

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
            for sub in lesson.sub_lessons:
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



async def main():
    print(await PalladaClient().get_week_timetable("БПИ25-01"))

if __name__ == "__main__":
    asyncio.run(main())

