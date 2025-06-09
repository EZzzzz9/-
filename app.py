import streamlit as st
import pandas as pd

st.set_page_config(page_title="Тест с повтором ошибок", layout="centered")
st.title("🧠 Тестирование с ручным переходом")

# 🔄 Сброс состояния
with st.sidebar:
    if st.button("🔁 Начать заново"):
        for key in list(st.session_state.keys()):
            del st.session_state[key]
        st.rerun()

# 🧠 Инициализация session_state
defaults = {
    "mode": "full_test",
    "step": 0,
    "score": 0,
    "answers": [],
    "finished": False,
    "show_result": False,
    "selected_option": None,
    "last_result": None,
    "current_df": None
}
for key, val in defaults.items():
    if key not in st.session_state:
        st.session_state[key] = val

uploaded_file = st.file_uploader("Загрузите Excel-файл с вопросами", type=["xlsx"])

if uploaded_file:
    try:
        df_full = pd.read_excel(uploaded_file, sheet_name="Sheet1")
        df_full = df_full.dropna(subset=["Вопрос", "Правильный ответ"])
    except Exception as e:
        st.error(f"Ошибка при чтении файла: {e}")
        st.stop()

    with st.expander("📄 Просмотр загруженных данных"):
        st.dataframe(df_full)

    if st.session_state.current_df is None:
        st.session_state.current_df = df_full.copy()

    df = st.session_state.current_df
    total_questions = len(df)

    # 🔢 Прогрессбар из 18 HTML-клеток
    def render_html_progress():
        progress_html = ""
        total_cells = 18
        answered = st.session_state.answers
        filled_cells = min(len(answered), total_cells)

        for i in range(total_cells):
            if i < len(answered):
                result = answered[i]["Результат"]
                color = "#4CAF50" if result == "✅ Верно" else "#F44336"
            else:
                color = "#333333"
            progress_html += f'<div style="width: 20px; height: 20px; background-color: {color}; margin: 2px; display: inline-block;"></div>'
        st.markdown(progress_html, unsafe_allow_html=True)

    render_html_progress()
    mode_label = "Основной тест" if st.session_state.mode == "full_test" else "Повтор ошибок"
    st.markdown(f"**Режим:** {mode_label} — Вопрос {st.session_state.step + 1} из {total_questions}")

    if st.session_state.step < total_questions:
        row = df.iloc[st.session_state.step]
        st.markdown(f"**{row['Вопрос']}**")

        options = ['A', 'B', 'C', 'D', 'E', 'F']
        valid_options = [(opt, str(row.get(opt))) for opt in options if pd.notna(row.get(opt))]
        correct_answer = str(row['Правильный ответ']).strip().upper()

        selected = st.radio(
            "Выберите ответ:",
            [f"{opt}) {text}" for opt, text in valid_options],
            key=f"q_{st.session_state.mode}_{st.session_state.step}"
        )

        if not st.session_state.show_result:
            if st.button("Ответить"):
                st.session_state.selected_option = selected[0]
                is_correct = st.session_state.selected_option == correct_answer
                st.session_state.last_result = is_correct

                st.session_state.answers.append({
                    "Режим": "Основной" if st.session_state.mode == "full_test" else "Повтор ошибок",
                    "Индекс": row.name,
                    "Вопрос": row["Вопрос"],
                    "Вы выбрали": st.session_state.selected_option,
                    "Правильный ответ": correct_answer,
                    "Результат": "✅ Верно" if is_correct else "❌ Неверно"
                })

                if is_correct:
                    st.session_state.score += 1

                st.session_state.show_result = True
                st.rerun()

        else:
            if st.session_state.last_result:
                st.success("✅ Верно!")
            else:
                st.error(f"❌ Неверно. Правильный ответ: {correct_answer}")

            if st.button("Следующий вопрос"):
                st.session_state.step += 1
                st.session_state.selected_option = None
                st.session_state.last_result = None
                st.session_state.show_result = False
                st.rerun()

    if st.session_state.step >= total_questions and not st.session_state.finished:
        st.session_state.finished = True
        st.success(f"✅ Этап завершён! Правильных ответов: {st.session_state.score} из {total_questions}")

        wrong_df = pd.DataFrame(st.session_state.answers)
        wrong_df = wrong_df[wrong_df["Результат"] != "✅ Верно"]
        wrong_indices = wrong_df["Индекс"].tolist()
        retry_df = df_full.loc[wrong_indices]

        if len(retry_df) > 0:
            st.warning(f"⚠️ Остались ошибки: {len(retry_df)}. Повторить только их?")

            st.download_button(
                "⬇️ Скачать ошибки (CSV)",
                data=retry_df.to_csv(index=False).encode("utf-8"),
                file_name="ошибки_для_повтора.csv",
                mime="text/csv"
            )

            if st.session_state.step >= len(retry_df):
                st.session_state.step = 0  # защита

            if st.button("🔁 Повторить ошибки"):
                st.session_state.mode = "retry_wrong"
                st.session_state.step = 0
                st.session_state.score = 0
                st.session_state.show_result = False
                st.session_state.finished = False
                st.session_state.answers = []
                st.session_state.current_df = retry_df.reset_index(drop=True)
                st.rerun()
        else:
            st.balloons()
            st.success("🎉 Все вопросы пройдены правильно!")

    # 📊 История ответов
    if st.session_state.answers:
        df_result = pd.DataFrame(st.session_state.answers)
        with st.expander("📋 История ответов"):
            st.dataframe(df_result[["Режим", "Вопрос", "Вы выбрали", "Правильный ответ", "Результат"]])

        with st.expander("📈 Статистика"):
            stat = df_result.groupby("Режим")["Результат"].value_counts().unstack(fill_value=0)
            st.write(stat)
else:
    st.info("👆 Загрузите Excel-файл с вопросами.")
