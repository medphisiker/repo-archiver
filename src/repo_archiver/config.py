"""
Модуль для загрузки и валидации конфигурации архивации.

Конфигурация хранится в JSON-файле и определяет:
- Метод и уровень сжатия
- Пути к .gitignore файлам
- Списки директорий для принудительного включения/исключения
- Параметры вывода
- Настройки шифрования
"""

import json
import os
from pathlib import Path
from typing import Any, TypedDict, NotRequired


class CompressionConfig(TypedDict):
    """Конфигурация сжатия ZIP."""
    method: str  # 'stored', 'deflated', 'bzip2', 'lzma'
    level: int  # 0-9 для deflated


class GitignoreConfig(TypedDict):
    """Конфигурация обработки .gitignore."""
    enabled: bool
    paths: list[str]


class EncryptionConfig(TypedDict):
    """Конфигурация шифрования ZIP."""
    enabled: bool
    password_env: NotRequired[str]  # Имя переменной окружения с паролем


class OutputConfig(TypedDict):
    """Конфигурация вывода."""
    filename: str
    directory: NotRequired[str]


class ArchiveConfig(TypedDict):
    """Полная конфигурация архивации."""
    compression: NotRequired[CompressionConfig]
    gitignore: NotRequired[GitignoreConfig]
    encryption: NotRequired[EncryptionConfig]
    force_include: NotRequired[list[str]]
    force_exclude: NotRequired[list[str]]
    output: NotRequired[OutputConfig]


class ConfigError(Exception):
    """Исключение ошибки конфигурации."""
    pass


def load_config(config_path: Path) -> ArchiveConfig:
    """
    Загружает конфигурацию из JSON-файла.

    Args:
        config_path: Путь к конфигурационному файлу

    Returns:
        Словарь с конфигурацией

    Raises:
        ConfigError: Если файл не найден или содержит невалидный JSON
    """
    if not config_path.exists():
        raise ConfigError(f"Конфигурационный файл не найден: {config_path}")

    try:
        with open(config_path, 'r', encoding='utf-8') as f:
            config = json.load(f)
    except json.JSONDecodeError as e:
        raise ConfigError(f"Ошибка парсинга JSON: {e}")

    return _validate_config(config)


def _validate_config(config: dict[str, Any]) -> ArchiveConfig:
    """
    Валидирует структуру конфигурации.

    Args:
        config: Словарь с конфигурацией

    Returns:
        Валидированная конфигурация

    Raises:
        ConfigError: Если конфигурация невалидна
    """
    # Проверяем compression
    if 'compression' in config:
        comp = config['compression']
        valid_methods = {'stored', 'deflated', 'bzip2', 'lzma'}
        if 'method' in comp and comp['method'].lower() not in valid_methods:
            raise ConfigError(
                f"Неверный метод сжатия: {comp['method']}. "
                f"Допустимые: {', '.join(valid_methods)}"
            )
        if 'level' in comp:
            level = comp['level']
            if not isinstance(level, int) or not (0 <= level <= 9):
                raise ConfigError(f"Уровень сжатия должен быть целым числом от 0 до 9")

    # Проверяем gitignore
    if 'gitignore' in config:
        gi = config['gitignore']
        if 'enabled' in gi and not isinstance(gi['enabled'], bool):
            raise ConfigError("gitignore.enabled должен быть boolean")
        if 'paths' in gi and not isinstance(gi['paths'], list):
            raise ConfigError("gitignore.paths должен быть списком")

    # Проверяем force_include и force_exclude
    for key in ('force_include', 'force_exclude'):
        if key in config and not isinstance(config[key], list):
            raise ConfigError(f"{key} должен быть списком строк")

    # Проверяем output
    if 'output' in config:
        out = config['output']
        if 'filename' in out and not isinstance(out['filename'], str):
            raise ConfigError("output.filename должен быть строкой")
        if 'directory' in out and not isinstance(out['directory'], str):
            raise ConfigError("output.directory должен быть строкой")

    # Проверяем encryption
    if 'encryption' in config:
        enc = config['encryption']
        if 'enabled' in enc and not isinstance(enc['enabled'], bool):
            raise ConfigError("encryption.enabled должен быть boolean")
        if 'password_env' in enc and not isinstance(enc['password_env'], str):
            raise ConfigError("encryption.password_env должен быть строкой")

    return config


def get_default_config() -> ArchiveConfig:
    """
    Возвращает конфигурацию по умолчанию.

    Returns:
        Конфигурация по умолчанию
    """
    return ArchiveConfig(
        compression=CompressionConfig(method='deflated', level=9),
        gitignore=GitignoreConfig(enabled=True, paths=['.gitignore']),
        encryption=EncryptionConfig(enabled=False, password_env='ARCHIVE_PASSWORD'),
        force_include=[],
        force_exclude=[],
        output=OutputConfig(filename='repo_archive.zip', directory='.')
    )


def get_password_from_env(config: ArchiveConfig) -> bytes | None:
    """
    Извлекает пароль из переменной окружения, указанной в конфигурации.

    Args:
        config: Конфигурация архивации

    Returns:
        Пароль в байтах или None если шифрование отключено
    """
    encryption = config.get('encryption', {})
    if not encryption.get('enabled', False):
        return None

    password_env = encryption.get('password_env', 'ARCHIVE_PASSWORD')
    password = os.environ.get(password_env)

    if password is None:
        return None

    return password.encode('utf-8')


def merge_configs(
    base: ArchiveConfig,
    override: dict[str, Any]
) -> ArchiveConfig:
    """
    Объединяет две конфигурации, где override имеет приоритет.

    Args:
        base: Базовая конфигурация
        override: Переопределяющая конфигурация

    Returns:
        Объединённая конфигурация
    """
    result = base.copy()

    for key, value in override.items():
        if key == 'output' and key in result:
            # Merge output configs
            result[key] = {**result[key], **value}
        elif key == 'gitignore' and key in result:
            # Merge gitignore configs
            result[key] = {**result[key], **value}
        elif key == 'compression' and key in result:
            # Merge compression configs
            result[key] = {**result[key], **value}
        else:
            result[key] = value

    return result
