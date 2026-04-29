from datetime import datetime
from html import escape

from app.client.serialize import Day, Week

lessons_start = {
    "08:00": 1,
    "09:40": 2,
    "11:30": 3,
    "13:30": 4,
    "15:10": 5,
    "16:50": 6,
    "18:30": 7,
    "20:10": 8,
}

weekdays = ["Понедельник", "Вторник", "Среда", "Четверг", "Пятница", "Суббота", "Воскресенье"]

months = {
    1: "января",
    2: "февраля",
    3: "марта",
    4: "апреля",
    5: "мая",
    6: "июня",
    7: "июля",
    8: "августа",
    9: "сентября",
    10: "октября",
    11: "ноября",
    12: "декабря",
}


def get_week_type_name(week_number: int) -> str:
    return "нечетная" if (week_number + 1) % 2 else "четная"


def format_week_title(week_number: int) -> str:
    return f"{week_number + 1}-я неделя ({get_week_type_name(week_number)})"


def get_russian_date() -> str:
    today = datetime.now()

    return f"{weekdays[today.weekday()]}, {today.day} {months[today.month]}"


def format_day(day: Day, flag=False, today=False) -> str:
    if not today:
        header = f"📅 <b>{day.name}</b>\n" + "▬" * 15
    else:
        header = f"<b>⭐️ Сегодня - {get_russian_date()}\n</b>"

    if flag:
        header += f"{flag}"

    if not day.lessons:
        return f"{header}\n❌ Занятий нет"

    result = [header]

    for lesson in day.lessons:
        lesson_block = format_lesson(lesson)
        if lesson_block:
            result.append(lesson_block)

    if len(result) == 1:
        return f"{header}\n❌ Занятий нет"

    return "\n".join(i for i in result if i).strip()


def format_lesson(lesson, lesson_number: int | None = None) -> str:
    if not lesson.sub_lessons:
        return ""

    lesson_number = lesson_number or lessons_start.get(lesson.start)
    num_emoji = f"{lesson_number}\uFE0F\u20E3" if lesson_number else "📚"
    period = f"{num_emoji} <b>{lesson.start} - {lesson.end}</b>"
    lesson_res = [period]

    for sub_lesson in lesson.sub_lessons:
        subgroup = f"\n{sub_lesson.subgroup + ' Подгруппа ' if sub_lesson.subgroup else ''}"
        block = f"<b>{sub_lesson.name} {subgroup}</b>"

        if sub_lesson.type:
            block += f"<i>({sub_lesson.type})</i>"

        if sub_lesson.teacher:
            teacher = escape(sub_lesson.teacher)
            if sub_lesson.teacher_url:
                teacher = f'<a href="{escape(sub_lesson.teacher_url, quote=True)}">{teacher}</a>'
            block += f"\n👨‍🏫 {teacher}"

        if sub_lesson.place:
            block += f"\n🏫 {sub_lesson.place.strip()}\n"

        lesson_res.append(block)

    return r"<blockquote>" + "\n".join(lesson_res) + "</blockquote>"


def format_week(week: Week) -> str:
    res = []

    for day in week.days:
        res.append(format_day(day))
        res.append("\n\n")

    return f"🕘 {format_week_title(week.number)}\n\n" + "".join(res).strip()
