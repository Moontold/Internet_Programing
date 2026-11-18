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


class HomeworkStatus(StrEnum):
    NOT_CHECKED = 'not_checked'
    DONE = 'done'
    NOT_DONE = 'not_done'


class NotificationKind(StrEnum):
    LESSON_SOON = 'lesson_soon'
    LESSON_SOON_TUTOR = 'lesson_soon_tutor'
    HOMEWORK = 'homework'
    DEBT = 'debt'
    LESSON_CANCELLED = 'lesson_cancelled'
    LESSON_MOVED = 'lesson_moved'
    SCHEDULE_CHANGED = 'schedule_changed'
    HOMEWORK_MISSING = 'homework_missing'
    PAYMENT_REMINDER = 'payment_reminder'


class VkState(StrEnum):
    """Доставка уведомления во ВКонтакте (бот — в спринте 4); на сайте запись видна сразу."""

    PENDING = 'pending'
    SENT = 'sent'
    SKIPPED = 'skipped'
    FAILED = 'failed'
