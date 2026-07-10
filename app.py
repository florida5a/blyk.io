import streamlit as st

# Настройка вкладки браузера
st.set_page_config(page_title="Blyk.io — ИИ-проверка справок", page_icon="👁️", layout="centered")

# Главный заголовок
st.title("👁️ Blyk.io")
st.subheader("ИИ-рентген для медицинских справок")
st.write("Привет! Это прототип системы проверки медицинских документов на подлинность.")

st.divider() # Красивая линия-разделитель

# Кнопка загрузки файла
uploaded_file = st.file_uploader(
    "Загрузите скан или фото справки (форма 095/у, 086/у и др.)", 
    type=["jpg", "jpeg", "png"]
)

# Что происходит, когда пользователь загрузил файл
if uploaded_file is not None:
    # Показываем картинку на экране
    st.image(uploaded_file, caption="Загруженная справка", use_container_width=True)
    
    # Анимация загрузки
    with st.spinner("Blyk анализирует документ..."):
        st.info("Тут скоро будет магия ИИ! Мы извлечем текст и проверим логику дат.")
        st.success("Сканирование завершено (пока это демо-режим).")
