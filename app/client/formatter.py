from datetime import datetime

from app.client.serialize import Day, Week

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

weekdays = ["Понедельник", "Вторник", "Среда", "Четверг", "Пятница", "Суббота", "Воскресенье"]

months = {
    1: "января", 2: "февраля", 3: "марта", 4: "апреля",
    5: "мая", 6: "июня", 7: "июля", 8: "августа",
    9: "сентября", 10: "октября", 11: "ноября", 12: "декабря"
}

def get_russian_date():

    today = datetime.now()

    return f"{weekdays[today.weekday()]}, {today.day} {months[today.month]}"


def format_day(day: Day, flag=False, today=False) -> str:

    if not today:
        header = f"📅 <b>{day.name}</b>\n" + "▬"*15
    else:

        header = f"<b>⭐️ Сегодня - {get_russian_date()}\n</b>"

    if flag:
        header += f"{flag}"

    if not day.lessons:
        return f"{header}\n❌ Занятий нет"

    result = [header]

    for i, lesson in enumerate(day.lessons, start=1):

        # Эмодзи номера пары
        num_emoji = f"{lessons_start[lesson.start]}\uFE0F\u20E3" if i <= 9 else f"{i}⃣ "

        # Заголовок пары
        period = f"{num_emoji} <b>{lesson.start} - {lesson.end}</b>"


        lesson_res = [period]

        for sub_lesson in lesson.sub_lessons:
            subgroup = f"\n{sub_lesson.subgroup + ' Подгруппа ' if sub_lesson.subgroup else ''}"

            block = f"<b>{sub_lesson.name} {subgroup}</b>"

            if sub_lesson.type:
                block += f"<i>({sub_lesson.type})</i>"

            if sub_lesson.teacher:
                block += f"\n👨‍🏫 {sub_lesson.teacher}"

            if sub_lesson.place:
                block += f"\n🏫 {sub_lesson.place.strip()}\n"

            lesson_res.append(block)

        if len(lesson_res) != 1:

            result.append(
                r'<blockquote>'
                f"{'\n'.join(lesson_res)}"
                "</blockquote>"
            )

    return "\n".join(i for i in result if i).strip() if len(result) > 1 else ""

def format_week(week: Week) -> str:
    res = []

    for day in week.days:
        res.append(format_day(day))
        res.append(f"\n\n")

    return f"🕘 {week.number+1}-я Неделя\n\n" + "".join(res).strip()
