import asyncio

from httpx import AsyncClient, ConnectError

from redis import asyncio as aioredis
from json import loads, dumps
from datetime import date, time
from app.db.base import session_maker, GroupService
from app.client.serialize import Week, Day, TimeTableResponse

from app.settings import bot_settings
from app.client.parser import parse_timetable


cache = aioredis.from_url(url='redis://localhost', port=6379, decode_responses=True)

lessons_start = {
    "08:00": 1,
    "09:40": 2,
    "11:30": 3,
    "13:30": 4,
    "15:10": 5,
    "16:50": 6,
    "18:30": 7,
    "20:10": 8
}


def format_day(day: Day, today=False) -> str:

    # Заголовок дня
    header = f"📅 <b>{day.name}</b>\n" + "═" * 20 + "\n" if not today else \
             f"<b>⭐️ Сегодня - {date.today().strftime("%d/%m %Y")}</b>"

    if not day.lessons:
        return f"{header}\n❌ Занятий нет"

    result = [header]

    for i, lesson in enumerate(day.lessons, start=1):

        # Эмодзи номера пары
        num_emoji = f"{lessons_start[lesson.start]}\uFE0F\u20E3" if i <= 9 else f"{i}⃣"

        # Заголовок пары
        result.append(f"\n{num_emoji} <b>{lesson.start} - {lesson.end}</b>")

        if not lesson.sub_lessons:
            result.append("  • Нет данных о занятии\n")
            continue



        for sub_lesson in lesson.sub_lessons:
            subgroup = f"{sub_lesson.subgroup + ' Подгруппа' if sub_lesson.subgroup else ''}"

            block = f"<b>{sub_lesson.name} {subgroup}</b>"

            if sub_lesson.type:
                block += f" <i>({sub_lesson.type})</i>"

            if sub_lesson.teacher:
                block += f"\n👨‍🏫 {sub_lesson.teacher}"

            if sub_lesson.place:
                block += f"\n🏫 {sub_lesson.place}\n"

            result.append(block)

        # разделитель между парами
        result.append("────────────────────")

    return "\n".join(result).strip()

def format_week(week: Week) -> str:
    res = []

    for day in week.days:
        res.append(format_day(day))
        res.append(f"\n\n\n")
    return f"📅{week.number}-я Неделя\n\n" + "".join(res).strip()



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
            print(e)
            return None
        except Exception as e:
            print(e)
            return None


    async def _get_timetable(self, group_name) -> TimeTableResponse:
        group_name = group_name.upper()
        cached = await cache.get(group_name)

        if cached:
            return TimeTableResponse(**loads(cached))

        group = await GroupService().get_one_by(name=group_name)
        response = await self.request(f"/group/{group.pallada_id}")

        if response is None:
            return None

        timetable = parse_timetable(response.text)

        await cache.set(
            group_name, dumps(timetable.dict()),
            ex=bot_settings.timetable_update_time_seconds
        )

        return timetable




    async def group_exists(self, name: str) -> bool:
        group = await GroupService().get_one_by(name=name)
        return bool(group)


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

            await asyncio.sleep(0.1)

        return count


    async def get_week_timetable(
            self,
            group: str,
            n: int = 0
    ) -> tuple[Week, str]:
        timetable = await self._get_timetable(group)

        if not timetable or not timetable.weeks:
            return (Week(number=-1), "Расписания нет!")

        week = timetable.weeks[n]

        return week, format_week(week)

    async def get_today_timetable(self, group_name: str):
        timetable = await self._get_timetable(group_name)
        if not timetable:
            return "❌ Не удалось определить сегодняшний день"

        days = [day for week in timetable.weeks for day in week.days]
        today = next((day for day in days if day.today), None)

        if not today:
            return "❌ Не удалось определить сегодняшний день"

        return format_day(today, today=True)




async def main():
    await PalladaClient().setup_groups( 14000, 15000)

if __name__ == "__main__":
    asyncio.run(main())

