"""Импорт-смоук: проверяет, что все модули backend импортируются без ошибок.

Запуск из каталога backend: python scripts/smoke_import.py
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

MODULES = [
    'app.config',
    'app.database',
    'app.schemas.base',
    'app.schemas.health',
    'app.routers.health',
    'app.main',
]


def main() -> int:
    for name in MODULES:
        __import__(name)
        print(f'ok  {name}')
    print(f'\nвсе модули импортированы: {len(MODULES)}')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
