import streamlit as st
import pandas as pd

st.set_page_config(page_title="Тест по вопросам", layout="centered")
st.title("📘 Веб-приложение для тестирования")
st.write("Загрузите Excel-файл с вопросами:")

# Загрузка файла пользователем
uploaded_file = st.file_uploader("Файл Excel", type=["xlsx"])

# Состояние приложения
if "step" not in st.session_state:
    st.session_state.step = 0
    st.session_state.score = 0
    st.session_state.answers = []
    st.session_state.quiz_finished = False

# Чтение данных
if uploaded_file:
    try:
        df = pd.read_excel(uploaded_file, sheet_name="Sheet1")
        df = df.dropna(subset=["Вопрос", "Правильный ответ"])
    except Exception as e:
        st.error(f"Ошибка при чтении файла: {e}")
        st.stop()

    with st.expander("🔍 Просмотр таблицы"):
        st.dataframe(df)

    if st.button("🔁 Начать заново"):
        st.session_state.step = 0
        st.session_state.score = 0
        st.session_state.answers = []
        st.session_state.quiz_finished = False

    if st.session_state.step < len(df):
        row = df.iloc[st.session_state.step]
        st.markdown(f"### Вопрос {st.session_state.step + 1} из {len(df)}")
        st.markdown(f"**{row['Вопрос']}**")

        options = ['A', 'B', 'C', 'D', 'E', 'F']
        valid_options = [(opt, str(row[opt])) for opt in options if pd.notna(row.get(opt))]
        correct_answer = str(row['Правильный ответ']).strip().upper()

        # Ответ пользователя
        answer = st.radio("Выберите ответ:", [f"{opt}) {text}" for opt, text in valid_options], key=st.session_state.step)

        if st.button("Ответить"):
            if answer:
                selected = answer[0]
                is_correct = selected == correct_answer
                st.session_state.answers.append({
                    "Вопрос": row["Вопрос"],
                    "Вы выбрали": selected,
                    "Правильный ответ": correct_answer,
                    "Результат": "✅ Верно" if is_correct else "❌ Неверно"
                })
                if is_correct:
                    st.session_state.score += 1
                st.session_state.step += 1
            else:
                st.warning("Пожалуйста, выберите вариант ответа перед подтверждением.")

    # Конец теста
    if st.session_state.step >= len(df) and not st.session_state.quiz_finished:
        st.session_state.quiz_finished = True
        st.success(f"🎉 Тест завершён! Результат: {st.session_state.score} из {len(df)}")

    if st.session_state.quiz_finished:
        with st.expander("📊 Подробный результат"):
            st.table(pd.DataFrame(st.session_state.answers))

else:
    st.info("👆 Пожалуйста, загрузите файл Excel с вопросами.")
