# Backlog развития LD LATTE Influencer Scout

Актуальность: 27 июля 2026 года.

Размер задачи:

- `S` — локальное изменение;
- `M` — несколько модулей/контрактов;
- `L` — новый контур или интеграция;
- `XL` — отдельный этап продукта.

Размер — относительный, не обещание срока.

## Рекомендуемый порядок

1. Сначала доказуемость и безопасность.
2. Затем автоматическое evidence enrichment.
3. Потом новые платформы и мультимодальность.
4. Только после этого CRM, отправка и learning loop.

Добавлять автосообщения до P0-готовности не следует.

## P0 — до следующего серьёзного live-пилота

| ID | Задача | Размер | Зачем | Критерий приёмки |
|---|---|---:|---|---|
| P0-01 | Строгие схемы LLM-ответов | M | Сейчас есть только `json.loads` и ручные проверки отдельных полей | Portrait, discovery и offer валидируются; unknown fields/типы обрабатываются предсказуемо; есть invalid fixtures |
| P0-02 | Защита от prompt injection | M | Title/snippet — недоверенные строки | Prompt явно помечает данные; найденные инструкции не исполняются; adversarial eval проходит |
| P0-03 | Freshness и profile-health gate | M | Cached sources быстро устаревают | У каждого evidence есть дата; stale-кандидат не допускается к контакту без refresh |
| P0-04 | Исправить data-quality counters | S | `duplicate_handles` всегда 0 | Реальный дубль увеличивает счётчик; тест покрывает |
| P0-05 | Ужесточить `profile_type` | S | Сейчас `None` может пройти | Только явный `personal_creator` проходит live discovery |
| P0-06 | ISO timestamp для live evidence | S | `"live"` нельзя использовать для аудита | `observed_at` — UTC ISO-8601; тест формата |
| P0-07 | Run manifest | M | Нельзя точно воспроизвести LLM-run | Сохраняются run ID, input hash, git SHA, model, prompt hash, timings, fallbacks |
| P0-08 | Failure-path tests | M | Нет покрытия timeout/invalid JSON/search failure | Все ошибки дают понятный status; demo остаётся доступен |
| P0-09 | Юридический channel gate | M | Research score не определяет допустимость рекламы | Поля `research_allowed`, `activation_status`, `legal_owner`; blocked нельзя approve |
| P0-10 | Evidence coverage report | S | 62% легко потерять за красивым portrait | UI показывает annotated/unknown/conflicts и список профилей для доработки |
| P0-11 | Финальная воспроизводимость тестового | S | Нужна одна ссылка и простой запуск | Чистая машина запускает demo по README; 9+ тестов зелёные; screenshot/JSON доступны |
| P0-12 | Указать фактическое время части 1 | S | Прямое условие задания | Пользователь подтверждает время; значение внесено без оценки AI |

## P1 — качество данных и рабочий процесс

| ID | Задача | Размер | Зачем | Критерий приёмки |
|---|---|---:|---|---|
| P1-01 | Автоматическое seed enrichment | L | 13 из 34 профилей unknown | Coverage ≥90% либо documented unavailable; каждый факт имеет source/date/confidence |
| P1-02 | Manual evidence review UI | M | Автоматические факты нужно подтверждать | Менеджер approve/edit/reject факт; история сохраняется |
| P1-03 | YouTube Shorts adapter | L | Заявлен заданием и prompt, но отсутствует в коде | Канонический channel/short URL, Data API evidence, tests, rate limits |
| P1-04 | Telegram adapter | L | Общий web search недостаточно устойчив | Платформенный evidence contract, freshness и creator/aggregator checks |
| P1-05 | Разрешённый Instagram adapter | L | Индексируемые сниппеты ограничены | Business/creator integration там, где доступно и допустимо; legal gate обязателен |
| P1-06 | Direct URL validation | M | Search presence не гарантирует живой профиль | Health status, redirects, canonical URL, last checked |
| P1-07 | Расширить metric parser | S | Текущие regex понимают не все локали | RU/EN форматы K/К/M/М, пробелы, commas; table-driven tests |
| P1-08 | Улучшить aggregator classifier | M | Два regex дают false negatives | Golden set личных/агрегаторских каналов; precision/recall threshold |
| P1-09 | Candidate identity graph | L | Один автор может быть на нескольких платформах | Person ID, linked accounts, merge/split review, no double outreach |
| P1-10 | PostgreSQL persistence | L | JSON не подходит для команды | Seeds, evidence, candidates, scores, offers, decisions и runs хранятся версионно |
| P1-11 | Outreach state machine | M | Статусы пока только в документации | Допустимые переходы enforced; timestamps/owner/reason |
| P1-12 | Suppression list | M | Нельзя писать повторно после отказа/жалобы | Block list работает между runs и платформами |
| P1-13 | Auth/RBAC | L | Публичный Streamlit может раскрыть данные и расходы | Роли viewer/manager/admin; audit login/actions |
| P1-14 | Queue, retry, cache | L | Live pipeline хрупкий и последовательный | Идемпотентные jobs, bounded retry, backoff, cache TTL |
| P1-15 | Provider-neutral LLM gateway | M | Сейчас реализован только DeepSeek | DeepSeek/OpenAI-compatible adapters, единый contract, per-provider eval |
| P1-16 | Token/cost controls | M | Live run может неконтролируемо расходовать бюджет | Per-run budget, cache, usage log, stop/fallback |
| P1-17 | Dependency lock и CI | M | Диапазоны версий могут дрейфовать | Lock-file, lint/type/tests/security workflow |
| P1-18 | Observability dashboard | M | Нельзя видеть drift и failures | Success rate, latency, cost, missingness, fallback, rejection reasons |

## P1 — мультимодальность и ranking

| ID | Задача | Размер | Зачем | Критерий приёмки |
|---|---|---:|---|---|
| P1-19 | Golden set эстетики | M | Нет эталона для visual model | Бренд-команда размечает пары/рубрику, inter-rater agreement измерен |
| P1-20 | Vision evidence schema | M | Нельзя смешивать embedding и факт | Признак привязан к media/source/date/model/confidence |
| P1-21 | Multimodal aesthetic prototype | L | Текущий aesthetic fit не смотрит ленту автоматически | На holdout превосходит текстовый baseline и не ухудшает factuality |
| P1-22 | Scoring sensitivity report | M | Веса пока бизнес-гипотеза | Изменение каждого feature показывает влияние на top-5 |
| P1-23 | Confidence calibration | L | Confidence сейчас задаётся вручную/LLM | Score bands соответствуют фактической доле ручных подтверждений |
| P1-24 | Offline ranking eval | M | Нет Precision@5/NDCG | Golden candidate set, baseline, versioned report |

## P2 — после появления реальной воронки

| ID | Задача | Размер | Зачем | Критерий приёмки |
|---|---|---:|---|---|
| P2-01 | CRM/Telegram approval integration | L | Замкнуть workflow | Сообщение отправляется только после owner + approval + legal status |
| P2-02 | Offer versioning/edit distance | M | Понять полезность генерации | Хранятся draft/final; считается объём ручных правок |
| P2-03 | Product-to-creator matching | L | Оффер должен предлагать релевантные вещи | 3–4 SKU объяснимо связаны со стилем, остатками и размерами |
| P2-04 | Contracts/rights fields | M | Права нельзя хранить в свободном тексте | Территория, срок, каналы, paid usage, карточки товара, статус документа |
| P2-05 | Publication evidence | M | Нужен факт исполнения | URL, дата, screenshot, маркировка, ERID, срок хранения |
| P2-06 | Marketplace attribution | XL | Нужна экономика | Promo/UTM/period uplift, returns, margin и ограничения causal inference |
| P2-07 | Monthly calibration | L | Веса должны обновляться по исходам | Изменение проходит offline eval и approval |
| P2-08 | Learning-to-rank | XL | Возможен только при достаточных данных | Есть sample-size threshold, holdout, fairness и rollback |
| P2-09 | Re-engagement recommendations | M | Полезны повторные сильные авторы | Решение основано на прошлом outcome, не только на profile score |
| P2-10 | Portfolio optimization | XL | Ограниченный бюджет нужно распределять | Оптимизация учитывает cost, reach, fit, stock и uncertainty |

## Набор обязательных acceptance tests

### Ingestion

- hidden hyperlink выигрывает у display;
- tracking удаляется;
- post/reel URL не становится seed;
- duplicate считается;
- огромный/повреждённый файл отклоняется безопасно;
- неизвестный лист даёт понятную ошибку.

### Evidence

- каждый факт имеет source и время;
- stale evidence помечается;
- конфликт источников не склеивается;
- unavailable не становится негативным фактом;
- raw evidence неизменяем, interpretation версионируется.

### Discovery

- URL вне allow-list отклоняется;
- seed duplicate отклоняется;
- aggregator отклоняется;
- YouTube/Telegram/Instagram identity канонизируется;
- prompt injection не меняет contract;
- несуществующий профиль не доходит до approval.

### Scoring

- feature ограничен 0..1;
- missing не равен 0;
- рост positive feature не снижает score при прочих равных;
- рост risk не повышает score;
- рост confidence не снижает score при положительном raw;
- порядок воспроизводим;
- score reason соответствует формуле.

### Offer

- anchor подтверждён source;
- нет выдуманного имени;
- нет требования положительного отзыва;
- нет обещания оплаты;
- бартер не считается согласованным;
- права обсуждаются отдельно;
- legal block запрещает отправку;
- manual approval обязателен.

## Milestone 1: «Честный и проверяемый MVP»

Включает P0-01…P0-12.

Готово, когда:

- demo воспроизводим;
- live failure безопасно откатывается;
- LLM-output валиден;
- freshness видна;
- channel policy отделена;
- все факты трассируются;
- тестовое можно открыть по одной ссылке.

## Milestone 2: «Evidence automation»

Включает P1-01…P1-09 и P1-19…P1-24.

Готово, когда:

- seed coverage выше 90%;
- три платформы имеют адаптеры;
- visual score проверен на golden set;
- top-5 измеряется через Precision@5;
- person deduplication работает.

## Milestone 3: «Командный workflow»

Включает P1-10…P1-18 и P2-01…P2-05.

Готово, когда:

- есть роли, БД, очередь и аудит;
- менеджер ведёт кандидата до публикации;
- комплаенс — hard gate;
- ни одно сообщение не теряется и не отправляется дважды.

## Milestone 4: «Оптимизация по бизнес-результату»

Включает P2-06…P2-10.

Готово, когда:

- есть достаточно фактических исходов;
- атрибуция описывает ограничения;
- ranking изменяется только через eval;
- основной результат — contribution margin, а не число найденных блогеров.

## Что дать другой модели первым

### Если нужна быстрая польза

Задачи P0-04, P0-05, P0-06 и P0-08.

### Если нужна самая важная продуктовая итерация

P1-01: automatic seed enrichment.

### Если нужно доказать «AI-часть»

P1-19…P1-24: golden set, multimodal evidence и ranking eval.

### Если нужна production-готовность

P0 целиком, затем P1-10…P1-18.

### Что пока не давать в реализацию

- автоматическую отправку;
- learning-to-rank;
- portfolio optimizer;
- массовый scraper;
- полный rewrite стека.

Для этих задач пока недостаточно данных или защитных контуров.
