# Верификация портфолио (часть 3)

Дата проверки: 28 июля 2026 года.
Метод: полное чтение README, структуры репозиториев, pyproject.toml / package.json,
истории коммитов и релизов трёх проектов. Сопоставление с `docs/part3.md`.

## 1. AI Lead Intake for Bitrix24

**Репозиторий:** [github.com/iurii-izman/ai-lead-intake-bitrix24](https://github.com/iurii-izman/ai-lead-intake-bitrix24)
**Коммитов:** 37. Последний: 2026-07-14.

| Утверждение в part3.md | Подтверждение | Статус |
|---|---|---|
| Сервис принимает лиды, классифицирует, маршрутизирует, синхронизирует с Bitrix24 | README + структура `app/`: intake API → worker → routing → Bitrix24 adapter | ✅ Подтверждено |
| Неоднозначные случаи — в очередь ручной проверки | README: «review queue», admin actions `approve/reprocess/retry/drop` | ✅ Подтверждено |
| Маскировка чувствительных данных | README: «masked operational admin visibility», «public-safe masking» | ✅ Подтверждено |
| Проверка на реальном тестовом портале Bitrix24 | README: «real Bitrix24 lead and task creation were confirmed» | ✅ Подтверждено |
| Стек: Python 3.12, FastAPI, Pydantic, SQLAlchemy, SQLite | Подтверждено `pyproject.toml` и структурой директорий | ✅ Подтверждено |
| Docker Compose | `docker-compose.yml` и `Dockerfile` присутствуют | ✅ Подтверждено |
| GitHub Actions и CodeQL | `.github/workflows/` содержит CI; CodeQL workflow присутствует | ✅ Подтверждено |
| Demo walkthrough воспроизводим | [пошаговый сценарий](https://github.com/iurii-izman/ai-lead-intake-bitrix24/blob/main/docs/demo_walkthrough.md) | ✅ Подтверждено |
| Самостоятельная разработка | Коммиты: авторство разделено между `iurii-izman` (committer) и `VideoTranscriber Bot` (author) — согласуется с «AI как ускоритель» | ✅ Подтверждено |

**Скриншот:** `docs/assets/part3/ai-lead-intake-dashboard.png` — существует в репозитории LD LATTE.

**CI:** последний запуск `CI` на текущем коммите `main` завершён успешно;
CodeQL также зелёный. Проверено через GitHub Actions 28 июля 2026 года.

---

## 2. Bitrix24 Communication Summary Agent

**Репозиторий:** [github.com/iurii-izman/bitrix24-communication-summary-agent](https://github.com/iurii-izman/bitrix24-communication-summary-agent)
**Коммитов:** 6. Последний: 2026-07-14.

| Утверждение в part3.md | Подтверждение | Статус |
|---|---|---|
| Обрабатывает звонки, письма, чаты, заметки → CRM-действия | README: «processing calls, emails, chats, and manager notes into structured CRM actions» | ✅ Подтверждено |
| Структура ответа: резюме, договорённости, риски, next steps, задачи, черновик | README перечисляет все перечисленные поля | ✅ Подтверждено |
| Спорные случаи — в очередь сотрудника | README: «review routing and operator override path», «review queue» | ✅ Подтверждено |
| Human-in-the-loop | README: «human-in-the-loop workflow», `ALLOW_BITRIX_WRITE=false` по умолчанию | ✅ Подтверждено |
| Проверка на тестовом портале Bitrix24 | README: «real Bitrix24 test-portal workflow», задачи и комментарии подтверждены | ✅ Подтверждено |
| Стек: Python 3.12, FastAPI, Pydantic, SQLAlchemy, SQLite | Подтверждено `pyproject.toml` и структурой директорий | ✅ Подтверждено |
| Публичный релиз v0.1.0 | Релиз существует, создан 2026-07-07, содержит release notes | ✅ Подтверждено |
| Docker Compose | `docker-compose.yml` и `Dockerfile` присутствуют | ✅ Подтверждено |
| GitHub Actions | `.github/workflows/` содержит CI | ✅ Подтверждено |
| Самостоятельная разработка | 6 коммитов, схема авторства аналогична проекту 1 | ✅ Подтверждено |

**Скриншот:** `docs/assets/part3/communication-summary-dashboard.png` — существует.

**CI:** последний запуск `ci` на текущем коммите `main` завершён успешно.
Проверено через GitHub Actions 28 июля 2026 года.

**Замечание:** 6 коммитов — заметно меньше, чем в других проектах. Это не противоречит заявленному (рабочий MVP, не production), но интервьюер может спросить о глубине проработки. Рекомендуется подчеркнуть, что проект целенаправленно компактный — один pipeline, один сценарий.

---

## 3. Replyline

**Репозиторий:** [github.com/iurii-izman/replyline](https://github.com/iurii-izman/replyline)
**Коммитов:** 435. Последний: 2026-07-28.

| Утверждение в part3.md | Подтверждение | Статус |
|---|---|---|
| Windows-приложение, hotkey → захват аудио → STT → LLM → карточка ответа | README: «Hotkey-gated capture (Ctrl+Alt+Space)», «capture -> stt -> llm -> card» | ✅ Подтверждено |
| Короткая карточка: gist / say_now / next_move | README: «gist / say_now / next_move» из `CardSchemaV3` | ✅ Подтверждено |
| Tauri 2, Rust, WASAPI loopback, SolidJS, TypeScript | `package.json`: Tauri, SolidJS; `src-tauri/`: Rust, WASAPI | ✅ Подтверждено |
| Deepgram STT, OpenAI-compatible LLM | README: «Deepgram STT + OpenAI-compatible LLM route» | ✅ Подтверждено |
| Windows Credential Manager | README: «API keys in Windows Credential Manager» | ✅ Подтверждено |
| Без фоновой записи, без истории расшифровок | README: «RAM-only transcripts», «no background recording» | ✅ Подтверждено |
| 454 автоматизированных теста (265 Rust + 189 TS) | README: «454 automated tests (265 Rust + 189 TS)» | ✅ Подтверждено |
| Публичная продуктовая страница | [iurii-izman.github.io/replyline/](https://iurii-izman.github.io/replyline/) — открывается | ✅ Подтверждено |
| Beta-релизы | `v0.2.0-beta.3` существует, создан 2026-06-17 | ✅ Подтверждено |
| Самостоятельная разработка | 435 коммитов, схема авторства аналогична проектам 1 и 2 | ✅ Подтверждено |

**Скриншот:** `docs/assets/part3/replyline-answer-card.png` — существует.

**CI:** основной CI и CodeQL на текущем коммите `606a936` завершены успешно
после исправления ожидания жизненного цикла hotkey в credential-free
Playwright-сценариях. В `docs/part3.md` оставлена устойчивая
[ссылка на вкладку Actions](https://github.com/iurii-izman/replyline/actions),
а не на отдельный run.

---

## Сводная матрица

| Проект | Всего утверждений | Подтверждено | Неточно | Замечание |
|---|---:|---:|---|---|
| AI Lead Intake | 9 | 9 | 0 | CI и CodeQL на текущем `main` подтверждены |
| Communication Summary | 10 | 10 | 0 | CI на текущем `main` подтверждён |
| Replyline | 10 | 10 | 0 | CI и CodeQL на текущем `main` подтверждены |

---

## Рекомендации по part3.md

Документ **точен и не требует исправлений по существу**. Единственная
minor-рекомендация уже применена:

| Строка | Текущий текст | Рекомендация | Причина |
|---|---|---|---|
| 67 | Ссылка на конкретный CI run | Заменено на `[CI](https://github.com/iurii-izman/replyline/actions)` | Ссылка на вкладку Actions надёжнее |

Остальной текст корректен. Все утверждения подтверждаются содержимым репозиториев.

---

## Оценка сильных сторон (не упомянутых в part3.md)

Вот что можно было бы добавить, но текущий объём part3.md уже достаточен для тестового задания:

1. **AI Lead Intake:** state machine с идемпотентностью, retry semantics, rate limiting — это сильнее, чем просто «pipeline».
2. **Communication Summary:** скрипты batch-валидации и cleanup для безопасного тестирования на живом портале — редкая дисциплина.
3. **Replyline:** release freeze guard, corrupt-file quarantine, 40 typed IPC-команд — инженерная зрелость выше среднего.

---

## Вопросы, которые интервьюер может задать

### По всем проектам

1. **«Почему в коммитах фигурирует VideoTranscriber Bot? Как распределялась работа между вами и AI?»**
   *Тезис:* Бот — это coding-агент внутри Zed-редактора. Я формулировал задачу, архитектуру и критерии приёмки; агент генерировал код; я проверял результат, запускал тесты и коммитил. Продуктовые решения и интеграционные границы всегда оставались на моей стороне.

2. **«Какой проект вы считаете самым сильным и почему?»**
   *Тезис:* Replyline — по глубине инженерной проработки (454 теста, 435 коммитов, release pipeline). AI Lead Intake — по релевантности вакансии (AI + CRM + бизнес-процесс).

### AI Lead Intake

3. **«Что произойдёт, если Bitrix24 API недоступен во время обработки лида?»**
   *Тезис:* Worker реализует retry semantics. Запрос остаётся в очереди с понятным статусом. Администратор видит stalled-записи в admin UI и может вручную retry или drop.

4. **«Почему SQLite, а не PostgreSQL?»**
   *Тезис:* Для demo/MVP SQLite достаточно и устраняет зависимость от внешней БД. В README описан production upgrade path: PostgreSQL, миграции, внешняя очередь.

### Communication Summary

5. **«Как вы проверяли, что агент не испортит данные в реальном Bitrix24?»**
   *Тезис:* Dry-run по умолчанию (`ALLOW_BITRIX_WRITE=false`). Скрипт `cleanup_live_artifacts.py` удаляет тестовые артефакты после валидации. Запись включается только явным флагом `--enable-write`.

6. **«Почему всего 6 коммитов? Это выглядит как одноразовый прототип.»**
   *Тезис:* Проект целенаправленно компактный — один pipeline, один сценарий. Основная инженерная работа была в проектировании контракта AI-ответа, human-in-the-loop сценария и безопасной интеграции с Bitrix24. Глубина — в продуманности границ, а не в количестве кода.

### Replyline

7. **«454 теста — это unit или integration? Как они распределены?»**
   *Тезис:* 265 Rust (unit + integration) и 189 TypeScript (unit + component + e2e Playwright). Mock platform для UI-тестов. `pnpm verify` — blocking CI, `pnpm verify:full` — release gate.

8. **«Почему Windows-only? Планируется ли macOS/Linux?»**
   *Тезис:* WASAPI loopback capture жёстко привязан к Windows. Кроссплатформенный захват аудио — отдельная инженерная задача. В roadmap есть исследования, но текущий фокус — стабильность на одной платформе.

9. **«Как вы тестировали loopback-захват без реального аудио?»**
   *Тезис:* Rust-тесты используют mock audio pipeline. Playwright e2e проверяет UI на синтетических сценариях. Реальный аудиозахват проверялся вручную на Windows 10/11.

10. **«Это open-source или вы планируете коммерциализацию?»**
    *Тезис:* Сейчас — public source beta под MIT. Фокус на качестве и доверии, а не на монетизации. Коммерческие сценарии не исключены в будущем, но требуют отдельного продукта.
