# Test Map

## Overview
- Контур покрывает AES-256 ZIP encryption, CLI password flow и archive exclusion semantics для [`repo-archiver`](tools/repo-archiver/README.md:1).
- Трассировка поддерживается на уровне `requirement -> suite -> test script`.
- Основная цель контура — доказать не только намерение кода, но и реальный эффект: архив нельзя прочитать без правильного пароля.

## Suites
| Suite | Requirement | Scripts | Status |
| :--- | :--- | :--- | :--- |
| [`encryption-aes.md`](tools/repo-archiver/docs/testing/suites/encryption-aes.md) | AES-256 шифрование ZIP, приоритет источников пароля, подтверждение интерактивного ввода, невозможность чтения без пароля | [`test_cli.py`](tools/repo-archiver/tests/test_cli.py), [`test_archiver.py`](tools/repo-archiver/tests/test_archiver.py) | active |

## Levels
- **L1 / Logic** — валидация [`prompt_for_password()`](tools/repo-archiver/src/repo_archiver/cli.py:101), [`validate_password()`](tools/repo-archiver/src/repo_archiver/cli.py:122), [`resolve_password()`](tools/repo-archiver/src/repo_archiver/cli.py:142).
- **L2 / Contract** — проверка encrypted metadata и guardrails для [`_enable_aes_encryption()`](tools/repo-archiver/src/repo_archiver/archiver.py:157).
- **L3 / System** — реальное создание архива через [`create_archive()`](tools/repo-archiver/src/repo_archiver/archiver.py:82) и чтение через `pyzipper`.
- **L4 / E2E** — запуск `python -m repo_archiver` в subprocess с конфигом и переменной окружения.

## Runbook
- Запуск: `uv run python -m unittest discover -s tests -p "test_*.py"`
- Точечный запуск: `uv run python -m unittest tests.test_cli tests.test_archiver`
- Быстрая проверка синтаксиса: `uv run python -m compileall src tests`
