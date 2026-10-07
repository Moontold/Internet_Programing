from enum import StrEnum


class Role(StrEnum):
    TUTOR = 'tutor'
    PARENT = 'parent'
    STUDENT = 'student'


class LessonFormat(StrEnum):
    OFFLINE = 'offline'
    ONLINE = 'online'


class LessonStatus(StrEnum):
    PLANNED = 'planned'
    HELD = 'held'
    CANCELLED = 'cancelled'
