# Справочник API

[← К README проекта](../README.md)

Краткая карта REST API backend для фронтенда и ревью. Полная схема запросов и ответов
с описанием каждого поля — в Swagger UI: `http://localhost/api/docs`.

## 1. Общие правила

- Все пути начинаются с `/api`. Тела запросов и ответов — JSON (кроме загрузки и
  скачивания файлов).
- Каждый ответ — конверт `{error, message, payload}`. Бизнес-ошибка («Неверный логин
  или пароль», «Ученик не найден») приходит с HTTP 200 и `error: true`, текст в `message`
  на русском — его можно показывать пользователю как есть.
- Стандартные коды HTTP:

  | Код | Когда | Что делать фронтенду |
  |---|---|---|
  | `401` | Нет cookie сессии или сессия истекла | Перейти на страницу входа |
  | `403` | Раздел чужой роли или запрос с чужим `Origin` (CSRF) | Показать «Нет доступа» |
  | `422` | Тело или параметры не прошли валидацию | Подсветить форму |

  Тело `401` и `403` — тот же конверт с текстом в `message`.
- **Сессия** — httpOnly-cookie `session` (`SameSite=Lax`, `Secure` при HTTPS), живёт
  `SESSION_DAYS` дней и продлевается при использовании. Запросы шлются с
  `credentials: 'include'`; из JavaScript cookie не читается.
- **CSRF.** `POST`, `PUT`, `PATCH`, `DELETE` принимаются, только если заголовок `Origin`
  (или `Referer`) совпадает с `APP_ORIGIN`. Браузер ставит его сам.
- Время передаётся в ISO 8601 с часовым поясом, хранится в UTC.

## 2. Аутентификация — `/api/auth`

| Метод и путь | Кто | Тело → `payload` | Что делает |
|---|---|---|---|
| `POST /auth/login` | все | `{login, password}` → `Profile` | Вход; ставит cookie сессии. После 10 неудач за 15 минут вход по логину блокируется |
| `POST /auth/logout` | все | — → `null` | Выход: сессия удаляется, cookie стирается |
| `GET /auth/me` | вошедший | — → `Profile` | Текущий пользователь; без входа — `401` |
| `POST /auth/change-password` | вошедший | `{old_password, new_password}` → `null` | Смена своего пароля (не короче 8 символов); остальные сессии пользователя завершаются |

`Profile`: `{id, role: 'tutor' | 'parent' | 'student', full_name, login}`.

## 3. Родители — `/api/parents`

Раздел репетитора: родителю и ученику отвечает `403`.

| Метод и путь | Тело → `payload` | Что делает |
|---|---|---|
| `GET /parents?is_active=` | — → `{parents: Parent[]}` | Список по алфавиту; `is_active=true/false` фильтрует по активности учётки |
| `POST /parents` | `ParentCreate` → `{parent, password}` | Создаёт учётку родителя; пароль задаёт репетитор, в ответе он показывается один раз |
| `GET /parents/{id}` | — → `Parent` | Карточка с детьми |
| `PATCH /parents/{id}` | `ParentUpdate` → `Parent` | Частичная правка; `is_active: false` запрещает вход и завершает сессии |
| `POST /parents/{id}/reset-password` | — → `{password}` | Новый пароль из 10 символов, сессии родителя завершаются |

- `ParentCreate`: `{full_name, login, password, phone?, contacts_note?}`; логин — латиница,
  цифры и `_ . -`, от 3 символов; пароль не короче 8 символов.
- `Parent`: `{id, full_name, phone, login, contacts_note, is_active, children: [{id, full_name, grade, is_active}]}`.

## 4. Ученики — `/api/students`

Раздел репетитора: родителю и ученику отвечает `403`.

| Метод и путь | Тело → `payload` | Что делает |
|---|---|---|
| `GET /students?is_active=` | — → `{students: StudentListItem[]}` | Список по алфавиту с родителем; фильтр «только активные» |
| `POST /students` | `StudentCreate` → `{student, password}` | Создаёт учётку ученика, привязанного к родителю |
| `GET /students/{id}` | — → `Student` | Карточка ученика |
| `PATCH /students/{id}` | `StudentUpdate` → `Student` | Частичная правка; `parent_id` перепривязывает к другому родителю, явный `grade: null` сбрасывает класс, `is_active: false` деактивирует |
| `POST /students/{id}/reset-password` | — → `{password}` | Новый пароль из 10 символов, сессии ученика завершаются |

- `StudentCreate`: `{full_name, login, password, parent_id, grade?: 1..11, grade_note?, format: 'online' | 'offline', price_per_lesson?}`.
- `StudentListItem`: `{id, full_name, grade, grade_note, format, is_active, parent: {id, full_name, phone}}`.
- `Student` = `StudentListItem` + `{login, price_per_lesson, series: Series[]}`, где `series` —
  действующие серии ученика (его регулярное расписание).

Деактивированный ученик или родитель не может войти («Учётная запись отключена»);
данные и история занятий остаются.

## 5. Серии занятий — `/api/series`

Раздел репетитора. Серия — правило «каждые N недель в такое-то время» с датой окончания
или бессрочно; в серии один или несколько учеников.

| Метод и путь | Тело → `payload` | Что делает |
|---|---|---|
| `POST /series` | `SeriesCreate` → `Series` | Создаёт серию и сразу порождает занятия на `SCHEDULE_HORIZON_WEEKS` недель вперёд; прошедшие вхождения рождаются «проведёнными» |
| `PATCH /series/{id}` | `SeriesUpdate` → `Series` | Правка в режиме «все занятия» (см. ниже); явный `until: null` делает серию бессрочной |
| `POST /series/{id}/stop` | `{from_date}` → `Series` | Остановка: с `from_date` занятий нет, проведённые и отменённые остаются |

- `SeriesCreate`: `{first_start, duration_minutes: 15..480, interval_weeks: 1..8, until?, title?, student_ids}`.
- `Series`: `{id, first_start, duration_minutes, interval_weeks, until, title, students: [{id, full_name}]}`.

## 6. Занятия — `/api/lessons`

Раздел репетитора. Удалённые занятия в выборки не попадают.

| Метод и путь | Тело → `payload` | Что делает |
|---|---|---|
| `GET /lessons?start=&end=&student_id=` | — → `{lessons: LessonShort[]}` | Занятия, начинающиеся в `[start, end)` (не больше года), по времени |
| `POST /lessons` | `{scheduled_start, duration_minutes, title?, student_ids}` → `Lesson` | Разовое занятие вне серии; `title` становится темой |
| `GET /lessons/{id}` | — → `Lesson` | Занятие |
| `PATCH /lessons/{id}` | `LessonUpdate` → `Lesson` | Перенос, длительность, состав — с областью `scope`; тема — всегда только у этого занятия |
| `POST /lessons/{id}/cancel` | `{scope: 'this' \| 'following'}` → `Lesson` | Отмена; проведённое тоже можно отменить |
| `DELETE /lessons/{id}?scope=this\|following` | — → `null` | Удаление; проведённое удалить нельзя |

- `LessonShort`: `{id, series_id, scheduled_start, duration_minutes, status: 'planned' | 'held' | 'cancelled',
  detached, topic, title, participants: [{student_id, full_name, price}]}`; `title` — название серии.
- `Lesson` = `LessonShort` + `{original_start}` — исходное место занятия в серии.
- `LessonUpdate`: `{scope: 'this' | 'following' | 'all', scheduled_start?, duration_minutes?, student_ids?, topic?}`.

### Области правки

| `scope` | Перенос, длительность, состав | Отмена | Удаление |
|---|---|---|---|
| `this` — только это | Меняется одно занятие, оно становится отделённым (`detached`) | Занятие отменено | Занятие скрыто |
| `following` — это и последующие | Серия заканчивается накануне, с этого занятия начинается новая с новыми параметрами; последующие перестраиваются, отделённые сохраняют своё время | Серия заканчивается накануне, последующие запланированные снимаются | Это и последующие запланированные скрыты |
| `all` — все занятия | Правило серии сдвигается на ту же дельту, меняются все запланированные неотделённые | — | — |

Правила, общие для всех областей: проведённые занятия не меняются; проведённое нельзя
перенести или удалить, только отменить; отменённое не редактируется; у разового занятия
есть только `this`. Отменённые и удалённые занятия держат своё место в серии — после правки
серии на их неделе новое занятие не появляется. Сдвиг «всех» ровно на целое число периодов
серии (например, на неделю при еженедельной серии) отклоняется.

### Фоновый worker

Отдельный контейнер `worker` (тот же образ, команда `python -m app.worker.main`):

| Период | Задача |
|---|---|
| 1 минута | Запланированные занятия, время которых закончилось, становятся проведёнными |
| 1 час | Действующие серии дополняются занятиями до горизонта; удалённые не порождаются заново |
| 1 сутки | Удаляются истёкшие сессии и записи о попытках входа старше суток |
