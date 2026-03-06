# repo-archiver

Инструмент для создания ZIP-архивов репозиториев с гибкой конфигурацией через JSON-файл.

## Возможности

- Архивация всего репозитория с историей Git
- Исключение внешних репозиториев и директорий по списку
- Исключение виртуальных окружений и временных файлов
- Принудительное включение директорий (игнорирует .gitignore)
- Настройка уровня и метода сжатия
- Поддержка нескольких .gitignore файлов
- CLI с переопределением настроек из командной строки

## Установка

### Из исходников

```bash
cd tools/repo-archiver
uv pip install -e .
```

### Использование без установки

```bash
uv run python -m repo_archiver [OPTIONS]
```

## Использование

### Базовое использование

```bash
# Использовать archive_config.json по умолчанию
repo-archiver

# Свой конфигурационный файл
repo-archiver -c my_config.json

# Переопределить имя выходного файла
repo-archiver -o backup.zip

# Архивировать другую директорию
repo-archiver -r /path/to/repo

# Игнорировать паттерны .gitignore
repo-archiver --no-gitignore

# Тихий режим (минимум вывода)
repo-archiver --quiet
```

### Как Python-модуль

```python
from pathlib import Path
from repo_archiver import create_archive, load_config

# Загрузить конфигурацию
config = load_config("archive_config.json")

# Создать архив
files_added, total_size = create_archive(
    root_dir=Path("."),
    output_path=Path("archive.zip"),
    config=config,
    verbose=True
)

print(f"Добавлено файлов: {files_added}")
print(f"Общий размер: {total_size / 1024 / 1024:.2f} MB")
```

## Шифрование

Инструмент поддерживает шифрование архива паролем. Пароль можно указать несколькими способами:

```bash
# Из переменной окружения
export ARCHIVE_PASSWORD="my-secret-password"
repo-archiver

# Из другой переменной окружения
repo-archiver --password-env MY_PASSWORD

# Интерактивный ввод (пароль не отображается в терминале)
repo-archiver --password-prompt

# Из командной строки (не рекомендуется для production)
repo-archiver -p "my-secret-password"
```

Приоритет источников пароля (от высшего к низшему):
1. `--password-prompt` — интерактивный ввод
2. `-p/--password` — из командной строки
3. `--password-env` — из указанной переменной окружения
4. Конфигурация (`encryption.password_env`)

## Конфигурация

Создайте файл `archive_config.json` в корневой директории репозитория:

```json
{
  "compression": {
    "method": "deflated",
    "level": 9
  },
  "gitignore": {
    "enabled": true,
    "paths": [
      ".gitignore"
    ]
  },
  "encryption": {
    "enabled": false,
    "password_env": "ARCHIVE_PASSWORD"
  },
  "force_include": [
    "folder_to_include"
  ],
  "force_exclude": [
    ".venv",
    "node_modules",
    "vendor",
    "submodules",
    "dist",
    "build"
  ],
  "output": {
    "filename": "repo_archive.zip",
    "directory": "."
  }
}
```

### Параметры конфигурации

| Параметр | Описание | По умолчанию |
|----------|----------|--------------|
| `compression.method` | Метод сжатия: `stored`, `deflated`, `bzip2`, `lzma` | `deflated` |
| `compression.level` | Уровень сжатия (0-9 для deflated) | `9` |
| `gitignore.enabled` | Использовать ли паттерны .gitignore | `true` |
| `gitignore.paths` | Список путей к файлам .gitignore | `[".gitignore"]` |
| `encryption.enabled` | Включить ли шифрование паролем | `false` |
| `encryption.password_env` | Имя переменной окружения с паролем | `"ARCHIVE_PASSWORD"` |
| `force_include` | Директории для принудительного включения (игнорируют .gitignore) | `[]` |
| `force_exclude` | Директории для принудительного исключения (всегда исключаются) | `[]` |
| `output.filename` | Имя выходного ZIP-файла | `repo_archive.zip` |
| `output.directory` | Директория для сохранения архива | `.` |

### Приоритет исключений

1. **force_exclude** — всегда исключает (высший приоритет)
2. **force_include** — всегда включает (игнорирует .gitignore)
3. **gitignore паттерны** — исключает по паттернам из .gitignore

## Запуск в Docker

```bash
# Получить готовый образ
docker pull medphisiker/repo-archiver:v0.0.1

# Базовый запуск
docker run --rm \
  -v /path/to/repo:/repo \
  -v /path/to/output:/output \
  medphisiker/repo-archiver:v0.0.1 \
  -c /repo/archive_config.json \
  -o /output/archive.zip \
  -r /repo

# С шифрованием (интерактивный ввод пароля)
# Требуется флаг -it для работы getpass
docker run --rm -it \
  -v $(pwd):/repo \
  -v $(pwd):/output \
  medphisiker/repo-archiver:v0.0.1 \
  -c /repo/archive_config.json \
  -o /output/archive.zip \
  -r /repo \
  --password-prompt

# С шифрованием (переменная окружения)
docker run --rm \
  -v $(pwd):/repo \
  -v $(pwd):/output \
  -e ARCHIVE_PASSWORD="my-secret" \
  medphisiker/repo-archiver:v0.0.1 \
  -c /repo/archive_config.json \
  -o /output/archive.zip \
  -r /repo
```

## Примеры

### Архивация проекта с исключением node_modules и .venv

```json
{
  "force_exclude": [".venv", "node_modules", "dist"],
  "force_include": [],
  "output": {
    "filename": "project_archive.zip"
  }
}
```

### Архивация с историей Git, но без внешних подмодулей

```json
{
  "gitignore": {
    "enabled": true,
    "paths": [".gitignore"]
  },
  "force_exclude": ["submodules", "vendor"],
  "force_include": [".git"]
}
```

### Пример архивирования репозитория с docker-контейнером

```bash
# Получить готовый образ
docker pull medphisiker/repo-archiver:v0.0.1

# Запуск (Linux/Mac) — базовый
docker run --rm \
  -v $(pwd):/repo \
  -v $(pwd):/output \
  medphisiker/repo-archiver:v0.0.1 \
  -c /repo/archive_config.json \
  -o /output/archive.zip \
  -r /repo

# Запуск (Linux/Mac) — с интерактивным вводом пароля
docker run --rm -it \
  -v $(pwd):/repo \
  -v $(pwd):/output \
  medphisiker/repo-archiver:v0.0.1 \
  -c /repo/archive_config.json \
  -o /output/archive.zip \
  -r /repo \
  --password-prompt

# Запуск (PowerShell/Windows) — с переменной окружения
docker run --rm `
  -v ${PWD}:/repo `
  -v ${PWD}:/output `
  -e ARCHIVE_PASSWORD="my-secret" `
  medphisiker/repo-archiver:v0.0.1 `
  -c /repo/archive_config.json `
  -o /output/archive.zip `
  -r /repo
```

## Лицензия

MIT
