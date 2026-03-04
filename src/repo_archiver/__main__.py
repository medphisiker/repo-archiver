"""
Точка входа для запуска модуля как `python -m repo_archiver`.

Перенаправляет вызов к CLI функции main().
"""

from .cli import main

if __name__ == '__main__':
    main()
