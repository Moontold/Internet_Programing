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
- `Student` = `StudentListItem` + `{login, price_per_lesson}`.

Деактивированный ученик или родитель не может войти («Учётная запись отключена»);
данные и история занятий остаются.
