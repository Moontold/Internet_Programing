from enum import StrEnum


class Role(StrEnum):
    TUTOR = 'tutor'
    PARENT = 'parent'
    STUDENT = 'student'


class LessonFormat(StrEnum):
    OFFLINE = 'offline'
    ONLINE = 'online'
