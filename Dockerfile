FROM python:3.13.2-slim

WORKDIR /app

# Устанавливаем uv
COPY --from=ghcr.io/astral-sh/uv:0.10.8 /uv /bin/uv

# Копируем файлы проекта
COPY pyproject.toml .
COPY src/ ./src/

# Устанавливаем зависимости и пакет
RUN uv pip install --system .

# Устанавливаем рабочую директорию для монтирования
WORKDIR /repo

# Точка входа
ENTRYPOINT ["repo-archiver"]
