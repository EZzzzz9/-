import streamlit as st
import pandas as pd

st.set_page_config(page_title="Тест по вопросам", layout="centered")

st.title("📘 Веб-приложение для тестирования")
st.write("Выберите файл с вопросами или используйте один из предустановленных.")

# --- Кэшируем загрузку Excel-файла ---
@st.cache_data
def load_questions(file):
    df = pd.read_excel(file, sheet_name="Sheet1")
    df = df.dropna(subset=["Вопрос", "Правильный ответ"])
    return df

# --- Файлы по умолчанию ---
default_files = {
    "Соп+общ.xlsx": "Соп+общ.xlsx",
    "Тер+общ.xlsx": "Тер+общ.xlsx",
}

# --- Выбор файла ---
uploaded_file = st.file_uploader("Загрузите свой Excel-файл", type=["xlsx"])
selected_default = st.selectbox("Или выберите один из встроенных файлов:", list(default_files.keys()))

# --- Определяем активный источник ---
data_file = uploaded_file if uploaded_file else default_files[selected_default]
questions_df = load_questions(data_file)

# --- Показать таблицу с вопросами ---
with st.expander("🔍 Просмотр загруженной таблицы"):
    st.dataframe(questions_df)

# --- Инициализация состояния ---
if "step" not in st.session_state:
    st.session_state.step = 0
    st.session_state.score = 0
    st.session_state.answers = []
    st.session_state.quiz_finished = False

# --- Кнопка "Начать заново" ---
if st.button("🔁 Начать заново"):
    st.session_state.step = 0
    st.session_state.score = 0
    st.session_state.answers = []
    st.session_state.quiz_finished = False

# --- Вопросы теста ---
if st.session_state.step < len(questions_df):
    row = questions_df.iloc[st.session_state.step]
    st.markdown(f"### Вопрос {st.session_state.step + 1} из {len(questions_df)}")
    st.markdown(f"**{row['Вопрос']}**")

    options = ['A', 'B', 'C', 'D', 'E', 'F']
    valid_options = [(opt, str(row[opt])) for opt in options if pd.notna(row.get(opt))]
    correct_answer = row['Правильный ответ'].strip().upper()

    # Радиокнопки для ответов
    answer = st.radio("Выберите ответ:", [f"{opt}) {text}" for opt, text in valid_options], key=st.session_state.step)

    # Кнопка ответа
    if st.button("Ответить"):
        selected = answer[0]  # Первая буква
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

# --- Итог ---
if st.session_state.step >= len(questions_df) and not st.session_state.quiz_finished:
    st.session_state.quiz_finished = True
    st.success(f"✅ Тест завершён! Ваш результат: {st.session_state.score} из {len(questions_df)}")

# --- Отображение результата ---
if st.session_state.quiz_finished:
    with st.expander("📊 Посмотреть подробные результаты"):
        st.table(pd.DataFrame(st.session_state.answers))
