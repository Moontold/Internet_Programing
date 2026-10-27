"""Импорт-смоук: проверяет, что все модули backend импортируются без ошибок.

Запуск из каталога backend: python scripts/smoke_import.py
Модули находятся обходом пакета app, новый файл попадает в проверку без правки скрипта.
"""

import importlib
import pkgutil
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import app  # noqa: E402


def main() -> int:
    names = ['app', *(module.name for module in pkgutil.walk_packages(app.__path__, prefix='app.'))]
    failed = 0
    for name in names:
        try:
            importlib.import_module(name)
            print(f'ok    {name}')
        except Exception as error:  # noqa: BLE001
            failed += 1
            print(f'FAIL  {name}: {error!r}')
    if failed:
        print(f'\nне импортировались: {failed} из {len(names)}')
        return 1
    print(f'\nвсе модули импортированы: {len(names)}')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
