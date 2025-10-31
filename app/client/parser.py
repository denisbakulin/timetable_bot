from bs4 import BeautifulSoup
import httpx
from app.client.serialize import TimeTableResponse,Week, Day, Lesson, SubLesson

import re
def parse_timetable(timetable_html) -> TimeTableResponse:
    bs = BeautifulSoup(timetable_html, "lxml")

    h3_element = bs.find("h3")

    lines = [line.strip() for line in h3_element.stripped_strings]
    group_name = lines[0].strip('"')

    weeks = bs.find_all("div", id=re.compile(r'^week_\d+_tab'))

    timetable = TimeTableResponse(group_name=group_name)

    for number, week in enumerate(weeks):
        days = week.find_all("div", class_="day")
        week = Week(number=number)

        for day in days:
            title = day.find("div", class_="header").find("div", class_="name").text.strip().split()
            lessons = day.find("div", class_="body").find_all("div", class_="line")
            day = Day(name=title[0], today=len(title) == 2)

            for lesson in lessons:
                start, end = (time.strip() for time in
                    lesson.find("div", class_="time").find("div", class_="visible-xs").contents
                    if isinstance(time, str)
                )

                sub_lessons = (
                    lesson.
                    find("div", class_="discipline").
                    find("div", class_="row").
                    find_all("div", class_=re.compile("col-md"))
                )
                lesson = Lesson(start=start, end=end)
                for row in sub_lessons:
                    subgroup = None

                    ul = row.find("ul")
                    elements = ul.find_all("li")

                    if len(elements) == 4:
                        subgroup = (ul.find("li", class_="bold num_pdgrp")
                                    or ul.find("i", class_="fa fa-paperclip").parent)
                        subgroup = subgroup.text.split()[0]

                    name = ul.find("span", class_="name").text
                    type_ = ul.find("i", class_="fa fa-bookmark").parent.contents[2].text.strip()[1:-1]
                    teacher = ul.find("i", class_="fa fa-user").next_element.text
                    place = ul.find("i", class_="fa fa-compass").next_element.text.replace('"', "")


                    sub_lesson = SubLesson(
                        name=name, type=type_, teacher=teacher,
                        place=place, subgroup=subgroup
                    )

                    lesson.sub_lessons.append(sub_lesson)
                day.lessons.append(lesson)
            week.days.append(day)
        timetable.weeks.append(week)

    print(timetable)
    return timetable


