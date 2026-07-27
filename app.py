from __future__ import annotations

import json

import streamlit as st

from ldlatte_agent.pipeline import ROOT, run_pipeline

st.set_page_config(
    page_title="LD LATTE Influencer Scout",
    page_icon="🤍",
    layout="wide",
)

st.title("LD LATTE Influencer Scout")
st.caption(
    "Excel → портрет → новые реальные кандидаты → объяснимый скоринг → персональные офферы"
)

with st.sidebar:
    st.header("Запуск")
    mode = st.radio(
        "Режим",
        ["Демо", "Live: DeepSeek", "Live: поиск + DeepSeek"],
        help="Демо не расходует токены и использует сохранённый снимок источников.",
    )
    limit = st.slider("Сколько кандидатов показать", 3, 5, 5)
    uploaded = st.file_uploader("Или загрузите другой XLSX", type=["xlsx"])
    sheet_url = st.text_input(
        "Или вставьте Google Sheets URL",
        placeholder="https://docs.google.com/spreadsheets/d/…",
        help="Работает для таблиц с доступом по ссылке. Закрытая таблица требует service account.",
    )
    default_path = ROOT / "examples" / "bloggers-demo.xlsx"
    st.caption(f"По умолчанию: {default_path.name} — синтетические данные")
    run = st.button("Запустить цикл", type="primary", use_container_width=True)

if not run:
    st.info("Нажмите «Запустить цикл». Для первой проверки оставьте режим «Демо».")
    st.stop()

source = uploaded if uploaded is not None else sheet_url.strip() or default_path
live_llm = mode != "Демо"
live_discovery = mode == "Live: поиск + DeepSeek"

try:
    with st.status("Выполняю pipeline…", expanded=True) as status:
        st.write("1/4 Читаю Excel и нормализую hyperlink-адреса")
        result = run_pipeline(
            source,
            live_llm=live_llm,
            live_discovery=live_discovery,
            limit=limit,
        )
        st.write("2/4 Строю кластерный портрет")
        st.write("3/4 Проверяю и ранжирую кандидатов")
        st.write("4/4 Формирую офферы; отправка остаётся на ручном подтверждении")
        status.update(label="Готово", state="complete")
except Exception as exc:
    st.error(str(exc))
    st.stop()

tabs = st.tabs(["Исходник", "Портрет", "Кандидаты", "Офферы", "Экспорт"])

with tabs[0]:
    a, b, c = st.columns(3)
    a.metric("Уникальных seed-профилей", len(result.seeds))
    b.metric("Исправлено скрытых ссылок", result.data_quality["hyperlink_overrides"])
    c.metric("Режим", result.run_meta["mode"])
    st.json(result.data_quality)
    st.dataframe(
        [
            {
                "№": seed.number,
                "строка Excel": seed.excel_row,
                "handle": seed.handle,
                "нормализованный URL": seed.normalized_url,
            }
            for seed in result.seeds
        ],
        use_container_width=True,
        hide_index=True,
    )

with tabs[1]:
    st.subheader("Портрет идеального блогера")
    st.json(result.portrait)
    st.warning(
        "Портрет не является средним по всем строкам: visual references и тематические "
        "выбросы отделены от core creators."
    )

with tabs[2]:
    st.dataframe(
        [
            {
                "score": candidate.score,
                "профиль": candidate.title,
                "платформа": candidate.platform,
                "подписчики": candidate.followers,
                "средние просмотры": candidate.avg_views,
                "статус": candidate.cooperation_status,
                "почему": candidate.reason,
                "URL": candidate.url,
            }
            for candidate in result.candidates
        ],
        use_container_width=True,
        hide_index=True,
    )
    for candidate in result.candidates:
        with st.expander(f"{candidate.score} — {candidate.title}"):
            st.write(candidate.reason)
            st.write("Наблюдаемые факты:")
            for fact in candidate.facts:
                st.write(f"- {fact}")
            st.write("Источники:")
            for source_item in candidate.sources:
                st.markdown(
                    f"- [{source_item['url']}]({source_item['url']}) — "
                    f"{source_item['note']}"
                )

with tabs[3]:
    st.warning("Черновики. Перед отправкой обязательны проверка менеджером и согласование условий.")
    for candidate in result.candidates:
        st.subheader(candidate.title)
        st.text_area(
            f"Оффер для @{candidate.handle}",
            candidate.offer,
            height=260,
            key=f"offer_{candidate.handle}",
        )

with tabs[4]:
    payload = json.dumps(result.to_dict(), ensure_ascii=False, indent=2)
    st.download_button(
        "Скачать полный JSON",
        payload,
        file_name="ldlatte_influencer_results.json",
        mime="application/json",
    )
    with st.expander("Предпросмотр JSON"):
        st.code(payload, language="json")
