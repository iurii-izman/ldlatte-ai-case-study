# Готовые промпты для глубокой проработки Influencer Scout

Перед каждым запросом приложить `docs/part1-model-context.md`. Для технической
задачи также приложить релевантные исходники. Не передавать `.env` и секреты.

## 1. Независимый аудит архитектуры

```text
Проведи независимый архитектурный аудит LD LATTE Influencer Scout.

Цель: определить, какие решения MVP стоит сохранить, а какие помешают перейти к
production. Не предлагай переписывание ради нового стека.

Разбери:
- границы deterministic/LLM;
- связность модулей;
- контракты данных;
- внешние зависимости;
- failure modes;
- идемпотентность;
- воспроизводимость;
- auditability;
- стоимость эксплуатации;
- путь миграции от Streamlit/JSON к сервису с очередью и БД.

Для каждой проблемы укажи:
1) evidence в файле/функции;
2) severity и вероятность;
3) минимальное исправление;
4) production-вариант;
5) критерий приёмки;
6) тест;
7) риск миграции.

В конце дай целевую C4-подобную схему и roadmap на 3 этапа.
```

Приложить:

- `ldlatte_agent/pipeline.py`;
- `ldlatte_agent/models.py`;
- остальные модули;
- `docs/part1-system-dossier.md`.

## 2. Продуктовый аудит глазами руководителя influencer marketing

```text
Представь, что ты руководитель influencer marketing fashion-бренда с продажами
на WB/Ozon. Оцени LD LATTE Influencer Scout не по красоте технологии, а по тому,
помогает ли он принимать решения.

Ответь:
- какие решения менеджер сможет принимать быстрее;
- каких данных не хватает;
- где score вводит в заблуждение;
- какие поля нужны до первого контакта;
- какие поля нужны после контакта;
- какой workflow должен быть у команды;
- какие действия запрещено автоматизировать;
- что должно быть видно на одном экране;
- какую метрику выбрать для месячного пилота.

Предложи:
1) идеальный candidate card;
2) state machine;
3) SLA;
4) причины reject;
5) monthly report;
6) эксперимент baseline vs tool.

Отделяй «обязательно для пилота» от «приятно иметь».
```

## 3. Автоматическое enrichment исходных 34 профилей

```text
Спроектируй evidence-first enrichment pipeline для 34 seed-профилей.

Ограничения:
- никаких неразрешённых логинов и обхода защит;
- отсутствие данных остаётся unknown;
- любой факт имеет source_url, observed_at и confidence;
- visual_reference не влияет на коммерческие метрики;
- система должна поддержать Telegram, YouTube и разрешённые Instagram paths;
- raw evidence хранится отдельно от интерпретации.

Нужно выдать:
1) source adapters и что каждый законно/технически может дать;
2) единый evidence schema;
3) deduplication;
4) freshness policy;
5) conflict resolution;
6) retry/rate-limit;
7) очередь;
8) ручной review UI;
9) тестовые fixtures;
10) критерий coverage >90%.

Предложи fallback, если профиль недоступен или не индексируется.
```

## 4. Мультимодальный анализ эстетики

```text
Спроектируй мультимодальный модуль aesthetic fit для женской одежды LD LATTE.

Не используй абстрактное «отправим картинки в vision model». Опиши:
- какие изображения/thumbnail можно использовать;
- как получить их разрешённым способом;
- как отделить визуал автора от репостов/рекламы;
- какие признаки нужны бренду;
- как сделать human-labelled golden set;
- embeddings vs VLM rubric;
- aggregation по постам;
- uncertainty;
- drift;
- bias;
- стоимость;
- eval.

Предложи schema результата, например:
visual_palette, styling_femininity, wearability, composition_cleanliness,
video_tryon_presence, product_detail_quality, creator_identity_consistency,
evidence, confidence.

Score не должен становиться полностью модельным. Покажи, как встроить модуль в
существующую формулу и как откатить его при низкой уверенности.
```

## 5. Platform discovery: Telegram, YouTube Shorts, Instagram

```text
Спроектируй три независимых discovery adapter для Telegram, YouTube Shorts и
разрешённых Instagram business/creator источников.

Для каждого:
- официальный/разрешённый источник;
- поисковая стратегия;
- canonical identity;
- доступные метрики;
- ограничения;
- rate limits;
- freshness;
- признаки личного автора;
- защита от агрегаторов;
- direct URL validation;
- тестовый sandbox/fixture;
- legal activation gate.

Создай общий Adapter protocol и unified CandidateEvidence schema. Не смешивай
research eligibility с разрешением разместить рекламу.

Отдельно опиши, как добавить YouTube в текущий `_candidate_handle`, потому что
сейчас prompt допускает YouTube, а код нет.
```

## 6. Пересмотр формулы скоринга

```text
Выступи как ML/ranking специалист. Проведи аудит текущего score:

raw = weighted average по observed features
confidence_factor = 0.85 + 0.15 * confidence
risk_penalty = 0.15 * risk
score = 100 * clamp(raw * confidence_factor - risk_penalty)

Веса:
content 20%, aesthetic 20%, marketplace 15%, engagement 15%, audience 10%,
activity 10%, barter 10%.

Проверь:
- корректность missing-data подхода;
- двойной учёт связанных признаков;
- calibration confidence;
- влияние risk;
- sensitivity;
- score bands;
- небольшую выборку;
- gaming;
- platform bias;
- large vs micro creators.

Предложи baseline v2, который остаётся объяснимым. Не предлагай learning-to-rank
до накопления достаточных исходов.

Нужны:
1) формула;
2) rationale;
3) тестовые примеры;
4) property-based invariants;
5) offline eval;
6) критерий перехода к обучаемой модели.
```

Приложить `ldlatte_agent/scoring.py` и `data/candidates.json`.

## 7. Evals для трёх LLM-задач

```text
Создай полноценную eval-стратегию для:
1) seed portrait;
2) candidate extraction;
3) offer generation.

Учитывай, что текущие ответы JSON, а URL нельзя придумывать.

Для каждого eval опиши:
- golden fixtures;
- deterministic checks;
- model-graded checks;
- hallucination tests;
- prompt injection tests;
- missing-data tests;
- conflicting-source tests;
- Russian language quality;
- cost/latency;
- pass threshold;
- regression policy.

Для оффера обязательно проверять:
- нет выдуманного отправителя;
- нет неподтверждённого факта;
- нет требования положительного отзыва;
- нет обещания оплаты;
- права на контент не присваиваются автоматически;
- есть конкретный anchor и CTA.

Верни структуру каталогов, fixtures и псевдокод runner.
```

## 8. Prompt-injection и security review

```text
Проведи threat model текущего Influencer Scout.

Недоверенные данные:
- XLSX;
- Google Sheets;
- search title/snippet;
- profile bio;
- LLM output;
- uploaded file.

Активы:
- API-ключи;
- кандидатская база;
- контакты;
- брендовая репутация;
- рекламный бюджет;
- права на контент.

Атакующие:
- владелец найденной страницы;
- злоумышленник в search index;
- пользователь публичного Streamlit;
- компрометированная dependency;
- ошибочная LLM.

Найди attack paths, включая:
- prompt injection;
- data poisoning;
- cost exhaustion;
- SSRF;
- malicious XLSX/ZIP bomb;
- XSS/markdown links;
- secret leakage;
- spam;
- approval bypass.

Для каждого: severity, current mitigation, residual risk, минимальный fix,
production control, test. Заверши security acceptance checklist.
```

## 9. Юридический и операционный workflow

```text
Выступи как специалист по рекламному комплаенсу, но явно отмечай, что ответ не
заменяет юридическую консультацию.

На основе актуальных норм РФ спроектируй decision tree для influencer
collaboration:
- research площадки;
- допустимость activation;
- реклама или органический редакционный контент;
- бартер/оплата/гибрид;
- договор;
- маркировка и ERID;
- отчётность;
- права на контент;
- удаление/срок размещения;
- налоги;
- персональные данные;
- хранение доказательств.

Отдельно разбери риск Instagram после 01.09.2025 и не делай вывод только по
названию площадки без первичного источника.

Результат:
1) policy fields в Candidate;
2) hard-block statuses;
3) роли и ответственность;
4) документы;
5) audit log;
6) вопросы юристу LD LATTE.
```

## 10. UX для influencer-менеджера

```text
Перепроектируй Streamlit MVP в рабочее место influencer-менеджера.

Сценарий:
1) импорт seed;
2) data-quality review;
3) portrait approval;
4) candidate inbox;
5) evidence inspection;
6) reject/approve;
7) offer edit;
8) legal check;
9) contact;
10) negotiation;
11) publication;
12) measurement.

Нужно:
- information architecture;
- candidate card;
- bulk actions;
- filters;
- empty/error/loading states;
- audit history;
- accessibility;
- permissions;
- notification policy;
- desktop/mobile priorities.

Для каждого экрана укажи решение пользователя, обязательные поля и способы
предотвратить ошибку. Не превращай UI в дашборд vanity metrics.
```

## 11. Эксперимент и бизнес-экономика

```text
Спроектируй месячный пилот Influencer Scout.

Нужно доказать не только экономию времени, но и качество сотрудничеств.

Опиши:
- baseline;
- unit of randomization;
- control/treatment;
- sample constraints;
- funnel events;
- full cost of barter;
- attribution window;
- promo/UTM limitations на WB/Ozon;
- leading metrics;
- main metric;
- guardrails;
- minimum detectable effect;
- правила остановки;
- отчёт через месяц.

Предложи формулу contribution margin интеграции и способ работать, если прямой
атрибуции заказов недостаточно. Не обещай causal lift без подходящего дизайна.
```

## 12. Код-ревью и план тестов

```text
Проведи построчное код-ревью приложенных модулей Influencer Scout.

Ищи:
- функциональные ошибки;
- несоответствие документации коду;
- silent failure;
- неправильную обработку missing;
- слабую валидацию;
- ошибки URL normalization;
- concurrency;
- timeout/retry;
- сериализацию;
- безопасность;
- тестируемость.

Особенно проверь известные подозрения:
- duplicate_handles всегда 0;
- profile_type=None проходит;
- observed_at="live";
- YouTube отсутствует;
- LLM JSON проверяется только json.loads;
- search result может содержать prompt injection.

Для каждой находки:
severity, file/function, сценарий воспроизведения, минимальный patch, тест.
Не изменяй код, пока не выдашь canonical список и приоритет.
```

## 13. Сравнение моделей и провайдеров

```text
Создай provider-neutral benchmark для DeepSeek, OpenAI, Claude, Gemini и
локальной модели применительно к Influencer Scout.

Три задачи:
- portrait JSON;
- candidate extraction из allow-list;
- offer JSON.

Оцени:
- schema adherence;
- hallucination rate;
- factuality;
- Russian copy quality;
- prompt injection resistance;
- latency;
- cost;
- rate limits;
- data handling;
- operational complexity.

Не выбирай победителя по общему впечатлению. Предложи eval dataset, scoring
rubric, число повторов и decision matrix. Укажи, где достаточно дешёвой модели,
а где нужна более сильная.
```

## 14. Deep research конкурентов и готовых инструментов

```text
Проведи актуальное исследование решений для influencer discovery/outreach,
которые могут заменить или дополнить собственную разработку.

Категории:
- российские influencer platforms;
- Telegram analytics;
- YouTube discovery;
- social listening;
- CRM/outreach;
- creator payments/contracts;
- ad labeling/ORD;
- UGC rights management.

Для каждого решения:
- подтверждённая функция;
- API/export;
- покрытие РФ/WB/Ozon;
- цена;
- ограничения;
- legal/data risk;
- build vs buy.

Используй первичные источники и указывай дату проверки. Заверши вариантом
гибридной архитектуры: что купить, что оставить своим.
```

## 15. Красная команда против качества результата

```text
Попытайся заставить систему выбрать плохого кандидата.

Сгенерируй adversarial fixtures:
- крупный бренд вместо автора;
- агрегатор с красивым snippet;
- купленные подписчики;
- один вирусный пост;
- устаревший профиль;
- противоречивые каталоги;
- fashion как вторичная тема;
- fake barter claim;
- prompt injection в bio;
- тот же человек под другим handle;
- seed duplicate с другим URL;
- запрещённая для activation площадка.

Для каждого покажи:
1) почему текущая система может ошибиться;
2) ожидаемый безопасный результат;
3) hard filter или feature;
4) тест;
5) лог для расследования.
```
