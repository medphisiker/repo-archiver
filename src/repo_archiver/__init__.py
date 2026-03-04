"""
repo-archiver — Инструмент для создания ZIP-архивов репозиториев.

Поддерживает:
- Гибкую конфигурацию через JSON-файлы
- Принудительное включение/исключение директорий
- Паттерны .gitignore
- Различные методы сжатия (deflated, bzip2, lzma)
- Шифрование паролем

Пример использования:
    >>> from repo_archiver import create_archive, load_config, get_password_from_env
    >>> config = load_config("archive_config.json")
    >>> password = get_password_from_env(config)
    >>> files_added, total_size = create_archive(
    ...     root_dir=Path("."),
    ...     output_path=Path("archive.zip"),
    ...     config=config,
    ...     password=password
    ... )
"""

__version__ = "0.1.0"
__author__ = "Your Name"
__all__ = [
    "__version__",
    "create_archive",
    "load_config",
    "get_password_from_env",
    "ArchiveError",
    "ConfigError",
]

from .archiver import create_archive, ArchiveError
from .config import load_config, ConfigError, get_password_from_env
