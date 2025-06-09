import streamlit as st
import pandas as pd
from io import StringIO

st.set_page_config(page_title="Тест с повтором ошибок", layout="centered")
st.title("🧠 Тестирование с ручным переходом")

# 🔄 Кнопка сброса состояния
st.markdown("### 🔄 Управление")
if st.button("🔁 Начать заново"):
    for key in list(st.session_state.keys()):
        del st.session_state[key]
    st.rerun()

# 🧠 Инициализация состояния
defaults = {
    "mode": "full_test",
    "step": 0,
    "score": 0,
    "answers": [],
    "finished": False,
    "show_result": False,
    "selected_option": None,
    "last_result": None,
    "current_df": None,
    "df_full": None
}
for key, val in defaults.items():
    if key not in st.session_state:
        st.session_state[key] = val

# 📂 Загрузка файлов
uploaded_xlsx = st.file_uploader("Загрузите Excel-файл с вопросами", type=["xlsx"])
uploaded_csv = st.file_uploader("🔄 Загрузите CSV с ошибками (необязательно)", type=["csv"])

# Загрузка Excel
if uploaded_xlsx:
    try:
        df_full = pd.read_excel(uploaded_xlsx, sheet_name=0)
        df_full = df_full.dropna(subset=["Вопрос", "Правильный ответ"])
        st.session_state.df_full = df_full.copy()
    except Exception as e:
        st.error(f"Ошибка при чтении Excel-файла: {e}")
        st.stop()

# Обработка CSV с ошибками
if uploaded_csv and st.session_state.df_full is not None:
    try:
        csv_df = pd.read_csv(uploaded_csv)
        # Фильтруем только ошибки
        csv_df = csv_df[csv_df["Результат"] == "❌ Неверно"]

        # Соединяем по тексту вопроса
        df_full = st.session_state.df_full
        matched = df_full[df_full["Вопрос"].isin(csv_df["Вопрос"])]
        st.session_state.current_df = matched.reset_index(drop=True)

        # Сброс состояния для новой сессии по ошибкам
        st.session_state.mode = "retry_from_csv"
        st.session_state.step = 0
        st.session_state.score = 0
        st.session_state.answers = []
        st.session_state.finished = False
        st.session_state.show_result = False

        st.success("✅ Загружен CSV с ошибками. Начинаем тест по ним.")
    except Exception as e:
        st.error(f"Ошибка при обработке CSV: {e}")
        st.stop()

# Если Excel загружен, но нет CSV или не найдено соответствий
if st.session_state.current_df is None and st.session_state.df_full is not None:
    st.session_state.current_df = st.session_state.df_full.copy()

df = st.session_state.current_df
if df is not None:
    total_questions = len(df)
    current_step = st.session_state.step

    correct_count = sum(1 for a in st.session_state.answers if a["Результат"] == "✅ Верно")
    wrong_count = sum(1 for a in st.session_state.answers if a["Результат"] == "❌ Неверно")

    # 🔳 HTML прогрессбар (18 клеток)
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

    if current_step < total_questions:
        row = df.iloc[current_step]
        st.markdown(f"**Прогресс:** Вопрос {current_step + 1} из {total_questions}")
        st.markdown(html_bar, unsafe_allow_html=True)
        st.markdown(f"✅ Правильно: {correct_count} | ❌ Неправильно: {wrong_count} | ⬛ Осталось: {total_questions - (correct_count + wrong_count)}")

        st.markdown(f"### Вопрос {current_step + 1}")
        st.markdown(f"**{row['Вопрос']}**")

        options = ['A', 'B', 'C', 'D', 'E', 'F']
        valid_options = [(opt, str(row.get(opt))) for opt in options if pd.notna(row.get(opt))]
        correct_answer = str(row['Правильный ответ']).strip().upper()

        selected = st.radio(
            "Выберите ответ:",
            [f"{opt}) {text}" for opt, text in valid_options],
            key=f"q_{st.session_state.mode}_{current_step}"
        )

        if not st.session_state.show_result:
            if st.button("Ответить"):
                selected_letter = selected[0]
                is_correct = selected_letter == correct_answer

                st.session_state.selected_option = selected_letter
                st.session_state.last_result = is_correct
                st.session_state.answers.append({
                    "Режим": "Основной" if st.session_state.mode == "full_test" else "Повтор ошибок",
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
                st.markdown("✅ **Верно!**", unsafe_allow_html=True)
            else:
                st.markdown(f"❌ **Неверно. Правильный ответ: {correct_answer}**", unsafe_allow_html=True)

    elif not st.session_state.finished:
        st.session_state.finished = True
        st.success(f"🎉 Этап завершён! Правильных ответов: {st.session_state.score} из {total_questions}")

        # Предлагаем повторить ошибки
        wrong_df = pd.DataFrame(st.session_state.answers)
        wrong_df = wrong_df[wrong_df["Результат"] != "✅ Верно"]
        wrong_indices = wrong_df["Индекс"].tolist()
        retry_df = st.session_state.df_full.loc[wrong_indices] if st.session_state.df_full is not None else None

        if retry_df is not None and len(retry_df) > 0:
            st.warning(f"⚠️ Остались ошибки: {len(retry_df)}. Повторить только их?")
            if st.button("🔁 Повторить ошибки"):
                st.session_state.mode = "retry_wrong"
                st.session_state.step = 0
                st.session_state.score = 0
                st.session_state.answers = []
                st.session_state.finished = False
                st.session_state.show_result = False
                st.session_state.current_df = retry_df.reset_index(drop=True)
                st.rerun()
        else:
            st.balloons()
            st.success("✅ Все вопросы пройдены правильно!")

        # Кнопка для скачивания CSV с ошибками
        if not wrong_df.empty:
            csv = wrong_df.to_csv(index=False).encode("utf-8-sig")
            st.download_button("⬇️ Скачать ошибки (CSV)", data=csv, file_name="ошибки.csv", mime="text/csv")

# Показываем историю ответов
if st.session_state.answers:
    with st.expander("📋 История ответов"):
        df_result = pd.DataFrame(st.session_state.answers)
        st.dataframe(df_result[["Режим", "Вопрос", "Вы выбрали", "Правильный ответ", "Результат"]])
