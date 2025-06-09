import streamlit as st
import pandas as pd

st.set_page_config(page_title="Тест по вопросам", layout="centered")
st.title("📘 Веб-приложение для тестирования")
st.write("Загрузите Excel-файл с вопросами для прохождения теста.")

# Загрузка файла пользователем
uploaded_file = st.file_uploader("📂 Загрузите файл Excel", type=["xlsx"])

# Инициализация состояний
if "step" not in st.session_state:
    st.session_state.step = 0
    st.session_state.score = 0
    st.session_state.answers = []
    st.session_state.quiz_finished = False
    st.session_state.show_result = False
    st.session_state.selected_option = None
    st.session_state.last_result = None

# Если файл загружен
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
        st.session_state.show_result = False
        st.session_state.selected_option = None
        st.session_state.last_result = None

    if st.session_state.step < len(df):
        row = df.iloc[st.session_state.step]
        st.markdown(f"### Вопрос {st.session_state.step + 1} из {len(df)}")
        st.markdown(f"**{row['Вопрос']}**")

        options = ['A', 'B', 'C', 'D', 'E', 'F']
        valid_options = [(opt, str(row[opt])) for opt in options if pd.notna(row.get(opt))]
        correct_answer = str(row['Правильный ответ']).strip().upper()

        # Радиокнопки
        selected = st.radio("Выберите ответ:", [f"{opt}) {text}" for opt, text in valid_options], key=f"q_{st.session_state.step}")

        # Ответить
        if not st.session_state.show_result:
            if st.button("Ответить"):
                st.session_state.selected_option = selected[0]  # Выбор буквы ответа
                is_correct = st.session_state.selected_option == correct_answer
                st.session_state.last_result = is_correct

                st.session_state.answers.append({
                    "Вопрос": row["Вопрос"],
                    "Вы выбрали": st.session_state.selected_option,
                    "Правильный ответ": correct_answer,
                    "Результат": "✅ Верно" if is_correct else "❌ Неверно"
                })

                if is_correct:
                    st.session_state.score += 1

                st.session_state.show_result = True

        # Показ результата
        if st.session_state.show_result:
            if st.session_state.last_result:
                st.success("✅ Верно!")
            else:
                st.error(f"❌ Неверно. Правильный ответ: {correct_answer}")

            if st.button("Следующий вопрос"):
                st.session_state.step += 1
                st.session_state.show_result = False
                st.session_state.selected_option = None

    # Завершение теста
    if st.session_state.step >= len(df) and not st.session_state.quiz_finished:
        st.session_state.quiz_finished = True
        st.success(f"🎉 Тест завершён! Ваш результат: {st.session_state.score} из {len(df)}")

    if st.session_state.quiz_finished:
        with st.expander("📊 Результаты"):
            st.table(pd.DataFrame(st.session_state.answers))

else:
    st.info("👆 Пожалуйста, загрузите Excel-файл для начала теста.")
