import streamlit as st
import pandas as pd

st.set_page_config(page_title="Тест с повтором ошибок", layout="centered")
st.title("🧠 Тестирование с повтором ошибок")

# 🔄 Сброс состояния
if st.button("🔁 Начать заново"):
    for key in list(st.session_state.keys()):
        del st.session_state[key]
    st.rerun()

# 🧠 Инициализация состояния
defaults = {
    "step": 0,
    "score": 0,
    "answers": [],
    "finished": False,
    "show_result": False,
    "selected_option": None,
    "last_result": None,
    "current_df": None,
    "df_full": None,
}
for key, val in defaults.items():
    if key not in st.session_state:
        st.session_state[key] = val

# 📂 Загрузка файлов
st.subheader("📥 Загрузка данных")
xlsx_file = st.file_uploader("Загрузите Excel-файл с вопросами", type=["xlsx"])
csv_file = st.file_uploader("(Необязательно) Загрузите CSV с ошибками", type=["csv"])

if xlsx_file:
    try:
        df_full = pd.read_excel(xlsx_file, sheet_name=0)
        df_full = df_full.dropna(subset=["Вопрос", "Правильный ответ"])
        st.session_state.df_full = df_full
    except Exception as e:
        st.error(f"Ошибка загрузки Excel: {e}")
        st.stop()

    # 🎯 Обработка CSV-файла
    if csv_file:
        try:
            df_errors = pd.read_csv(csv_file)
            df_errors = df_errors[df_errors["Результат"] == "❌ Неверно"]

            # Фильтрация df_full на основе совпадения по тексту вопроса
            filtered_df = df_full[df_full["Вопрос"].isin(df_errors["Вопрос"])]
            if filtered_df.empty:
                st.warning("⚠️ В CSV-файле нет вопросов, совпадающих с Excel.")
            else:
                st.session_state.current_df = filtered_df.reset_index(drop=True)
                st.info(f"🔁 Загружено {len(filtered_df)} вопросов из CSV с ошибками.")
        except Exception as e:
            st.error(f"Ошибка чтения CSV: {e}")
            st.stop()

    # Если CSV не загружен — работаем со всем набором
    if st.session_state.current_df is None:
        st.session_state.current_df = st.session_state.df_full.copy()

    df = st.session_state.current_df
    total_questions = len(df)
    step = st.session_state.step

    # 📊 Прогрессбар HTML (18 клеток)
    BAR_CELLS = 18
    html_bar = '<div style="display: flex; gap: 2px;">'
    for i in range(BAR_CELLS):
        relative_index = int(i / BAR_CELLS * total_questions)
        if relative_index >= total_questions:
            color = "black"
        else:
            row_index = df.iloc[relative_index].name
            answer = next((a for a in st.session_state.answers if a["Индекс"] == row_index), None)
            if answer:
                color = "green" if answer["Результат"] == "✅ Верно" else "red"
            else:
                color = "black"
        html_bar += f'<div style="width: 20px; height: 20px; background-color: {color}; border: 1px solid #555;"></div>'
    html_bar += '</div>'

    correct_count = sum(1 for a in st.session_state.answers if a["Результат"] == "✅ Верно")
    wrong_count = sum(1 for a in st.session_state.answers if a["Результат"] == "❌ Неверно")

    st.markdown(f"**Прогресс:** Вопрос {step + 1} из {total_questions}")
    st.markdown(html_bar, unsafe_allow_html=True)
    st.markdown(f"✅ Правильно: {correct_count} | ❌ Неверно: {wrong_count} | ⬛ Осталось: {total_questions - (correct_count + wrong_count)}")

    # 🧠 Тестирование
    if step < total_questions:
        row = df.iloc[step]
        st.markdown(f"### Вопрос {step + 1}")
        st.markdown(f"**{row['Вопрос']}**")

        options = ['A', 'B', 'C', 'D', 'E', 'F']
        valid_options = [(opt, str(row.get(opt))) for opt in options if pd.notna(row.get(opt))]
        correct_answer = str(row["Правильный ответ"]).strip().upper()

        selected = st.radio(
            "Выберите ответ:",
            [f"{opt}) {text}" for opt, text in valid_options],
            key=f"q_{step}"
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

    # ✅ Завершение
    if step >= total_questions and not st.session_state.finished:
        st.session_state.finished = True
        st.success(f"✅ Этап завершён! Правильных ответов: {st.session_state.score} из {total_questions}")
        st.balloons()

    # 📋 История
    if st.session_state.answers:
        with st.expander("📄 История ответов"):
            df_result = pd.DataFrame(st.session_state.answers)
            st.dataframe(df_result[["Вопрос", "Вы выбрали", "Правильный ответ", "Результат"]])
else:
    st.info("👆 Загрузите Excel-файл с вопросами.")
