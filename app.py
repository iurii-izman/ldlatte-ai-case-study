"""Streamlit UI for LD LATTE Influencer Scout — demo-first, recruiter-facing."""

from __future__ import annotations

import csv
import io
import json

import streamlit as st

from ldlatte_agent.pipeline import ROOT, run_pipeline

# ── page config ──────────────────────────────────────────────────────

st.set_page_config(
    page_title="LD LATTE Influencer Scout",
    page_icon="🤍",
    layout="wide",
)

# ── helpers ──────────────────────────────────────────────────────────

MODE_META = {
    "Демо": {
        "tokens": False,
        "network": False,
        "local": True,
        "description": (
            "Использует rule-based портрет и сохранённый исследовательский "
            "снимок кандидатов. Не расходует токены, не делает сетевых запросов."
        ),
    },
    "Live: DeepSeek": {
        "tokens": True,
        "network": True,
        "local": False,
        "description": (
            "LLM-портрет и LLM-офферы через DeepSeek API. Кандидаты — "
            "из сохранённого снимка. Расходует токены."
        ),
    },
    "Live: поиск + DeepSeek": {
        "tokens": True,
        "network": True,
        "local": False,
        "description": (
            "Собирает публичные evidence по исходным профилям, ищет новых "
            "кандидатов через DuckDuckGo и строит портрет и офферы через "
            "DeepSeek. Результаты зависят от поискового индекса."
        ),
    },
}


def _fmt(val, default: str = "—") -> str:
    """Format a value for display; None → placeholder, not zero."""
    if val is None:
        return default
    if isinstance(val, float):
        return f"{val:.2f}"
    return str(val)


def _risk_color(risk: float) -> str:
    if risk >= 0.15:
        return "red"
    if risk >= 0.08:
        return "orange"
    return "green"


def _conf_color(conf: float) -> str:
    if conf >= 0.85:
        return "green"
    if conf >= 0.70:
        return "orange"
    return "red"


# ── build CSV ────────────────────────────────────────────────────────


def _build_shortlist_csv(candidates) -> str:
    buf = io.StringIO()
    writer = csv.writer(buf)
    writer.writerow([
        "rank", "score", "confidence", "risk", "platform", "title",
        "handle", "url", "reason", "cooperation_status", "contact",
    ])
    for i, c in enumerate(candidates, 1):
        writer.writerow([
            i,
            _fmt(c.score),
            _fmt(c.confidence),
            _fmt(c.risk),
            c.platform,
            c.title,
            c.handle,
            c.url,
            c.reason,
            c.cooperation_status,
            c.contact,
        ])
    return buf.getvalue()


# ── error classifier ─────────────────────────────────────────────────


def _classify_error(exc: Exception, mode: str) -> str:
    msg = str(exc).lower()
    if "no such file" in msg or "file not found" in msg or "enoent" in msg:
        return "Файл не найден. Проверьте путь к XLSX."
    if "sheet" in msg and ("not found" in msg or "не найден" in msg):
        return "Лист не найден в книге. Проверьте название листа (ожидается «Исходник»)."
    if "badzipfile" in msg or "corrupt" in msg or "поврежд" in msg:
        return (
            "XLSX-файл повреждён или имеет неверный формат. "
            "Попробуйте открыть файл в Excel и сохранить заново."
        )
    if "deepseek_api_key" in msg or "api key" in msg or "не найден" in msg:
        return (
            "Не найден DEEPSEEK_API_KEY. "
            "Создайте .env файл по образцу .env.example и укажите ключ."
        )
    if "deepseek" in msg and ("error" in msg or "http" in msg or "status" in msg):
        return "Ошибка DeepSeek API. Проверьте ключ, баланс и доступность сервиса."
    if "google sheets" in msg or ("google" in msg and "sheet" in msg):
        return "Google Sheets недоступна. Проверьте, что таблица открыта по ссылке и URL корректен."
    if "valid json" in msg or "json" in msg:
        return "DeepSeek вернул ответ в неверном формате. Попробуйте ещё раз."
    if "timeout" in msg or "timed out" in msg:
        return "Превышено время ожидания ответа от API. Проверьте подключение к интернету."
    return f"Непредвиденная ошибка: {exc}"


# ── landing ──────────────────────────────────────────────────────────

if "pipeline_has_run" not in st.session_state:
    st.session_state.pipeline_has_run = False

if not st.session_state.pipeline_has_run:
    st.title("🤍 LD LATTE Influencer Scout")
    st.markdown("### Что делает инструмент")
    st.markdown(
        "Помогает бренду женской одежды **LD LATTE** находить блогеров "
        "для бартерных интеграций: от Excel-таблицы с референсами до "
        "короткого списка из 3–5 новых кандидатов с персональными "
        "черновиками предложений."
    )

    col1, col2, col3 = st.columns(3)
    with col1:
        st.markdown("**📥 Вход**")
        st.markdown("- Excel с Instagram-ссылками\n- или Google Sheets\n- или загрузка XLSX")
    with col2:
        st.markdown("**⚙️ Обработка**")
        st.markdown(
            "- Нормализация hyperlink\n- Кластерный портрет\n"
            "- Поиск и проверка URL\n- Объяснимый скоринг"
        )
    with col3:
        st.markdown("**📤 Выход**")
        st.markdown(
            "- 3–5 новых кандидатов\n- Оценки и доказательства\n"
            "- Персональные черновики\n- JSON / CSV экспорт"
        )

    st.info(
        "**Демо-режим** использует синтетический seed из `examples/bloggers-demo.xlsx` "
        "и сохранённый снимок пяти публичных кандидатов из `data/candidates.json`. "
        "Никакие реальные профили, ключи или приватные данные не требуются."
    )

    st.warning(
        "**Отправка офферов не автоматизирована.** Все черновики требуют "
        "ручной проверки менеджером: актуальность профиля, охваты, контакт, "
        "условия и юридическая допустимость площадки."
    )

    st.caption(
        "Настройте параметры в боковой панели слева и нажмите «Запустить цикл»."
    )

# ── sidebar ──────────────────────────────────────────────────────────

with st.sidebar:
    st.header("🚀 Запуск")

    mode = st.radio(
        "Режим работы",
        ["Демо", "Live: DeepSeek", "Live: поиск + DeepSeek"],
        help="Выберите режим. Демо — без токенов и сети.",
    )

    meta = MODE_META[mode]
    st.caption(meta["description"])

    cols_meta = st.columns(3)
    cols_meta[0].metric("Токены", "✅ нет" if not meta["tokens"] else "⚠️ да", delta=None)
    cols_meta[1].metric("Сеть", "✅ нет" if not meta["network"] else "🌐 да", delta=None)
    cols_meta[2].metric("Локально", "✅ да" if meta["local"] else "🌐 нет", delta=None)

    limit = st.slider("Максимум кандидатов", 3, 5, 5)

    st.divider()
    st.caption("**Свой источник данных** (опционально)")

    uploaded = st.file_uploader(
        "Загрузить XLSX",
        type=["xlsx"],
        help="Загрузите свой Excel-файл с колонками: номер, ссылка.",
    )

    sheet_url = st.text_input(
        "Google Sheets URL",
        placeholder="https://docs.google.com/spreadsheets/d/…",
        help="Работает для таблиц с доступом по ссылке. Закрытая таблица требует service account.",
    )

    st.divider()

    default_path = ROOT / "examples" / "bloggers-demo.xlsx"
    if not uploaded and not sheet_url.strip():
        st.caption(f"📄 По умолчанию: **{default_path.name}** (синтетические данные)")

    run = st.button("Запустить цикл", type="primary", use_container_width=True)

# ── execution ────────────────────────────────────────────────────────

if not run:
    st.stop()

source = uploaded if uploaded is not None else sheet_url.strip() or default_path
live_llm = mode != "Демо"
live_discovery = mode == "Live: поиск + DeepSeek"
live_seed_enrichment = mode == "Live: поиск + DeepSeek"

try:
    with st.status("Выполняю pipeline…", expanded=True) as status:
        st.write("1/5 Чтение Excel, нормализация hyperlink-адресов")
        result = run_pipeline(
            source,
            live_llm=live_llm,
            live_seed_enrichment=live_seed_enrichment,
            live_discovery=live_discovery,
            limit=limit,
        )
        st.write(
            "2/5 Сбор датированных evidence по исходным профилям"
            if live_seed_enrichment
            else "2/5 Загрузка сохранённых seed-evidence"
        )
        st.write("3/5 Построение кластерного портрета блогера")
        st.write("4/5 Поиск, проверка URL и ранжирование кандидатов")
        st.write("5/5 Формирование офферов (отправка — только после ручного подтверждения)")
        status.update(label="✅ Pipeline завершён", state="complete")
    st.session_state.pipeline_has_run = True
except Exception as exc:
    friendly = _classify_error(exc, mode)
    st.error(f"**Ошибка:** {friendly}")
    st.stop()

# ── tabs ─────────────────────────────────────────────────────────────

tabs = st.tabs([
    "📊 Данные",
    "🎨 Портрет",
    "👤 Кандидаты",
    "📝 Офферы",
    "📦 Экспорт",
    "⚠️ Ограничения",
])

# ── tab 0: Data quality ──────────────────────────────────────────────

with tabs[0]:
    st.subheader("Качество входных данных")
    dq = result.data_quality
    col_a, col_b, col_c, col_d = st.columns(4)
    col_a.metric("Уникальных профилей", dq.get("unique_profiles", len(result.seeds)))
    col_b.metric("Исправлено скрытых ссылок", dq.get("hyperlink_overrides", 0))
    col_c.metric("Пропущено (не URL)", dq.get("skipped_non_profiles", 0))
    col_d.metric("Режим", result.run_meta.get("mode", "—"))

    if dq.get("live_discovery_fallback"):
        st.warning(dq["live_discovery_fallback"])
    if dq.get("seed_enrichment_fallback"):
        st.warning(dq["seed_enrichment_fallback"])
    if dq.get("seed_enrichment_search_failures"):
        st.warning(
            "Часть seed-запросов не сработала: "
            f"{dq['seed_enrichment_search_failures']}. "
            "Пропуски сохранены как unknown."
        )

    st.caption("Сырой отчёт data_quality")
    st.json(dq)

    st.caption("Нормализованные seed-профили")
    st.dataframe(
        [
            {
                "№": seed.number if seed.number is not None else "—",
                "Строка Excel": seed.excel_row,
                "Handle": f"@{seed.handle}",
                "URL": seed.normalized_url,
            }
            for seed in result.seeds
        ],
        use_container_width=True,
        hide_index=True,
    )

# ── tab 1: Portrait ──────────────────────────────────────────────────

with tabs[1]:
    st.subheader("Портрет идеального блогера")

    portrait = result.portrait
    method = portrait.get("method", "rule-based" if not live_llm else "llm")
    st.caption(f"Метод: {method}")

    if portrait.get("summary"):
        st.info(portrait["summary"])

    if portrait.get("clusters"):
        st.markdown("**Кластеры seed-базы**")
        for cluster in portrait["clusters"]:
            cluster_label = (
                f"{cluster.get('name', '—')} "
                f"({len(cluster.get('handles', []))} профилей)"
            )
            with st.expander(cluster_label):
                st.write(cluster.get("why", "—"))
                st.write(", ".join(cluster.get("handles", [])))

    col_ae, col_op = st.columns(2)
    with col_ae:
        archetype = portrait.get("aesthetic_archetype", {})
        if archetype:
            st.markdown("**Эстетический архетип**")
            if archetype.get("visual"):
                st.markdown("*Визуал:*")
                for v in archetype["visual"]:
                    st.markdown(f"- {v}")
            if archetype.get("voice"):
                st.markdown("*Голос:*")
                for v in archetype["voice"]:
                    st.markdown(f"- {v}")
            if archetype.get("content"):
                st.markdown("*Контент:*")
                for v in archetype["content"]:
                    st.markdown(f"- {v}")

    with col_op:
        op_fit = portrait.get("operational_fit", {})
        if op_fit:
            st.markdown("**Операционная пригодность**")
            if op_fit.get("must_have"):
                st.markdown("*Обязательно:*")
                for item in op_fit["must_have"]:
                    st.markdown(f"- {item}")
            if op_fit.get("preferred"):
                st.markdown("*Желательно:*")
                for item in op_fit["preferred"]:
                    st.markdown(f"- {item}")
            if op_fit.get("exclude_or_review"):
                st.markdown("*Исключить / ручная проверка:*")
                for item in op_fit["exclude_or_review"]:
                    st.markdown(f"- {item}")

    if portrait.get("evidence_coverage") is not None:
        ec = portrait["evidence_coverage"]
        ec_pct = round(ec * 100)
        st.metric("Evidence coverage", f"{ec_pct}%")

    if portrait.get("limitations"):
        with st.expander("Ограничения портрета"):
            for lim in portrait["limitations"]:
                st.markdown(f"- {lim}")

    st.caption(
        "Портрет не усредняет все seed-профили: visual references и "
        "тематические выбросы отделены от core creators."
    )

# ── tab 2: Candidates ────────────────────────────────────────────────

with tabs[2]:
    st.subheader("Ранжированные кандидаты")

    # Summary table
    st.dataframe(
        [
            {
                "Score": _fmt(c.score),
                "Conf.": f"{c.confidence:.0%}",
                "Риск": f"{c.risk:.0%}",
                "Профиль": c.title,
                "Платформа": c.platform,
                "Подписчики": _fmt(c.followers),
                "Просмотры": _fmt(c.avg_views),
                "ER": _fmt(c.engagement_rate),
                "Бартер": c.cooperation_status,
                "Anchor": c.offer_anchor[:80] + ("…" if len(c.offer_anchor) > 80 else ""),
            }
            for c in result.candidates
        ],
        use_container_width=True,
        hide_index=True,
    )

    st.divider()

    # Detailed card per candidate
    for i, c in enumerate(result.candidates, 1):
        with st.expander(
            f"#{i}  Score: {_fmt(c.score)}  |  {c.title}  |  {c.platform}",
            expanded=(i == 1),
        ):
            # Metrics row
            m1, m2, m3, m4, m5, m6 = st.columns(6)
            m1.metric("Score", _fmt(c.score))
            m2.metric(
                "Confidence",
                f"{c.confidence:.0%}",
                delta=None,
                delta_color="off",
                help="Уверенность в полноте и достоверности данных.",
            )
            m3.metric(
                "Risk",
                f"{c.risk:.0%}",
                delta=None,
                delta_color="off",
                help="Штраф за риск-сигналы (репутация, противоречия).",
            )
            m4.metric("Подписчики", _fmt(c.followers))
            m5.metric("Ср. просмотры", _fmt(c.avg_views))
            m6.metric("Engagement rate", _fmt(c.engagement_rate))

            # Reason
            if c.reason:
                st.markdown(f"**Почему подходит:** {c.reason}")

            # Bar status
            st.markdown(f"**Бартерный статус:** {c.cooperation_status}")
            st.markdown(f"**Контакт:** {c.contact}")

            # Facts
            if c.facts:
                st.markdown("**Наблюдаемые факты:**")
                for fact in c.facts:
                    st.markdown(f"- {fact}")

            # Anchor
            if c.offer_anchor:
                st.markdown(f"**Anchor для оффера:** _{c.offer_anchor}_")

            # Sources with dates
            if c.sources:
                st.markdown("**Источники:**")
                for src in c.sources:
                    observed = src.get("observed_at", "—")
                    url = src.get("url", "")
                    note = src.get("note", "")
                    st.markdown(
                        f"- [{url}]({url})  \n"
                        f"  *{observed}* — {note[:200]}"
                    )

            # Features (collapsed)
            if c.features:
                with st.expander("🧮 Признаки (features)"):
                    st.json(c.features)

            # URL link
            st.markdown(f"🔗 [{c.url}]({c.url})")

# ── tab 3: Offers ────────────────────────────────────────────────────

with tabs[3]:
    st.subheader("Черновики предложений")

    st.warning(
        "**⚠️ Сообщения не отправлены.** Каждый оффер — черновик. "
        "Перед контактом менеджер обязан проверить:"
    )
    cols_check = st.columns(3)
    cols_check[0].markdown("- Актуальность профиля")
    cols_check[1].markdown("- Охваты и метрики")
    cols_check[2].markdown("- Контакт и условия")
    st.caption(
        "Юридическая допустимость площадки, маркировка рекламы и "
        "права на контент проверяются отдельно."
    )

    st.divider()

    for c in result.candidates:
        st.markdown(f"### {c.title}")
        st.caption(
            f"Платформа: {c.platform}  ·  "
            f"Anchor: _{c.offer_anchor[:100]}{'…' if len(c.offer_anchor) > 100 else ''}_"
        )
        st.text_area(
            "Черновик оффера",
            c.offer,
            height=220,
            key=f"offer_{c.handle}",
            label_visibility="collapsed",
        )
        st.caption("✏️ Текст можно редактировать перед копированием.")
        st.divider()

# ── tab 4: Export ────────────────────────────────────────────────────

with tabs[4]:
    st.subheader("Экспорт результатов")

    col_json, col_csv = st.columns(2)

    with col_json:
        payload = json.dumps(result.to_dict(), ensure_ascii=False, indent=2)
        st.download_button(
            "📥 Скачать полный JSON",
            payload,
            file_name="ldlatte_influencer_results.json",
            mime="application/json",
            use_container_width=True,
        )
        with st.expander("Предпросмотр JSON"):
            st.code(payload, language="json")

    with col_csv:
        csv_data = _build_shortlist_csv(result.candidates)
        st.download_button(
            "📥 Скачать shortlist CSV",
            csv_data,
            file_name="ldlatte_influencer_shortlist.csv",
            mime="text/csv",
            use_container_width=True,
        )
        with st.expander("Предпросмотр CSV"):
            st.code(csv_data, language="text")

    st.caption(
        "Экспорт не содержит API-ключ, приватный seed-список или "
        "необработанные персональные данные."
    )

# ── tab 5: Limitations ───────────────────────────────────────────────

with tabs[5]:
    st.subheader("Ограничения текущей версии")

    st.markdown("**Исследовательские**")
    st.markdown(
        "- Instagram discovery ограничен индексируемыми публичными результатами.\n"
        "- YouTube Shorts adapter пока не реализован.\n"
        "- Мультимодальный анализ визуала не выполняется.\n"
        "- Метрики получены из публичных источников и требуют проверки перед контактом."
    )

    st.markdown("**Операционные**")
    st.markdown(
        "- Отправка офферов не автоматизирована и невозможна из интерфейса.\n"
        "- Нет CRM-интеграции, базы данных и аудита.\n"
        "- Live-результаты недетерминированы и зависят от поискового индекса.\n"
        "- Отсутствует проверка юридической допустимости площадки."
    )

    st.markdown("**Интерфейс**")
    st.markdown(
        "- Streamlit-прототип, не production dashboard.\n"
        "- Нет ролевой модели и аутентификации.\n"
        "- Публичный деплой потребует auth и cost limits."
    )

    st.info(
        "Полный backlog и план развития: "
        "[part1-improvement-backlog.md](docs/part1-improvement-backlog.md)"
    )
