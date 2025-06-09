import streamlit as st
import pandas as pd
import random

st.set_page_config(page_title="Тест по вопросам", layout="centered")

st.title("📘 Веб-приложение для тестирования")
st.write("Выберите файл с вопросами или используйте один из предустановленных.")

# --- Функция загрузки Excel-файла ---
@st.cache_data
def load_questions(file):
    df = pd.read_excel(file, sheet_name="Sheet1")
    df = df.dropna(subset=["Вопрос", "Правильный ответ"])
    return df

# --- Загрузка файла пользователем ---
uploaded_file = st.file_uploader("Загрузите Excel-файл с вопросами", type=["xlsx"])

# Или использование встроенного набора
default_files = {
    "Соп+общ.xlsx": "/mnt/data/Соп+общ.xlsx",
    "Тер+общ.xlsx": "/mnt/data/Тер+общ.xlsx",
}
default_choice = st.selectbox("Или выберите предустановленный файл:", list(default_files.keys()))
data_file = uploaded_file if uploaded_file else default_files[default_choice]

# Загрузка данных
questions_df = load_questions(data_file)

# Отображение таблицы
with st.expander("🔍 Просмотр загруженной таблицы"):
    st.dataframe(questions_df)

# --- Состояние теста ---
if "step" not in st.session_state:
    st.session_state.step = 0
    st.session_state.score = 0
    st.session_state.answers = []

# Начать тест
if st.button("🔁 Начать заново"):
    st.session_state.step = 0
    st.session_state.score = 0
    st.session_state.answers = []
    st.experimental_rerun()

# --- Тестирование ---
if st.session_state.step < len(questions_df):
    row = questions_df.iloc[st.session_state.step]
    st.markdown(f"### Вопрос {st.session_state.step + 1}: {row['Вопрос']}")

    options = ['A', 'B', 'C', 'D', 'E', 'F']
    valid_options = [(opt, str(row[opt])) for opt in options if pd.notna(row.get(opt))]
    correct_answer = row['Правильный ответ'].strip().upper()

    answer = st.radio("Выберите ответ:", [f"{opt}) {text}" for opt, text in valid_options], key=st.session_state.step)

    if st.button("Ответить"):
        selected = answer[0]
        is_correct = selected == correct_answer
        st.session_state.answers.append({
            "question": row["Вопрос"],
            "selected": selected,
            "correct": correct_answer,
            "result": "✅ Верно" if is_correct else "❌ Неверно"
        })
        if is_correct:
            st.session_state.score += 1
        st.session_state.step += 1
        st.experimental_rerun()
else:
    # Завершение
    st.success(f"Вы завершили тест! Результат: {st.session_state.score} из {len(questions_df)}")

    with st.expander("📊 Подробный результат"):
        st.table(pd.DataFrame(st.session_state.answers))
