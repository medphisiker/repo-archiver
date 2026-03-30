# Suite: AES Encryption

## Purpose
Проверить, что [`repo-archiver`](tools/repo-archiver/README.md:1) создаёт настоящий AES-256 ZIP archive, а не только имитирует password protection.

## Requirement Traceability
- **REQ-ENC-001**: Если передан пароль, архив создаётся с AES-256 шифрованием.
- **REQ-ENC-002**: Интерактивный ввод через [`--password-prompt`](tools/repo-archiver/src/repo_archiver/cli.py:84) требует подтверждения и отклоняет пустой пароль.
- **REQ-ENC-003**: Приоритет источников пароля соблюдается: prompt → CLI → explicit env → config env.
- **REQ-ENC-004**: Архив нельзя прочитать без пароля, но можно прочитать с правильным паролем.
- **REQ-ENC-005**: `.gitignore` и force include/exclude продолжают работать в encrypted режиме.

## Test Scripts
- [`test_cli.py`](tools/repo-archiver/tests/test_cli.py)
- [`test_archiver.py`](tools/repo-archiver/tests/test_archiver.py)

## Coverage Matrix
| Test Case | Level | Requirement | Notes |
| :--- | :--- | :--- | :--- |
| `TC-ENC-L1-001` prompt success | L1 | REQ-ENC-002 | Проверяет UTF-8 bytes результат [`prompt_for_password()`](tools/repo-archiver/src/repo_archiver/cli.py:101). |
| `TC-ENC-L1-002` empty prompt rejected | L1 | REQ-ENC-002 | Пустой пароль должен завершаться ошибкой. |
| `TC-ENC-L1-003` mismatch rejected | L1 | REQ-ENC-002 | Подтверждение должно совпадать. |
| `TC-ENC-L1-004` source priority | L1 | REQ-ENC-003 | Проверяет [`resolve_password()`](tools/repo-archiver/src/repo_archiver/cli.py:142). |
| `TC-ENC-L2-001` empty encryption password rejected | L2 | REQ-ENC-001 | Guardrail для [`_enable_aes_encryption()`](tools/repo-archiver/src/repo_archiver/archiver.py:157). |
| `TC-ENC-L2-002` metadata marked encrypted | L2 | REQ-ENC-001 | Проверяет encrypted flag и AES extra field. |
| `TC-ENC-L3-001` read without password fails | L3 | REQ-ENC-004 | Реальный encrypted ZIP не должен читаться без пароля. |
| `TC-ENC-L3-002` read with correct password succeeds | L3 | REQ-ENC-004 | Реальный payload должен восстанавливаться через `pyzipper`. |
| `TC-ENC-L3-003` ignore rules preserved | L3 | REQ-ENC-005 | Проверяет, что `.gitignore` остаётся активным. |
| `TC-ENC-L4-001` CLI env flow | L4 | REQ-ENC-001, REQ-ENC-003, REQ-ENC-004 | Запуск через subprocess: `python -m repo_archiver`. |

## Execution
- Полный прогон: `uv run python -m unittest discover -s tests -p "test_*.py"`
- Точечный прогон suite: `uv run python -m unittest tests.test_cli tests.test_archiver`

## Real Dependencies
- [`pyzipper`](tools/repo-archiver/pyproject.toml:6) как runtime/backend для AES ZIP.
- Реальная файловая система через `tempfile`.
- Реальный subprocess для L4 сценария.
