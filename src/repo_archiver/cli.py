"""
CLI интерфейс для repo-archiver.

Предоставляет консольную команду для создания архивов репозиториев
с поддержкой конфигурации через JSON-файл и переопределений из командной строки.
"""

import argparse
import getpass
import os
import sys
from pathlib import Path

from .config import load_config, ConfigError, merge_configs, get_default_config, get_password_from_env
from .archiver import create_archive, ArchiveError


def create_parser() -> argparse.ArgumentParser:
    """
    Создаёт парсер аргументов командной строки.

    Returns:
        Настроенный ArgumentParser
    """
    parser = argparse.ArgumentParser(
        prog='repo-archiver',
        description='Создание ZIP-архива репозитория с JSON-конфигурацией',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Примеры использования:
  repo-archiver                         # Использовать archive_config.json по умолчанию
  repo-archiver -c my_config.json       # Использовать свой конфиг
  repo-archiver -o backup.zip           # Переопределить имя выходного файла
  repo-archiver -r /path/to/repo        # Архивировать другую директорию
  repo-archiver --no-gitignore          # Игнорировать .gitignore паттерны
  repo-archiver --quiet                 # Тихий режим (минимум вывода)
        """
    )

    parser.add_argument(
        '-c', '--config',
        type=str,
        default='archive_config.json',
        help='Путь к JSON-конфигурационному файлу (по умолчанию: archive_config.json)'
    )

    parser.add_argument(
        '-o', '--output',
        type=str,
        help='Имя выходного ZIP-файла (переопределяет конфиг)'
    )

    parser.add_argument(
        '-r', '--root',
        type=str,
        default='.',
        help='Корневая директория репозитория (по умолчанию: текущая директория)'
    )

    parser.add_argument(
        '--no-gitignore',
        action='store_true',
        help='Не использовать паттерны .gitignore'
    )

    parser.add_argument(
        '-q', '--quiet',
        action='store_true',
        help='Тихий режим (минимум вывода)'
    )

    parser.add_argument(
        '-p', '--password',
        type=str,
        help='Пароль для шифрования архива (переопределяет конфиг)'
    )

    parser.add_argument(
        '--password-env',
        type=str,
        help='Имя переменной окружения для чтения пароля (переопределяет конфиг)'
    )

    parser.add_argument(
        '--password-prompt',
        action='store_true',
        help='Интерактивный ввод пароля (не отображается в терминале)'
    )

    parser.add_argument(
        '--version',
        action='version',
        version='%(prog)s 0.1.0'
    )

    return parser


def main() -> int:
    """
    Точка входа для консольной команды repo-archiver.

    Returns:
        Код возврата (0 - успех, 1 - ошибка)
    """
    parser = create_parser()
    args = parser.parse_args()

    root_dir = Path(args.root).resolve()

    # Загружаем конфигурацию
    config_path = Path(args.config)
    if not config_path.is_absolute():
        config_path = root_dir / config_path

    try:
        config = load_config(config_path)
        if not args.quiet:
            print(f"✅ Конфигурация загружена: {config_path}")
    except ConfigError as e:
        print(f"❌ {e}")
        return 1

    # Переопределяем настройки из аргументов командной строки
    overrides = {}
    if args.output:
        overrides['output'] = {'filename': args.output}
    if args.no_gitignore:
        overrides['gitignore'] = {'enabled': False}

    # Объединяем конфигурации
    if overrides:
        config = merge_configs(config, overrides)

    # Определяем путь к выходному файлу
    output_config = config.get('output', {})
    output_filename = output_config.get('filename', 'repo_archive.zip')
    output_directory = output_config.get('directory', '.')

    output_path = Path(output_directory) / output_filename
    if not output_path.is_absolute():
        output_path = root_dir / output_path

    # Убедимся, что путь имеет расширение .zip
    if output_path.suffix.lower() != '.zip':
        output_path = output_path.with_suffix(output_path.suffix + '.zip')

    # Получаем пароль (приоритет: CLI > env > config)
    password: bytes | None = None
    if args.password_prompt:
        password = getpass.getpass("Введите пароль для шифрования архива: ").encode('utf-8')
    elif args.password:
        password = args.password.encode('utf-8')
    elif args.password_env:
        password = os.environ.get(args.password_env, '').encode('utf-8') or None
    else:
        # Пробуем получить пароль из конфигурации
        password = get_password_from_env(config)

    if not args.quiet and password is not None:
        print("🔒 Шифрование включено")

    if not args.quiet:
        print("=" * 60)
        print("📦 Создание архива репозитория")
        print("=" * 60)
        print(f"Корневая директория: {root_dir}")
        print(f"Выходной файл: {output_path}")
        print()

    try:
        files_added, total_size = create_archive(
            root_dir, output_path, config, verbose=not args.quiet, password=password
        )
    except ArchiveError as e:
        print(f"❌ {e}")
        return 1

    if not args.quiet:
        print("=" * 60)

    if files_added > 0:
        if not args.quiet:
            print(f"✅ Архив успешно создан!")
            print(f"   Файлов добавлено: {files_added}")
            print(f"   Исходный размер: {total_size / 1024 / 1024:.2f} MB")

            compressed_size = output_path.stat().st_size
            print(f"   Сжатый размер: {compressed_size / 1024 / 1024:.2f} MB")

            if total_size > 0:
                compression_ratio = (1 - compressed_size / total_size) * 100
                print(f"   Степень сжатия: {compression_ratio:.1f}%")

            print(f"   Путь к архиву: {output_path}")
        return 0
    else:
        print("❌ Не удалось создать архив (файлы не добавлены)")
        return 1


if __name__ == '__main__':
    sys.exit(main())
