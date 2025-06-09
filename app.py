import streamlit as st
import pandas as pd

st.set_page_config(page_title="Повтор ошибок", layout="centered")
st.title("🧠 Повторное тестирование по ошибкам")

# 🔁 Кнопка сброса
if st.button("🔁 Начать заново"):
    for key in list(st.session_state.keys()):
        del st.session_state[key]
    st.rerun()

# 🧠 Инициализация состояния
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

# 📂 Загрузка Excel-файла
st.markdown("### 📘 Загрузите Excel-файл с вопросами")
uploaded_excel = st.file_uploader("Excel (.xlsx)", type=["xlsx"], key="excel")

if uploaded_excel:
    try:
        df_full = pd.read_excel(uploaded_excel, sheet_name=0)
        df_full = df_full.dropna(subset=["Вопрос", "Правильный ответ"])
        df_full["Вопрос_норм"] = df_full["Вопрос"].astype(str).str.strip().str.lower()
        st.session_state.df_full = df_full.copy()
        st.success("✅ Excel-файл загружен!")
    except Exception as e:
        st.error(f"Ошибка Excel: {e}")
        st.stop()

# 📂 Загрузка CSV-файла
st.markdown("### 📄 Загрузите CSV-файл с ошибками")
uploaded_csv = st.file_uploader("CSV (.csv)", type=["csv"], key="csv")

if uploaded_csv and st.session_state.df_full is not None:
    try:
        df_errors = pd.read_csv(uploaded_csv)
        if "Вопрос" not in df_errors.columns:
            st.error("CSV должен содержать колонку 'Вопрос'")
            st.stop()

        df_errors["Вопрос_норм"] = df_errors["Вопрос"].astype(str).str.strip().str.lower()
        df_full = st.session_state.df_full.copy()
        df_matched = df_full[df_full["Вопрос_норм"].isin(df_errors["Вопрос_норм"])]

        if df_matched.empty:
            st.error("❌ Ни один вопрос из CSV не найден в Excel.")
            st.stop()

        st.session_state.current_df = df_matched.reset_index(drop=True)
        st.success(f"✅ Найдено {len(df_matched)} вопросов из CSV в Excel.")

    except Exception as e:
        st.error(f"Ошибка CSV: {e}")
        st.stop()

# 👉 Основная логика тестирования
df = st.session_state.current_df
if df is not None and not df.empty:
    current_step = st.session_state.step
    total_questions = len(df)

    st.markdown(f"**Прогресс:** Вопрос {current_step + 1} из {total_questions}")

    # Прогрессбар из 18 клеток
    BAR_CELLS = 18
    html_bar = '<div style="display: flex; gap: 2px;">'
    for i in range(BAR_CELLS):
        rel_idx = int(i / BAR_CELLS * total_questions)
        if rel_idx >= total_questions:
            color = "black"
        else:
            q_index = df.iloc[rel_idx].name
            answer = next((a for a in st.session_state.answers if a["Индекс"] == q_index), None)
            color = "green" if answer and answer["Результат"] == "✅ Верно" else "red" if answer else "black"
        html_bar += f'<div style="width: 20px; height: 20px; background-color: {color}; border: 1px solid #555;"></div>'
    html_bar += '</div>'
    st.markdown(html_bar, unsafe_allow_html=True)

    correct_count = sum(1 for a in st.session_state.answers if a["Результат"] == "✅ Верно")
    wrong_count = sum(1 for a in st.session_state.answers if a["Результат"] == "❌ Неверно")
    st.markdown(f"✅ Правильно: {correct_count} | ❌ Неправильно: {wrong_count} | ⬛ Осталось: {total_questions - (correct_count + wrong_count)}")

    # Текущий вопрос
    if current_step < total_questions:
        row = df.iloc[current_step]
        st.markdown(f"### {row['Вопрос']}")

        options = ['A', 'B', 'C', 'D', 'E', 'F']
        valid_options = [(opt, str(row.get(opt))) for opt in options if pd.notna(row.get(opt))]
        correct_answer = str(row['Правильный ответ']).strip().upper()

        selected = st.radio(
            "Выберите ответ:",
            [f"{opt}) {text}" for opt, text in valid_options],
            key=f"q_{current_step}"
        )

        if not st.session_state.show_result:
            if st.button("Ответить"):
                selected_letter = selected[0]
                is_correct = selected_letter == correct_answer
                st.session_state.selected_option = selected_letter
                st.session_state.last_result = is_correct
                st.session_state.answers.append({
                    "Индекс": row.name,
                    "Вопрос": row["Вопрос"],
                    "Вы выбрали": selected_letter,
                    "Правильный ответ": correct_answer,
                    "Результат": "✅ Верно" if is_correct else "❌ Неверно"
                })
                if is_correct:
                    st.session_state.score += 1
                st.session_state.show_result = True
                st.rerun()

        else:
            if st.button("Следующий вопрос"):
                st.session_state.step += 1
                st.session_state.show_result = False
                st.session_state.selected_option = None
                st.session_state.last_result = None
                st.rerun()

            if st.session_state.last_result:
                st.markdown("✅ **Верно!**")
            else:
                st.markdown(f"❌ **Неверно. Правильный ответ: {correct_answer}**")

    elif current_step >= total_questions:
        st.success("🎉 Повторное тестирование завершено!")
        st.markdown(f"**Правильных ответов: {st.session_state.score} из {total_questions}**")

        with st.expander("📋 История ответов"):
            df_result = pd.DataFrame(st.session_state.answers)
            st.dataframe(df_result[["Вопрос", "Вы выбрали", "Правильный ответ", "Результат"]])

else:
    st.info("Загрузите Excel и CSV, чтобы начать тестирование.")
