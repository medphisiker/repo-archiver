"""
Основной модуль для создания ZIP-архивов репозиториев.

Предоставляет функцию create_archive для архивации файлов с учётом:
- Принудительного включения/исключения директорий
- Паттернов .gitignore
- Настроек сжатия
- AES-256 шифрования паролем
"""

import os
from pathlib import Path
import zipfile

import pyzipper

from .config import ArchiveConfig
from .patterns import load_gitignore_patterns, should_exclude_by_pattern


class ArchiveError(Exception):
    """Исключение ошибки архивации."""


class EncryptedZipError(ArchiveError):
    """Исключение ошибки AES-шифрования архива."""


def normalize_rule_path(pattern: str) -> str:
    """Нормализует путь правила без потери ведущей точки у dotfiles."""
    return pattern.removeprefix("./")


def should_exclude(
    file_path: Path,
    root_dir: Path,
    gitignore_patterns: list[str],
    force_include: list[str],
    force_exclude: list[str],
    use_gitignore: bool,
) -> bool:
    """
    Определяет, должен ли файл быть исключён из архива.

    Приоритет проверок (от высшего к низшему):
    1. force_exclude — всегда исключает
    2. force_include — всегда включает (игнорирует gitignore)
    3. gitignore паттерны

    Args:
        file_path: Полный путь к файлу.
        root_dir: Корневая директория репозитория.
        gitignore_patterns: Паттерны из .gitignore.
        force_include: Список директорий для принудительного включения.
        force_exclude: Список директорий для принудительного исключения.
        use_gitignore: Использовать ли паттерны .gitignore.

    Returns:
        True если файл должен быть исключён.
    """
    rel_path = str(file_path.relative_to(root_dir))
    rel_path_parts = file_path.relative_to(root_dir).parts

    for exclude_pattern in force_exclude:
        exclude_pattern = normalize_rule_path(exclude_pattern)
        if rel_path == exclude_pattern:
            return True
        if rel_path.startswith(exclude_pattern + "/"):
            return True
        if rel_path_parts and rel_path_parts[0] == exclude_pattern:
            return True

    for include_pattern in force_include:
        include_pattern = normalize_rule_path(include_pattern)
        if rel_path == include_pattern:
            return False
        if rel_path.startswith(include_pattern + "/"):
            return False

    if use_gitignore and should_exclude_by_pattern(rel_path, gitignore_patterns):
        return True

    return False


def iter_files(root_dir: Path) -> tuple[Path, ...]:
    """
    Возвращает все файлы внутри корневой директории, включая dotfiles.

    Args:
        root_dir: Корневая директория репозитория.

    Returns:
        Кортеж путей к файлам.
    """
    files: list[Path] = []
    for dirpath, _, filenames in os.walk(root_dir):
        current_dir = Path(dirpath)
        for filename in filenames:
            files.append(current_dir / filename)
    return tuple(files)


def create_archive(
    root_dir: Path,
    output_path: Path,
    config: ArchiveConfig,
    verbose: bool = True,
    password: bytes | None = None,
) -> tuple[int, int]:
    """
    Создает ZIP-архив из содержимого репозитория.

    Args:
        root_dir: Корневая директория репозитория.
        output_path: Путь для выходного ZIP-файла.
        config: Конфигурация архивации.
        verbose: Выводить ли подробную информацию.
        password: Пароль для AES-256 шифрования архива в байтах.

    Returns:
        Кортеж (количество файлов, общий размер в байтах).

    Raises:
        ArchiveError: Если не удалось создать архив.
    """
    compression_config = config.get("compression", {})
    compression_method = get_compression_method(compression_config.get("method", "deflated"))
    compression_level = compression_config.get("level", 9)

    gitignore_config = config.get("gitignore", {})
    use_gitignore = gitignore_config.get("enabled", True)
    gitignore_paths = gitignore_config.get("paths", [".gitignore"])

    force_include = config.get("force_include", [])
    force_exclude = config.get("force_exclude", [])

    gitignore_patterns: list[str] = []
    if use_gitignore:
        gitignore_patterns = load_gitignore_patterns(gitignore_paths, root_dir)
        if verbose:
            print(f"Загружено паттернов .gitignore: {len(gitignore_patterns)}")

    if verbose:
        print(f"Принудительно включено: {force_include}")
        print(f"Принудительно исключено: {force_exclude}")
        if password is not None:
            print("Режим архива: AES-256 encrypted ZIP")
        print()

    files_added = 0
    total_size = 0
    excluded_files: list[str] = []
    output_path_resolved = output_path.resolve()

    try:
        with pyzipper.AESZipFile(
            output_path,
            "w",
            compression=compression_method,
            compresslevel=compression_level,
        ) as zip_file:
            if password is not None:
                _enable_aes_encryption(zip_file, password)

            for file_path in iter_files(root_dir):
                if file_path.resolve() == output_path_resolved:
                    continue

                if should_exclude(
                    file_path,
                    root_dir,
                    gitignore_patterns,
                    force_include,
                    force_exclude,
                    use_gitignore,
                ):
                    excluded_files.append(str(file_path.relative_to(root_dir)))
                    continue

                arc_name = file_path.relative_to(root_dir)

                try:
                    zip_file.write(str(file_path), arcname=str(arc_name))
                    file_size = file_path.stat().st_size
                    files_added += 1
                    total_size += file_size
                except Exception as exc:
                    if verbose:
                        print(f"Ошибка добавления файла {file_path}: {exc}")
                    continue
    except Exception as exc:
        raise ArchiveError(f"Ошибка создания архива: {exc}") from exc

    if verbose and excluded_files:
        print("Исключённые файлы:")
        for excluded in sorted(excluded_files)[:20]:
            print(f"  - {excluded}")
        if len(excluded_files) > 20:
            print(f"  ... и ещё {len(excluded_files) - 20}")
        print()

    return files_added, total_size


def _enable_aes_encryption(zip_file: pyzipper.AESZipFile, password: bytes) -> None:
    """
    Включает AES-256 шифрование для новых записей архива.

    Args:
        zip_file: Открытый ZIP-архив.
        password: Пароль в байтах.

    Raises:
        EncryptedZipError: Если пароль пустой.
    """
    if not password:
        raise EncryptedZipError("Пароль для шифрования не может быть пустым")

    zip_file.setpassword(password)
    zip_file.setencryption(pyzipper.WZ_AES, nbits=256)


def get_compression_method(method_name: str) -> int:
    """
    Возвращает константу сжатия ZIP по имени метода.

    Args:
        method_name: Название метода (`stored`, `deflated`, `bzip2`, `lzma`).

    Returns:
        Константа сжатия zipfile.
    """
    methods = {
        "stored": zipfile.ZIP_STORED,
        "deflated": zipfile.ZIP_DEFLATED,
        "bzip2": zipfile.ZIP_BZIP2,
        "lzma": zipfile.ZIP_LZMA,
    }
    return methods.get(method_name.lower(), zipfile.ZIP_DEFLATED)
