import re

from bs4 import BeautifulSoup

from app.client.serialize import (Day, Lesson, SubLesson, TimeTableResponse,
                                  Week)
from datetime import datetime

def format_place(place: str) -> str:
    to_remove = ["корп.", "каб.", '"']
    for i in to_remove:
        place = place.replace(i, "")
    return place

def parse_timetable(timetable_html) -> TimeTableResponse:
    bs = BeautifulSoup(timetable_html, "lxml")

    h3_element = bs.find("h3")

    lines = [line.strip() for line in h3_element.stripped_strings]
    group_name = lines[0].strip('"')

    weeks = bs.find_all("div", id=re.compile(r'^week_\d+_tab'))

    week_tab = [week.parent.get("class") for week in bs.find_all(
        "a",
        attrs={
            "data-toggle": "tab",
            "href": re.compile(r'#week_\d+_tab')
        }
    )]

    current_week = 0

    for idx, week_class in enumerate(week_tab):
        if "active" in week_class:
            current_week = idx

    date_ = bs.find("h4").text.replace(" ", "").split("-")[0].strip()
    timetable = TimeTableResponse(group_name=group_name, date_=date_)

    for number, week in enumerate(weeks):
        days = week.find_all("div", class_="day")
        week = Week(number=number, current=number == current_week)

        for day in days:
            title = day.find("div", class_="header").find("div", class_="name").text.strip().split()
            lessons = day.find("div", class_="body").find_all("div", class_="line")
            day = Day(name=title[0])

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
                    place = ul.find("i", class_="fa fa-compass").next_element.text


                    sub_lesson = SubLesson(
                        name=name, type=type_, teacher=teacher,
                        place=format_place(place), subgroup=subgroup
                    )

                    lesson.sub_lessons.append(sub_lesson)
                day.lessons.append(lesson)
            week.days.append(day)
        timetable.weeks.append(week)

    return timetable


