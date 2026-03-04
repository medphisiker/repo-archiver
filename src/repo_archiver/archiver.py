"""
Основной модуль для создания ZIP-архивов репозиториев.

Предоставляет функцию create_archive для архивации файлов с учётом:
- Принудительного включения/исключения директорий
- Паттернов .gitignore
- Настроек сжатия
- Шифрования паролем
"""

import zipfile
from pathlib import Path
from typing import Any

from .config import ArchiveConfig
from .patterns import load_gitignore_patterns, should_exclude_by_pattern


class ArchiveError(Exception):
    """Исключение ошибки архивации."""
    pass


def should_exclude(
    file_path: Path,
    root_dir: Path,
    gitignore_patterns: list[str],
    force_include: list[str],
    force_exclude: list[str],
    use_gitignore: bool
) -> bool:
    """
    Определяет, должен ли файл быть исключён из архива.

    Приоритет проверок (от высшего к низшему):
    1. force_exclude — всегда исключает
    2. force_include — всегда включает (игнорирует gitignore)
    3. gitignore паттерны

    Args:
        file_path: Полный путь к файлу
        root_dir: Корневая директория репозитория
        gitignore_patterns: Паттерны из .gitignore
        force_include: Список директорий для принудительного включения
        force_exclude: Список директорий для принудительного исключения
        use_gitignore: Использовать ли паттерны .gitignore

    Returns:
        True если файл должен быть исключён
    """
    rel_path = str(file_path.relative_to(root_dir))
    rel_path_parts = file_path.relative_to(root_dir).parts

    # 1. Проверяем принудительное исключение (HIGHEST priority)
    for exclude_pattern in force_exclude:
        exclude_pattern = exclude_pattern.lstrip('./')
        # Проверяем точное совпадение или нахождение внутри директории
        if rel_path == exclude_pattern:
            return True
        if rel_path.startswith(exclude_pattern + '/'):
            return True
        # Проверяем по первой части пути (для директорий верхнего уровня)
        if rel_path_parts[0] == exclude_pattern:
            return True

    # 2. Проверяем принудительное включение (overrides gitignore)
    for include_pattern in force_include:
        include_pattern = include_pattern.lstrip('./')
        # Проверяем, находится ли файл в принудительно включаемой директории
        if rel_path == include_pattern:
            return False  # Это сама директория (не должна исключаться)
        if rel_path.startswith(include_pattern + '/'):
            return False  # Файл внутри принудительно включаемой директории

    # 3. Проверяем паттерны .gitignore
    if use_gitignore:
        if should_exclude_by_pattern(rel_path, gitignore_patterns):
            return True

    return False


def create_archive(
    root_dir: Path,
    output_path: Path,
    config: ArchiveConfig,
    verbose: bool = True,
    password: bytes | None = None
) -> tuple[int, int]:
    """
    Создает ZIP-архив из содержимого репозитория.

    Args:
        root_dir: Корневая директория репозитория
        output_path: Путь для выходного ZIP-файла
        config: Конфигурация архивации
        verbose: Выводить ли подробную информацию
        password: Пароль для шифрования архива (в байтах)

    Returns:
        Кортеж (количество файлов, общий размер в байтах)

    Raises:
        ArchiveError: Если не удалось создать архив
    """
    # Извлекаем настройки из конфигурации
    compression_config = config.get('compression', {})
    compression_method = get_compression_method(compression_config.get('method', 'deflated'))
    compression_level = compression_config.get('level', 9)

    gitignore_config = config.get('gitignore', {})
    use_gitignore = gitignore_config.get('enabled', True)
    gitignore_paths = gitignore_config.get('paths', ['.gitignore'])

    force_include = config.get('force_include', [])
    force_exclude = config.get('force_exclude', [])

    # Загружаем паттерны .gitignore
    gitignore_patterns = []
    if use_gitignore:
        gitignore_patterns = load_gitignore_patterns(gitignore_paths, root_dir)
        if verbose:
            print(f"Загружено паттернов .gitignore: {len(gitignore_patterns)}")

    if verbose:
        print(f"Принудительно включено: {force_include}")
        print(f"Принудительно исключено: {force_exclude}")
        print()

    files_added = 0
    total_size = 0
    excluded_files = []

    try:
        with zipfile.ZipFile(
            output_path,
            'w',
            compression=compression_method,
            compresslevel=compression_level
        ) as zip_file:
            for file_path in root_dir.rglob('*'):
                if file_path.is_dir():
                    continue

                if should_exclude(
                    file_path,
                    root_dir,
                    gitignore_patterns,
                    force_include,
                    force_exclude,
                    use_gitignore
                ):
                    excluded_files.append(str(file_path.relative_to(root_dir)))
                    continue

                arc_name = file_path.relative_to(root_dir)

                try:
                    # Добавляем файл с паролем если указан
                    if password is not None:
                        # Для шифрования используем write с pwd
                        zip_file.write(file_path, arc_name, pwd=password)
                    else:
                        zip_file.write(file_path, arc_name)
                    file_size = file_path.stat().st_size
                    files_added += 1
                    total_size += file_size
                except Exception as e:
                    if verbose:
                        print(f"Ошибка добавления файла {file_path}: {e}")
                    continue
    except Exception as e:
        raise ArchiveError(f"Ошибка создания архива: {e}")

    # Выводим список исключённых файлов (для отладки)
    if verbose and excluded_files:
        print("Исключённые файлы:")
        for excluded in sorted(excluded_files)[:20]:  # Показываем первые 20
            print(f"  - {excluded}")
        if len(excluded_files) > 20:
            print(f"  ... и ещё {len(excluded_files) - 20}")
        print()

    return files_added, total_size


def get_compression_method(method_name: str) -> int:
    """
    Возвращает константу сжатия zipfile по имени метода.

    Args:
        method_name: Название метода ('stored', 'deflated', 'bzip2', 'lzma')

    Returns:
        Константа сжатия zipfile
    """
    methods = {
        'stored': zipfile.ZIP_STORED,
        'deflated': zipfile.ZIP_DEFLATED,
        'bzip2': zipfile.ZIP_BZIP2,
        'lzma': zipfile.ZIP_LZMA,
    }
    return methods.get(method_name.lower(), zipfile.ZIP_DEFLATED)
