import streamlit as st
import pandas as pd
from io import StringIO

st.set_page_config(page_title="Тест с повтором ошибок", layout="centered")
st.title("🧠 Тестирование")

# Кнопка сброса
if st.button("🔁 Начать заново"):
    st.session_state.clear()
    st.rerun()

# Инициализация состояния
defaults = {
    "step": 0,
    "score": 0,
    "answers": [],
    "finished": False,
    "show_result": False,
    "selected_option": None,
    "last_result": None,
    "mode": "full_test",
    "df_full": None,
    "current_df": None,
}
for key, val in defaults.items():
    if key not in st.session_state:
        st.session_state[key] = val

# Загрузка файлов
st.sidebar.header("📂 Загрузка файлов")
xlsx_file = st.sidebar.file_uploader("Загрузите Excel (.xlsx)", type="xlsx")
csv_file = st.sidebar.file_uploader("Загрузите CSV с ошибками (опц.)", type="csv")

# Загружаем Excel
if xlsx_file:
    try:
        df_full = pd.read_excel(xlsx_file)
        df_full = df_full.dropna(subset=["Вопрос", "Правильный ответ"])
        st.session_state.df_full = df_full
        if st.session_state.current_df is None:
            st.session_state.current_df = df_full.copy()
    except Exception as e:
        st.error(f"Ошибка при чтении Excel: {e}")
        st.stop()

# Загружаем CSV с ошибками
if csv_file and st.session_state.df_full is not None:
    try:
        csv_df = pd.read_csv(csv_file)
        csv_df = csv_df[csv_df["Результат"] == "❌ Неверно"]

        retry_questions = csv_df["Вопрос"].tolist()
        matched = st.session_state.df_full[st.session_state.df_full["Вопрос"].isin(retry_questions)].copy()

        if not matched.empty:
            st.session_state.current_df = matched.reset_index(drop=True)
            st.session_state.step = 0
            st.session_state.answers = []
            st.session_state.score = 0
            st.session_state.show_result = False
            st.session_state.finished = False
            st.session_state.mode = "csv_retry"
            st.success("📄 Загружен CSV. Тест будет по ошибочным вопросам.")
            st.rerun()
        else:
            st.warning("Не удалось найти вопросы из CSV в Excel.")
    except Exception as e:
        st.error(f"Ошибка при чтении CSV: {e}")
        st.stop()

df = st.session_state.current_df
if df is not None:
    total = len(df)
    current = st.session_state.step

    # Прогрессбар
    correct = sum(1 for a in st.session_state.answers if a["Результат"] == "✅ Верно")
    wrong = sum(1 for a in st.session_state.answers if a["Результат"] == "❌ Неверно")
    st.markdown(f"**Прогресс:** Вопрос {current+1} из {total}")
    st.markdown(f"✅ Правильно: {correct} | ❌ Неверно: {wrong} | ⬛ Осталось: {total - (correct + wrong)}")

    if current < total:
        row = df.iloc[current]
        st.markdown(f"### {row['Вопрос']}")
        options = ['A', 'B', 'C', 'D', 'E', 'F']
        valid = [(opt, str(row[opt])) for opt in options if pd.notna(row.get(opt))]
        correct_answer = str(row["Правильный ответ"]).strip().upper()

        # Ключ зависит от текущего шага и режима
        radio_key = f"radio_{st.session_state.mode}_{current}"
        selected = st.radio(
            "Выберите вариант:",
            [f"{opt}) {text}" for opt, text in valid],
            key=radio_key,
            index=None
        )

        if not st.session_state.show_result:
            if st.button("Ответить"):
                if selected:
                    selected_letter = selected[0]
                    is_correct = selected_letter == correct_answer

                    st.session_state.answers.append({
                        "Режим": "Повтор по CSV" if st.session_state.mode == "csv_retry" else "Основной",
                        "Индекс": row.name,
                        "Вопрос": row["Вопрос"],
                        "Вы выбрали": selected_letter,
                        "Правильный ответ": correct_answer,
                        "Результат": "✅ Верно" if is_correct else "❌ Неверно"
                    })
                    if is_correct:
                        st.session_state.score += 1
                    st.session_state.last_result = is_correct
                    st.session_state.show_result = True
                    st.session_state.selected_option = selected_letter
                    st.rerun()
        else:
            if st.button("Следующий вопрос"):
                st.session_state.step += 1
                st.session_state.show_result = False
                st.session_state.selected_option = None
                st.session_state.last_result = None
                st.rerun()

            if st.session_state.last_result:
                st.success("✅ Верно!")
            else:
                st.error(f"❌ Неверно. Правильный ответ: {correct_answer}")

    elif not st.session_state.finished:
        st.session_state.finished = True
        st.success(f"Тест завершён! ✅ Правильно: {st.session_state.score} из {total}")

        wrong_df = pd.DataFrame(st.session_state.answers)
        wrong_df = wrong_df[wrong_df["Результат"] != "✅ Верно"]
        if not wrong_df.empty:
            st.warning("Хотите повторить только ошибки?")
            if st.button("🔁 Повторить ошибки"):
                st.session_state.step = 0
                st.session_state.score = 0
                st.session_state.show_result = False
                st.session_state.finished = False
                st.session_state.mode = "retry_wrong"
                st.session_state.current_df = st.session_state.df_full[
                    st.session_state.df_full["Вопрос"].isin(wrong_df["Вопрос"])
                ].reset_index(drop=True)
                st.session_state.answers = []
                st.rerun()

        # Кнопка для скачивания ошибок
        csv = wrong_df.to_csv(index=False).encode("utf-8")
        st.download_button("⬇️ Скачать ошибки в CSV", data=csv, file_name="ошибки.csv", mime="text/csv")

    # История
    if st.session_state.answers:
        with st.expander("📋 История ответов"):
            st.dataframe(pd.DataFrame(st.session_state.answers))
else:
    st.info("👆 Загрузите Excel-файл с вопросами.")
