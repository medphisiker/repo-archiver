# Task: Реорганизовать документацию тестов `repo-archiver` в lazy-loading структуру

## Контекст
- Источник: аудит тестовой документации для [`tools/repo-archiver`](tools/repo-archiver/README.md:1)
- Связанные артефакты: [`tools/repo-archiver/docs/testing/test-map.md`](tools/repo-archiver/docs/testing/test-map.md:1), [`tools/repo-archiver/docs/testing/suites/encryption-aes.md`](tools/repo-archiver/docs/testing/suites/encryption-aes.md:1), [`tools/repo-archiver/tests/test_cli.py`](tools/repo-archiver/tests/test_cli.py:1), [`tools/repo-archiver/tests/test_archiver.py`](tools/repo-archiver/tests/test_archiver.py:1), [`tools/repo-archiver/TESTING_DOCUMENTATION_APPROACH.md`](tools/repo-archiver/TESTING_DOCUMENTATION_APPROACH.md:1)

## Architecture Context References
- [ ] [`tools/repo-archiver/README.md`](tools/repo-archiver/README.md:1)
- [ ] [`tools/repo-archiver/docs/testing/test-map.md`](tools/repo-archiver/docs/testing/test-map.md:1)
- [ ] [`tools/repo-archiver/TESTING_DOCUMENTATION_APPROACH.md`](tools/repo-archiver/TESTING_DOCUMENTATION_APPROACH.md:1)

## Specification References
- [ ] [`tools/repo-archiver/docs/testing/suites/encryption-aes.md`](tools/repo-archiver/docs/testing/suites/encryption-aes.md:1)
- [ ] [`tools/repo-archiver/README.md`](tools/repo-archiver/README.md:238)

## Test Design References
- [ ] [`tools/repo-archiver/docs/testing/test-map.md`](tools/repo-archiver/docs/testing/test-map.md:1)
- [ ] [`tools/repo-archiver/docs/testing/suites/encryption-aes.md`](tools/repo-archiver/docs/testing/suites/encryption-aes.md:17)

## Workflow References
- [ ] `none`
- [ ] Для задачи не требуется отдельный workflow; навигация строится через test map и suite pages

## Цель
- Создать удобную для человека и LLM-агента тестовую документацию `repo-archiver` с progressive disclosure: общая карта покрытия, glossary уровней L1-L4, suite summary и подробные кейсы с точечными ссылками на код тестов, следуя подходу из [`tools/repo-archiver/TESTING_DOCUMENTATION_APPROACH.md`](tools/repo-archiver/TESTING_DOCUMENTATION_APPROACH.md:1).

## Шаги реализации
- [ ] Создать glossary уровней тестирования в [`tools/repo-archiver/docs/testing/levels.md`](tools/repo-archiver/docs/testing/levels.md:1)
- [ ] Обновить [`tools/repo-archiver/docs/testing/test-map.md`](tools/repo-archiver/docs/testing/test-map.md:1), добавив lazy-loading навигацию на glossary, suite и cases pages
- [ ] Расширить [`tools/repo-archiver/docs/testing/suites/encryption-aes.md`](tools/repo-archiver/docs/testing/suites/encryption-aes.md:1) до полного покрытия всех тестов из [`test_cli.py`](tools/repo-archiver/tests/test_cli.py:1) и [`test_archiver.py`](tools/repo-archiver/tests/test_archiver.py:1)
- [ ] Создать подробную страницу кейсов [`tools/repo-archiver/docs/testing/cases/encryption-aes-cases.md`](tools/repo-archiver/docs/testing/cases/encryption-aes-cases.md:1)
- [ ] Проверить, что каждый тестовый метод имеет трассировку `requirement -> suite -> test script -> test case`

## Definition of Done
- [ ] Создан [`tools/repo-archiver/docs/testing/levels.md`](tools/repo-archiver/docs/testing/levels.md:1)
- [ ] [`tools/repo-archiver/docs/testing/test-map.md`](tools/repo-archiver/docs/testing/test-map.md:1) даёт краткую карту и ссылки на следующие уровни детализации
- [ ] [`tools/repo-archiver/docs/testing/suites/encryption-aes.md`](tools/repo-archiver/docs/testing/suites/encryption-aes.md:1) покрывает все актуальные тесты
- [ ] [`tools/repo-archiver/docs/testing/cases/encryption-aes-cases.md`](tools/repo-archiver/docs/testing/cases/encryption-aes-cases.md:1) содержит подробные описания кейсов и ссылки на код
- [ ] Документация подходит как для человека, так и для LLM-агента

## Execution Status
- Current State: Задача создана после аудита тестовой документации `repo-archiver`; реализация ещё не начата.
- Next Step: В новом чате открыть [`tools/repo-archiver/tasks_descriptions/tasks/004-testing-docs-lazy-map.md`](tools/repo-archiver/tasks_descriptions/tasks/004-testing-docs-lazy-map.md:1) и начать с создания glossary [`tools/repo-archiver/docs/testing/levels.md`](tools/repo-archiver/docs/testing/levels.md:1).
- Blockers: none
- Contract Changes: none
- Verification: Наличие задачи [`tools/repo-archiver/tasks_descriptions/tasks/004-testing-docs-lazy-map.md`](tools/repo-archiver/tasks_descriptions/tasks/004-testing-docs-lazy-map.md:1)
