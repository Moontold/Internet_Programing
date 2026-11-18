"""Смоук-скрипт построителей уведомлений: app.core.notifications.

Запуск из каталога backend: python scripts/smoke_notifications.py
Не требует БД и .env. Тексты и ключи — матрица 4.2 документа
docs/Требования/Спринт 3. Финансы и уведомления.md.
"""
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path
from zoneinfo import ZoneInfo

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.core.notifications import (  # noqa: E402
    Kind, LessonInfo, StudentRow, debt_draft, drafts_to_rows, fmt_date, fmt_money, homework_drafts,
    homework_missing_draft, is_due_soon, lesson_cancelled_drafts, lesson_moved_drafts, lesson_soon_drafts,
    lesson_soon_tutor_draft, needs_homework_reminder, payment_reminder_draft, schedule_changed_drafts,
)

TZ = ZoneInfo('Europe/Moscow')
START = datetime(2026, 10, 20, 14, 0, tzinfo=timezone.utc)  # вт, 20 октября, 17:00 по Москве
LESSON = LessonInfo(lesson_id=7, start=START, series_title='Алгебра', topic='Квадратные уравнения',
                    student_names=('Маша Иванова', 'Петя Иванов'))
# Маша и Петя — дети одного родителя (user 30); Вова — другого (user 31), его учётка отключена
MASHA = StudentRow(student_id=1, student_user_id=11, student_name='Маша Иванова', student_active=True,
                   parent_user_id=30, parent_active=True)
PETYA = StudentRow(student_id=2, student_user_id=12, student_name='Петя Иванов', student_active=True,
                   parent_user_id=30, parent_active=True)
VOVA = StudentRow(student_id=3, student_user_id=13, student_name='Вова Смирнов', student_active=False,
                  parent_user_id=31, parent_active=True)
failed = 0


def check(condition: bool, label: str) -> None:
    global failed
    print(('ok    ' if condition else 'FAIL  ') + label)
    if not condition:
        failed += 1


def by_user(drafts) -> dict[int, list[str]]:
    result: dict[int, list[str]] = {}
    for draft in drafts:
        result.setdefault(draft.user_id, []).append(draft.title)
    return result


def formatting() -> None:
    check(fmt_date(moment=START, tz=TZ) == 'вт, 20 октября, 17:00', 'дата «вт, 20 октября, 17:00»')
    check(fmt_money(amount=2400) == '2 400' and fmt_money(amount=900) == '900', 'сумма с пробелом между разрядами')
    check(LESSON.label == 'Алгебра', 'название — название серии')
    check(LessonInfo(lesson_id=1, start=START, topic='Дроби').label == 'Дроби', 'без серии — тема')
    check(LessonInfo(lesson_id=1, start=START).label == 'Занятие', 'без темы — «Занятие»')


def lesson_soon() -> None:
    drafts = lesson_soon_drafts(lesson=LESSON, rows=[MASHA, VOVA], tz=TZ)
    users = by_user(drafts)
    check(users[11] == ['Скоро занятие: Алгебра, вт, 20 октября, 17:00.'], 'ученику «Скоро занятие»')
    check(users[30] == ['Скоро занятие у ребёнка Маша Иванова: Алгебра, вт, 20 октября, 17:00.'], 'родителю — с именем')
    check(13 not in users, 'деактивированному ученику не создаётся')
    check(users[31] == ['Скоро занятие у ребёнка Вова Смирнов: Алгебра, вт, 20 октября, 17:00.'],
          'активный родитель деактивированного ученика получает')
    moved = lesson_soon_drafts(lesson=LessonInfo(lesson_id=7, start=START + timedelta(hours=2)), rows=[MASHA], tz=TZ)
    old_keys = {item.dedupe_key for item in drafts}
    check(all(item.dedupe_key not in old_keys for item in moved), 'после переноса ключ другой — напоминание снова')
    check(drafts[0].dedupe_key == f'lesson_soon:7:{int(START.timestamp())}:11', 'ключ lesson_soon:{id}:{время}:{user}')
    twins = lesson_soon_drafts(lesson=LESSON, rows=[MASHA, PETYA], tz=TZ)
    parent = [item for item in twins if item.user_id == 30]
    check(len(parent) == 2 and len({item.dedupe_key for item in parent}) == 2, 'двое детей — два уведомления родителю')

    tutor = lesson_soon_tutor_draft(lesson=LESSON, tutor_user_id=1, tz=TZ)
    check(tutor.title == 'Через 30 минут: Алгебра, вт, 20 октября, 17:00. Участники: Маша Иванова, Петя Иванов.',
          'репетитору «Через 30 минут» со списком участников')
    check(tutor.dedupe_key == f'lesson_soon_tutor:7:{int(START.timestamp())}', 'ключ lesson_soon_tutor')


def homework_and_debt() -> None:
    drafts = homework_drafts(lesson=LESSON, rows=[MASHA, PETYA], tz=TZ)
    users = by_user(drafts)
    check(users[11] == ['Домашнее задание к занятию Алгебра, вт, 20 октября, 17:00.'], 'домашка ученику')
    check(sorted(users[30]) == [
        'Домашнее задание для ребёнка Маша Иванова к занятию Алгебра, вт, 20 октября, 17:00.',
        'Домашнее задание для ребёнка Петя Иванов к занятию Алгебра, вт, 20 октября, 17:00.',
    ], 'домашка родителю — по уведомлению на ребёнка')
    check(all(item.dedupe_key and item.kind == Kind.HOMEWORK for item in drafts), 'домашка гасится ключом')
    again = homework_drafts(lesson=LESSON, rows=[MASHA, PETYA], tz=TZ)
    check({item.dedupe_key for item in again} == {item.dedupe_key for item in drafts}, 'повторное сохранение — те же ключи')

    debt = debt_draft(lesson=LESSON, parent_user_id=30, debt=2400)
    check(debt.title == 'Задолженность за занятия: 2 400 ₽.' and debt.dedupe_key == 'debt:7:30', 'долг: текст и ключ')
    reminder = payment_reminder_draft(parent_user_id=30, debt=2400)
    check(reminder.title == 'Напоминание об оплате: задолженность за занятия — 2 400 ₽.', 'напоминание об оплате')
    check(reminder.dedupe_key is None, 'напоминание об оплате повторяемо')


def schedule() -> None:
    cancelled = lesson_cancelled_drafts(lesson=LESSON, rows=[MASHA, PETYA], tz=TZ)
    users = by_user(cancelled)
    check(users[11] == ['Занятие отменено: Алгебра, вт, 20 октября, 17:00.'], 'отмена: ученику')
    check(len(users[30]) == 1, 'отмена: родителю одно уведомление на двоих детей')

    old = START - timedelta(days=1)
    moved = lesson_moved_drafts(lesson=LESSON, rows=[MASHA], old_start=old, tz=TZ)
    check(moved[0].title == 'Занятие перенесено: Алгебра, пн, 19 октября, 17:00 → вт, 20 октября, 17:00.',
          'перенос: старая → новая дата')
    check(all(item.dedupe_key is None for item in moved), 'перенос повторяем')

    changed = schedule_changed_drafts(lesson=LESSON, rows=[MASHA], tz=TZ)
    check(changed[0].title == 'Изменилось расписание: Алгебра, начиная с вт, 20 октября, 17:00. '
                              'Новое расписание — на сайте.', 'изменилось расписание')
    check(sorted(item.user_id for item in changed) == [11, 30], 'изменилось расписание: ученик и родитель по одному')

    missing = homework_missing_draft(lesson=LESSON, tutor_user_id=1, tz=TZ)
    check(missing.title == 'Не задана домашка: Алгебра, вт, 20 октября, 17:00.' and missing.dedupe_key == 'homework_missing:7',
          'нет домашки: текст и ключ')


def windows() -> None:
    now = START - timedelta(hours=23)
    check(is_due_soon(start=START, now=now, lead=timedelta(hours=24)), 'за 23 часа — пора «Скоро занятие»')
    check(not is_due_soon(start=START, now=START - timedelta(hours=25), lead=timedelta(hours=24)), 'за 25 часов — рано')
    check(not is_due_soon(start=START, now=START + timedelta(minutes=1), lead=timedelta(hours=24)), 'начавшееся — нет')
    delay, window = timedelta(hours=1), timedelta(hours=24)
    end = START + timedelta(minutes=60)
    check(needs_homework_reminder(start=START, duration_minutes=60, now=end + timedelta(minutes=61), delay=delay, window=window),
          'через 61 минуту после конца — напомнить')
    check(not needs_homework_reminder(start=START, duration_minutes=60, now=end + timedelta(minutes=30), delay=delay,
                                      window=window), 'через 30 минут — рано')
    check(not needs_homework_reminder(start=START, duration_minutes=60, now=end + timedelta(hours=25), delay=delay,
                                      window=window), 'старше суток — не напоминать (окно после деплоя)')
    long_title = LessonInfo(lesson_id=1, start=START, series_title='А' * 400)
    check(len(drafts_to_rows([homework_missing_draft(lesson=long_title, tutor_user_id=1, tz=TZ)])[0]['title']) == 300,
          'текст обрезается до 300 символов')


def main() -> int:
    formatting()
    lesson_soon()
    homework_and_debt()
    schedule()
    windows()
    if failed:
        print(f'\nпровалено проверок: {failed}')
        return 1
    print('\nALL OK')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
