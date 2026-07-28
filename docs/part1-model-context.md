# Контекст-пакет для работы над Influencer Scout в другой AI-модели

Этот файл можно передать Claude, ChatGPT, Gemini, DeepSeek или локальной модели
вместе с репозиторием. Он специально отделяет проверенные факты от планов, чтобы
модель не приписывала MVP несуществующие возможности.

## 1. Роль системы

Название: `LD LATTE Influencer Scout`.

Цель: помочь бренду женской одежды LD LATTE находить блогеров для бартерных или
гибридных интеграций на основе уже одобренной seed-базы.

Бренд:

- женская одежда;
- полный цикл от эскиза до готового товара;
- продажи на Wildberries и Ozon;
- команда 60+ человек;
- ожидается практичная AI-автоматизация, а не только prompts.

## 2. Исходное требование

Инструмент должен:

1. подключиться к таблице;
2. проанализировать профили;
3. построить портрет идеального блогера;
4. найти 3–5 новых реальных профилей;
5. объяснить соответствие;
6. написать персональное предложение о сотрудничестве;
7. иметь инструкцию, промпты и схему автоматизации.

Нужен MVP, а не готовая production-система.

## 3. Проверенные факты о текущем состоянии

Дата snapshot: 28 июля 2026 года.

- Реальный входной файл: `docs/Блогеры.xlsx`.
- В книге 2 листа.
- `Исходник`: диапазон `A1:B74`.
- `Новые блоггеры`: диапазон `A1:D4`.
- Загрузчик находит 34 уникальных seed-профиля.
- В 6 ячейках hyperlink target отличается от отображаемого текста.
- Размечено evidence по 21 seed.
- 13 seed имеют роль `unknown`.
- Evidence coverage: 0,62.
- Три контрольных full-live run: 24–33 из 34 seed с public-index evidence,
  46–73 источника, coverage 0,71–0,97; пропуски остались unknown.
- Распределение: 8 core, 2 visual references, 6 secondary, 5 outliers,
  13 unknown.
- В cached snapshot 5 новых кандидатов.
- Demo-run возвращает score: 87,3; 87,2; 85,3; 79,9; 72,0.
- Suite содержит 52 теста: локально 51 проходит и один live-тест пропущен; в
  публичном CI без приватной таблицы проходят 50 и пропущены два.
- Есть Streamlit UI, CLI и JSON export.
- Автоматической отправки сообщений нет.

## 4. Реализованный pipeline

```text
XLSX / upload / public Google Sheets
→ hyperlink extraction
→ Instagram URL normalization
→ saved annotations or dated public-index seed evidence
→ rule-based or DeepSeek portrait
→ cached candidates or DDGS live discovery
→ exact-URL allow-list
→ filters
→ deterministic score
→ deterministic or DeepSeek offer
→ Streamlit / CLI JSON
→ manual approval
```

### Режимы

1. `Демо`: без сети и токенов.
2. `Live: DeepSeek`: LLM portrait + LLM offers, cached candidates.
3. `Live: поиск + DeepSeek`: automatic seed evidence + web discovery + LLM
   portrait/offers.

## 5. Архитектурные границы

### Обычный код отвечает за

- разбор Excel;
- нормализацию;
- точную URL allow-list;
- seed deduplication;
- feature clipping;
- scoring;
- risk/confidence;
- safe fallback оффера;
- сериализацию.

### LLM отвечает за

- интерпретацию evidence в портрете;
- выбор/классификацию только URL из search results;
- извлечение признаков;
- персональный текст.

### Человек отвечает за

- фактическую проверку профиля;
- актуальность метрик;
- условия;
- юридическую допустимость площадки;
- одобрение текста;
- отправку.

## 6. Scoring

Веса:

```json
{
  "content_fit": 0.20,
  "aesthetic_fit": 0.20,
  "marketplace_fit": 0.15,
  "engagement_quality": 0.15,
  "audience_fit": 0.10,
  "activity": 0.10,
  "barter_likelihood": 0.10
}
```

Формула:

```text
raw = Σ(xᵢ × wᵢ) / Σ(wᵢ) только по наблюдаемым признакам
confidence_factor = 0.85 + 0.15 × confidence
risk_penalty = 0.15 × risk
score = 100 × clamp(raw × confidence_factor − risk_penalty, 0, 1)
```

Missing не равен нулю. Неопределённость отражается через confidence.

## 7. Основные контракты

### Seed

```json
{
  "excel_row": 0,
  "number": null,
  "display": "",
  "source_url": "",
  "handle": "",
  "normalized_url": ""
}
```

### Candidate

```json
{
  "handle": "",
  "platform": "",
  "url": "",
  "title": "",
  "followers": null,
  "avg_views": null,
  "engagement_rate": null,
  "facts": [],
  "sources": [],
  "features": {},
  "confidence": 0.0,
  "risk": 0.0,
  "cooperation_status": "требуется уточнить",
  "contact": "",
  "offer_anchor": "",
  "score": null,
  "reason": "",
  "offer": ""
}
```

### Evidence target

```json
{
  "profile_url": "",
  "observed_at": "ISO-8601",
  "source_url": "",
  "fact": "",
  "confidence": 0.0
}
```

## 8. Критические правила продукта

Модель не должна предлагать отменить эти правила без явного анализа риска:

1. Не усреднять всю seed-базу.
2. Бренд/visual reference не определяет бартерные метрики.
3. Missing не считать нулём.
4. Не придумывать URL.
5. Не придумывать публикации, аудиторию, город или метрики.
6. Не считать тематику доказательством согласия на бартер.
7. Не требовать положительный отзыв.
8. Не обещать оплату без согласования.
9. Не выдумывать имя отправителя.
10. Права на контент обсуждать отдельно.
11. Не отправлять сообщение автоматически.
12. Research status площадки не равен legal activation status.

## 9. Что пока не реализовано

- production-grade seed enrichment через разрешённые platform sources;
- vision-анализ ленты;
- YouTube adapter;
- закрытая Google Sheets через service account;
- Instagram Graph API adapter;
- строгая JSON Schema валидация LLM;
- prompt-injection defense;
- direct profile health check;
- persistent database;
- CRM/outreach;
- auth/RBAC;
- queue/retry/cache;
- legal policy engine;
- learning loop;
- бизнес-атрибуция.

Не описывать эти возможности как готовые.

## 10. Известные проблемы

- Public-index seed enrichment зависит от поисковой выдачи и не гарантирует
  evidence для каждого профиля.
- Search queries не включают YouTube.
- Followers parser понимает ограниченное число форматов.
- Aggregator heuristic покрывает лишь несколько шаблонов.
- Search snippet может содержать prompt injection.
- Нет retry/backoff.
- Нет prompt hashes, token usage и cost в run metadata.
- Requirements без lock-файла.
- Публичный deployment потребует auth и cost limits.

## 11. Юридическая граница

Не давать окончательных юридических выводов.

Для РФ закон № 72-ФЗ от 07.04.2025 требует отдельной проверки допустимости
рекламной публикации на ограниченных/запрещённых ресурсах. Instagram-профиль
можно исследовать как источник, но нельзя автоматически превращать это в
рекомендацию размещения.

Для любой площадки нужно определить:

- является ли публикация рекламой;
- нужна ли маркировка/ERID и отчётность;
- кто ответственен;
- права на контент;
- договор/акт;
- налоги и стоимость бартера.

## 12. Что считать хорошим предложением модели

Хорошее предложение:

- ссылается на конкретный файл, функцию или контракт;
- отделяет исправление бага от новой функции;
- называет приоритет и риск;
- сохраняет deterministic guardrails;
- содержит критерии приёмки;
- предлагает тест;
- указывает миграцию данных;
- оценивает влияние на стоимость и эксплуатацию;
- не требует переписать всё без доказанной причины.

Плохое предложение:

- «добавить AI для улучшения качества» без метрики;
- «спарсить Instagram» без правовой и платформенной модели;
- заменить score целиком LLM-решением;
- автоматически отправлять сообщения;
- трактовать cached evidence как live;
- обещать рост продаж без эксперимента.

## 13. Формат ответа для другой модели

Просите модель отвечать так:

1. Что она считает фактом из контекста.
2. Какие делает предположения.
3. Какие проблемы нашла.
4. Приоритет `P0/P1/P2`.
5. Предлагаемое изменение.
6. Какие файлы/контракты меняются.
7. Критерии приёмки.
8. Тесты/evals.
9. Риски и rollback.
10. Что не следует делать сейчас.

## 14. Базовый промпт для нового диалога

```text
Ты выступаешь как senior product/AI/engineering reviewer системы LD LATTE
Influencer Scout.

Прочитай приложенный контекст и релевантные файлы репозитория. Не приписывай
MVP функции из раздела «не реализовано». Сначала перечисли проверенные факты и
предположения. Затем реши задачу: <ВСТАВИТЬ КОНКРЕТНУЮ ЗАДАЧУ>.

Сохраняй принципы:
- evidence before inference;
- missing != 0;
- LLM не придумывает URL;
- итоговый score детерминирован;
- legal activation отделён от research;
- любое сообщение требует human approval.

Ответ дай в структуре:
1) диагноз;
2) варианты;
3) рекомендуемый вариант и почему;
4) изменения по файлам/контрактам;
5) критерии приёмки;
6) тесты/evals;
7) риски/rollback;
8) открытые вопросы.

Не предлагай общий rewrite, если проблему можно решить локально.
```

## 15. Какие файлы приложить

Минимум:

- `docs/part1-system-dossier.md`;
- `ldlatte_agent/models.py`;
- `ldlatte_agent/pipeline.py`;
- файл компонента, который разбирается;
- соответствующий prompt;
- `tests/test_pipeline.py`.

Для анализа данных:

- `examples/seed_annotations.json` для публичного demo; приватную разметку
  исходной таблицы передавать только в закрытом контуре;
- `data/candidates.json`;
- обезличенную/разрешённую копию структуры workbook либо агрегированную сводку.

Не отправлять:

- `.env`;
- API-ключ;
- закрытые данные без разрешения;
- исходную таблицу в публичный сервис, если это запрещено владельцем данных.

## 16. Машиночитаемый snapshot

```yaml
project: ldlatte-influencer-scout
version: 0.1.0
snapshot_date: 2026-07-27
language: python
ui: streamlit
llm_provider: deepseek
input:
  workbook_sheets: 2
  seed_profiles: 34
  hyperlink_overrides: 6
seed_evidence:
  annotated: 21
  unknown: 13
  coverage: 0.62
roles:
  core_creator: 8
  visual_reference: 2
  secondary_cluster: 6
  outlier: 5
  unknown: 13
output:
  candidates: 5
  scores: [87.3, 87.2, 85.3, 79.9, 72.0]
tests:
  total: 52
  passed_public_ci: 50
  skipped_public_ci: 2
  failed: 0
external:
  google_sheets_public_export: implemented
  public_index_seed_enrichment: implemented_mvp
  ddgs_discovery: implemented
  deepseek_json: implemented
  youtube_adapter: false
  instagram_graph_adapter: false
human_approval_required: true
auto_send: false
main_gap: automatic_seed_enrichment_and_multimodal_evidence
```
