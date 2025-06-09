import streamlit as st
import pandas as pd
from io import StringIO

st.set_page_config(page_title="Тест с повтором ошибок", layout="centered")
st.title("🧠 Тестирование с ручным переходом")

# 🔄 Кнопка сброса
st.markdown("### 🔄 Управление")
if st.button("🔁 Начать заново"):
    for key in list(st.session_state.keys()):
        del st.session_state[key]
    st.rerun()

# 🧠 Инициализация
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

# 📂 Загрузка Excel
xlsx_file = st.file_uploader("Загрузите Excel-файл с вопросами", type=["xlsx"])
csv_file = st.file_uploader("🔁 (Опционально) Загрузите CSV с ошибками", type=["csv"])

if xlsx_file:
    try:
        df_full = pd.read_excel(xlsx_file, sheet_name="Sheet1")
        df_full = df_full.dropna(subset=["Вопрос", "Правильный ответ"])
    except Exception as e:
        st.error(f"Ошибка при чтении Excel: {e}")
        st.stop()

    # 🔍 Если есть CSV, фильтруем по ошибкам
    if csv_file:
        try:
            df_csv = pd.read_csv(csv_file)
            wrong_questions = df_csv[df_csv["Результат"] == "❌ Неверно"]["Вопрос"].tolist()
            df_full = df_full[df_full["Вопрос"].isin(wrong_questions)].reset_index(drop=True)
            st.info(f"🔁 Загружено {len(df_full)} вопросов с ошибками из CSV")
        except Exception as e:
            st.error(f"Ошибка при чтении CSV: {e}")
            st.stop()

    # Просмотр
    with st.expander("📄 Просмотр загруженных данных"):
        st.dataframe(df_full)

    if st.session_state.current_df is None:
        st.session_state.current_df = df_full.copy()

    df = st.session_state.current_df
    total_questions = len(df)
    current_step = st.session_state.step

    # Прогресс
    correct_count = sum(1 for a in st.session_state.answers if a["Результат"] == "✅ Верно")
    wrong_count = sum(1 for a in st.session_state.answers if a["Результат"] == "❌ Неверно")
    unanswered = total_questions - (correct_count + wrong_count)

    # 🔳 HTML-прогрессбар (18 клеток)
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

    st.markdown(f"**Прогресс:** Вопрос {current_step + 1} из {total_questions}")
    st.markdown(html_bar, unsafe_allow_html=True)
    st.markdown(f"✅ Правильно: {correct_count} | ❌ Неправильно: {wrong_count} | ⬛ Осталось: {unanswered}")

    if current_step < total_questions:
        row = df.iloc[current_step]
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
                st.markdown("✅ **Верно!**")
            else:
                st.markdown(f"❌ **Неверно. Правильный ответ: {correct_answer}**")

    # ✅ Завершение
    if current_step >= total_questions and not st.session_state.finished:
        st.session_state.finished = True
        st.success(f"🎉 Этап завершён! Правильных ответов: {st.session_state.score} из {total_questions}")

        wrong_df = pd.DataFrame(st.session_state.answers)
        wrong_df = wrong_df[wrong_df["Результат"] != "✅ Верно"]

        if not wrong_df.empty:
            st.warning(f"⚠️ Остались ошибки: {len(wrong_df)}. Повторить только их?")
            if st.button("🔁 Повторить ошибки"):
                st.session_state.mode = "retry_wrong"
                st.session_state.step = 0
                st.session_state.score = 0
                st.session_state.show_result = False
                st.session_state.finished = False
                st.session_state.answers = []
                st.session_state.current_df = df_full[df_full["Вопрос"].isin(wrong_df["Вопрос"])].reset_index(drop=True)
                st.rerun()

            # 💾 Кнопка для скачивания ошибок
            csv_out = wrong_df[["Режим", "Вопрос", "Вы выбрали", "Правильный ответ", "Результат"]]
            csv_str = csv_out.to_csv(index=False)
            st.download_button("💾 Скачать ошибки CSV", data=csv_str, file_name="ошибки.csv", mime="text/csv")
        else:
            st.success("🎉 Все вопросы пройдены правильно!")
            st.balloons()

    if st.session_state.answers:
        with st.expander("📋 История ответов"):
            df_result = pd.DataFrame(st.session_state.answers)
            st.dataframe(df_result[["Режим", "Вопрос", "Вы выбрали", "Правильный ответ", "Результат"]])
else:
    st.info("👆 Загрузите Excel-файл с вопросами.")
