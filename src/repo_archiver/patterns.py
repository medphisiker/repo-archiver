"""
Модуль для работы с паттернами .gitignore.

Предоставляет функции для загрузки и проверки соответствия путей паттернам.
"""

import fnmatch
import os
from pathlib import Path


def load_gitignore_patterns(gitignore_paths: list[str], root_dir: Path) -> list[str]:
    """
    Загружает паттерны исключений из файлов .gitignore.

    Args:
        gitignore_paths: Список путей к файлам .gitignore (относительно root_dir)
        root_dir: Корневая директория репозитория

    Returns:
        Список паттернов для исключения
    """
    patterns = []

    for gitignore_path in gitignore_paths:
        full_path = root_dir / gitignore_path
        if not full_path.exists():
            continue

        with open(full_path, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                # Пропускаем пустые строки и комментарии
                if not line or line.startswith('#'):
                    continue
                patterns.append(line)

    return patterns


def matches_pattern(rel_path: str, pattern: str) -> bool:
    """
    Проверяет, соответствует ли путь паттерну .gitignore.

    Поддерживает:
    - Прямое совпадение путей
    - Glob-паттерны (*, ?, [])
    - Паттерны для директорий (заканчивающиеся на /)
    - Паттерны с путями (содержащие /)

    Args:
        rel_path: Относительный путь к файлу
        pattern: Паттерн из .gitignore

    Returns:
        True если путь соответствует паттерну
    """
    # Удаляем ведущий слэш для сравнения
    pattern = pattern.lstrip('/')
    rel_path = rel_path.lstrip('/')

    path_parts = rel_path.split('/')

    # Прямое совпадение всего пути
    if fnmatch.fnmatch(rel_path, pattern):
        return True

    # Совпадение по имени файла (для паттернов без '/')
    if '/' not in pattern:
        # Проверяем имя файла
        if fnmatch.fnmatch(path_parts[-1], pattern):
            return True
        # Проверяем, является ли любая часть пути совпадением (для директорий)
        for part in path_parts:
            if fnmatch.fnmatch(part, pattern):
                return True

    # Совпадение для директорий (паттерн заканчивается на '/')
    if pattern.endswith('/'):
        dir_pattern = pattern.rstrip('/')
        for i, part in enumerate(path_parts[:-1]):  # Исключаем имя файла
            partial_path = '/'.join(path_parts[:i+1])
            if fnmatch.fnmatch(part, dir_pattern):
                return True
            if fnmatch.fnmatch(partial_path, dir_pattern):
                return True

    # Совпадение для путей с '/' (но не заканчивающихся на '/')
    if '/' in pattern and not pattern.endswith('/'):
        if fnmatch.fnmatch(rel_path, pattern):
            return True
        # Проверяем, находится ли файл внутри игнорируемой директории
        pattern_parts = pattern.split('/')
        if len(pattern_parts) > 1:
            pattern_prefix = '/'.join(pattern_parts[:-1])
            if rel_path.startswith(pattern_prefix + '/'):
                return True

    return False


def should_exclude_by_pattern(
    rel_path: str,
    patterns: list[str]
) -> bool:
    """
    Проверяет, должен ли путь быть исключён по списку паттернов.

    Args:
        rel_path: Относительный путь к файлу
        patterns: Список паттернов для проверки

    Returns:
        True если путь соответствует хотя бы одному паттерну
    """
    for pattern in patterns:
        if matches_pattern(rel_path, pattern):
            return True
    return False
