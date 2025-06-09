import streamlit as st
import pandas as pd

st.set_page_config(page_title="Повтор по ошибкам", layout="centered")
st.title("📘 Повторное тестирование по ошибкам")

# 🔁 Кнопка сброса
if st.button("🔁 Начать заново"):
    for k in list(st.session_state.keys()):
        del st.session_state[k]
    st.rerun()

# 🧠 Состояния
defaults = {
    "step": 0,
    "score": 0,
    "answers": [],
    "show_result": False,
    "selected_option": None,
    "last_result": None,
    "current_df": None,
    "df_full": None,
}
for k, v in defaults.items():
    if k not in st.session_state:
        st.session_state[k] = v

# Загрузка Excel
st.markdown("### 📘 Загрузите Excel-файл с полными вопросами")
xlsx_file = st.file_uploader("Excel (.xlsx)", type=["xlsx"], key="xlsx")

# Загрузка CSV
st.markdown("### 📄 Загрузите CSV-файл с ошибками")
csv_file = st.file_uploader("CSV (.csv)", type=["csv"], key="csv")

if xlsx_file:
    try:
        df_full = pd.read_excel(xlsx_file)
        df_full = df_full.dropna(subset=["Вопрос", "Правильный ответ"])
        df_full["Вопрос_норм"] = df_full["Вопрос"].astype(str).str.strip().str.lower()
        st.session_state.df_full = df_full
        st.success("✅ Excel-файл загружен")
    except Exception as e:
        st.error(f"Ошибка чтения Excel: {e}")
        st.stop()

if csv_file and st.session_state.df_full is not None:
    try:
        df_csv = pd.read_csv(csv_file, encoding="utf-8")
        df_csv.columns = [col.strip().lower() for col in df_csv.columns]  # Приведение к нижнему регистру

        if "вопрос" not in df_csv.columns:
            st.error("CSV должен содержать колонку 'Вопрос'")
            st.stop()

        df_csv["вопрос_норм"] = df_csv["вопрос"].astype(str).str.strip().str.lower()
        df_full = st.session_state.df_full
        df_full["Вопрос_норм"] = df_full["Вопрос"].astype(str).str.strip().str.lower()

        df_matched = df_full[df_full["Вопрос_норм"].isin(df_csv["вопрос_норм"])]
        if df_matched.empty:
            st.warning("❌ Ни один вопрос из CSV не найден в Excel.")
            st.stop()

        st.session_state.current_df = df_matched.reset_index(drop=True)
        st.success(f"✅ Найдено {len(df_matched)} вопросов по ошибкам")
    except Exception as e:
        st.error(f"Ошибка чтения CSV: {e}")
        st.stop()

# Тестирование
df = st.session_state.current_df
if df is not None and not df.empty:
    step = st.session_state.step
    total = len(df)

    st.markdown(f"**Прогресс:** Вопрос {step+1} из {total}")

    # 🔳 Прогрессбар
    BAR_CELLS = 18
    bar_html = '<div style="display: flex; gap: 2px;">'
    for i in range(BAR_CELLS):
        rel_idx = int(i / BAR_CELLS * total)
        if rel_idx >= total:
            color = "black"
        else:
            q_index = df.iloc[rel_idx].name
            a = next((x for x in st.session_state.answers if x["Индекс"] == q_index), None)
            color = "green" if a and a["Результат"] == "✅ Верно" else "red" if a else "black"
        bar_html += f'<div style="width:20px;height:20px;background-color:{color};border:1px solid #555;"></div>'
    bar_html += "</div>"
    st.markdown(bar_html, unsafe_allow_html=True)

    # Статистика
    correct = sum(1 for a in st.session_state.answers if a["Результат"] == "✅ Верно")
    wrong = sum(1 for a in st.session_state.answers if a["Результат"] == "❌ Неверно")
    st.markdown(f"✅ Правильно: {correct} | ❌ Неправильно: {wrong} | ⬛ Осталось: {total - (correct + wrong)}")

    # Вопрос
    if step < total:
        row = df.iloc[step]
        st.markdown(f"### {row['Вопрос']}")

        options = ['A', 'B', 'C', 'D', 'E', 'F']
        valid_options = [(opt, str(row.get(opt))) for opt in options if pd.notna(row.get(opt))]
        correct_answer = str(row['Правильный ответ']).strip().upper()

        selected = st.radio(
            "Выберите ответ:",
            [f"{opt}) {text}" for opt, text in valid_options],
            key=f"q_{step}"
        )

        if not st.session_state.show_result:
            if st.button("Ответить"):
                letter = selected[0]
                is_correct = letter == correct_answer
                st.session_state.answers.append({
                    "Индекс": row.name,
                    "Вопрос": row["Вопрос"],
                    "Вы выбрали": letter,
                    "Правильный ответ": correct_answer,
                    "Результат": "✅ Верно" if is_correct else "❌ Неверно"
                })
                if is_correct:
                    st.session_state.score += 1
                st.session_state.last_result = is_correct
                st.session_state.show_result = True
                st.rerun()
        else:
            if st.button("Следующий вопрос"):
                st.session_state.step += 1
                st.session_state.show_result = False
                st.session_state.last_result = None
                st.rerun()

            if st.session_state.last_result:
                st.markdown("✅ **Верно!**")
            else:
                st.markdown(f"❌ **Неверно. Правильный ответ: {correct_answer}**")

    else:
        st.success("🎉 Повторное тестирование завершено.")
        st.markdown(f"**Правильных ответов: {st.session_state.score} из {total}**")

        with st.expander("📋 История ответов"):
            df_result = pd.DataFrame(st.session_state.answers)
            st.dataframe(df_result[["Вопрос", "Вы выбрали", "Правильный ответ", "Результат"]])
else:
    st.info("📂 Загрузите оба файла (xlsx + csv), чтобы начать.")
