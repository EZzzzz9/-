import streamlit as st
import pandas as pd
import time

st.set_page_config(page_title="Тестирование с повтором ошибок", layout="centered")
st.title("🧠 Тестирование с автоповтором ошибок")

# 🔄 Сброс состояния
if st.button("🔁 Начать заново"):
    for key in list(st.session_state.keys()):
        del st.session_state[key]
    st.experimental_rerun()

# 🧠 Инициализация session_state
if "mode" not in st.session_state:
    st.session_state.mode = "full_test"  # full_test / retry_wrong
    st.session_state.step = 0
    st.session_state.score = 0
    st.session_state.answers = []
    st.session_state.finished = False
    st.session_state.show_result = False
    st.session_state.selected_option = None
    st.session_state.last_result = None
    st.session_state.response_time = None
    st.session_state.current_df = None  # df, состоящий из текущего этапа (весь тест или ошибки)

# 📂 Загрузка файла
uploaded_file = st.file_uploader("Загрузите Excel-файл с вопросами", type=["xlsx"])

if uploaded_file:
    try:
        df_full = pd.read_excel(uploaded_file, sheet_name="Sheet1")
        df_full = df_full.dropna(subset=["Вопрос", "Правильный ответ"])
    except Exception as e:
        st.error(f"Ошибка при чтении файла: {e}")
        st.stop()

    with st.expander("🔍 Просмотр загруженных данных"):
        st.dataframe(df_full)

    # 📄 Формируем начальный набор данных
    if st.session_state.current_df is None:
        st.session_state.current_df = df_full.copy()

    df = st.session_state.current_df

    # ❓ Вывод вопроса
    if st.session_state.step < len(df):
        row = df.iloc[st.session_state.step]
        st.markdown(f"### Вопрос {st.session_state.step + 1} из {len(df)}")
        st.markdown(f"**{row['Вопрос']}**")

        options = ['A', 'B', 'C', 'D', 'E', 'F']
        valid_options = [(opt, str(row.get(opt))) for opt in options if pd.notna(row.get(opt))]
        correct_answer = str(row['Правильный ответ']).strip().upper()

        selected = st.radio(
            "Выберите ответ:",
            [f"{opt}) {text}" for opt, text in valid_options],
            key=f"q_{st.session_state.mode}_{st.session_state.step}"
        )

        # 🟢 Ответ
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
                st.session_state.response_time = time.time()

        # ✅ Показ результата и автопереход
        if st.session_state.show_result:
            if st.session_state.last_result:
                st.success("✅ Верно!")
            else:
                st.error(f"❌ Неверно. Правильный ответ: {correct_answer}")

            if time.time() - st.session_state.response_time >= 1:
                st.session_state.step += 1
                st.session_state.show_result = False
                st.session_state.selected_option = None
                st.session_state.response_time = None
                st.experimental_rerun()

    # 🏁 Завершение раунда
    if st.session_state.step >= len(df) and not st.session_state.finished:
        st.session_state.finished = True
        st.success(f"✅ Этап завершён! Правильных ответов: {st.session_state.score} из {len(df)}")

        # Фильтрация неправильных ответов
        wrong_df = pd.DataFrame(st.session_state.answers)
        wrong_df = wrong_df[wrong_df["Результат"] != "✅ Верно"]
        wrong_indices = wrong_df["Индекс"].tolist()
        retry_df = df_full.loc[wrong_indices]

        if len(retry_df) > 0:
            st.warning(f"⚠️ Остались ошибки: {len(retry_df)}. Хотите повторить только их?")

            if st.button("🔁 Повторить ошибки"):
                # Сброс состояния
                st.session_state.mode = "retry_wrong"
                st.session_state.step = 0
                st.session_state.score = 0
                st.session_state.show_result = False
                st.session_state.selected_option = None
                st.session_state.finished = False
                st.session_state.current_df = retry_df.reset_index(drop=True)
                st.experimental_rerun()
        else:
            st.balloons()
            st.success("🎉 Все вопросы пройдены правильно! Повторов не требуется.")

    # 📊 История
    if st.session_state.answers:
        with st.expander("📋 История ответов"):
            df_result = pd.DataFrame(st.session_state.answers)
            st.dataframe(df_result[["Режим", "Вопрос", "Вы выбрали", "Правильный ответ", "Результат"]])
else:
    st.info("👆 Загрузите Excel-файл с вопросами, чтобы начать.")
