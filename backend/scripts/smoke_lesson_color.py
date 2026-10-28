"""Смоук-скрипт цвета занятий и переноса проведённого занятия.

Запуск из каталога backend: python scripts/smoke_lesson_color.py
Не требует БД и .env (обязательные настройки подставляются заглушками): проверяет схему, проекцию по роли и правило переноса проведённого.
"""
import os
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

from pydantic import ValidationError

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
for name in ('POSTGRES_DB', 'POSTGRES_USER', 'POSTGRES_PASSWORD', 'TUTOR_LOGIN', 'TUTOR_PASSWORD'):
    os.environ.setdefault(name, 'smoke-check')

from app.core.errors import AppError  # noqa: E402
from app.core.projection import TUTOR_ACCESS, project_short  # noqa: E402
from app.models import Lesson, LessonStatus  # noqa: E402
from app.schemas.lesson import LessonColorUpdate  # noqa: E402
from app.services.lesson_service import check_held_move  # noqa: E402

failed = 0


def check(condition: bool, label: str) -> None:
    global failed
    print(('ok    ' if condition else 'FAIL  ') + label)
    if not condition:
        failed += 1


def rejected(color: str) -> bool:
    try:
        LessonColorUpdate(color=color)
    except ValidationError:
        return True
    return False


def move_error(scope: str, new_start: datetime, now: datetime) -> str:
    try:
        check_held_move(scope=scope, new_start=new_start, duration_minutes=60, now=now)
    except AppError as error:
        return error.message
    return ''


def lesson(color: str | None) -> Lesson:
    start = datetime(2026, 10, 20, 14, 0, tzinfo=timezone.utc)
    return Lesson(
        id=1,
        series_id=1,
        original_start=start,
        scheduled_start=start,
        duration_minutes=60,
        status=LessonStatus.PLANNED,
        detached=False,
        color=color,
        topic='',
        homework_text='',
    )


def main() -> int:
    check(LessonColorUpdate(color='#A1b2C3').color == '#A1b2C3', 'цвет #rrggbb принимается в любом регистре')
    check(LessonColorUpdate().color is None and LessonColorUpdate().scope == 'this', 'по умолчанию: без цвета, только это')
    for bad in ('red', '#abc', 'a1b2c3', '#a1b2c3d', '#gggggg'):
        check(rejected(bad), f'неверный формат отклоняется: {bad!r}')

    inherited = project_short(lesson=lesson(color=None), access=TUTOR_ACCESS, title='', series_color='#336699')
    check(inherited.color == '#336699' and not inherited.own_color, 'без своего цвета — цвет серии')
    own = project_short(lesson=lesson(color='#aa0000'), access=TUTOR_ACCESS, title='', series_color='#336699')
    check(own.color == '#aa0000' and own.own_color, 'свой цвет перекрывает цвет серии')
    plain = project_short(lesson=lesson(color=None), access=TUTOR_ACCESS, title='', series_color=None)
    check(plain.color is None, 'нет ни своего цвета, ни цвета серии — null')

    now = datetime(2026, 10, 28, 12, 0, tzinfo=timezone.utc)
    check(move_error(scope='this', new_start=now - timedelta(days=1), now=now) == '', 'проведённое переносится на вчера')
    check(move_error(scope='this', new_start=now - timedelta(minutes=60), now=now) == '', 'конец ровно сейчас — допустимо')
    check('прошедшее' in move_error(scope='this', new_start=now - timedelta(minutes=30), now=now),
          'конец в будущем — отказ')
    check('прошедшее' in move_error(scope='this', new_start=now + timedelta(days=1), now=now), 'в будущее — отказ')
    for scope in ('following', 'all'):
        check('только с областью' in move_error(scope=scope, new_start=now - timedelta(days=1), now=now),
              f'область {scope!r} для проведённого — отказ')

    if failed:
        print(f'\nпровалено проверок: {failed}')
        return 1
    print('\nвсе проверки пройдены')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
