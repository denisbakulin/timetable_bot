from pydantic import BaseModel, Field
from datetime import datetime


class SubLesson(BaseModel):
    name: str
    type: str
    teacher: str
    place: str
    subgroup: str | None = None



class Lesson(BaseModel):
    start: str
    end: str
    sub_lessons: list[SubLesson] = Field(default_factory=list)


class Day(BaseModel):
    name: str
    lessons: list[Lesson] = Field(default_factory=list)


class Week(BaseModel):
    days: list[Day] = Field(default_factory=list)
    number: int
    current: bool


class TimeTableResponse(BaseModel):
    group_name: str
    date_: str
    weeks: list[Week] = Field(default_factory=list)