import streamlit as st
import requests
import base64

# Настройка вкладки браузера
st.set_page_config(page_title="Blyk.io — ИИ-проверка справок", page_icon="👁️", layout="centered")

# Главный заголовок
st.title("👁️ Blyk.io")
st.subheader("ИИ-рентген для медицинских справок")
st.write("Привет! Это рабочая система проверки медицинских документов на подлинность на базе Google Gemini.")

st.divider()

# Кнопка загрузки файла
uploaded_file = st.file_uploader(
    "Загрузите скан или фото справки (форма 095/у, 086/у и др.)", 
    type=["jpg", "jpeg", "png"]
)

if uploaded_file is not None:
    st.image(uploaded_file, caption="Загруженная справка", use_container_width=True)
    
    # Проверяем, на месте ли наш секретный сейф с ключом
    if "GEMINI_API_KEY" not in st.secrets:
        st.error("Ошибка: Ключ GEMINI_API_KEY не найден в настройках (Secrets) вашего Streamlit!")
    else:
        api_key = st.secrets["GEMINI_API_KEY"]
        
        # Появляется кнопка для запуска анализа
        if st.button("🚀 Запустить ИИ-анализ справки"):
            with st.spinner("Blyk изучает пиксели, текст и логику дат через Gemini..."):
                try:
                    # Кодируем картинку в формат, который понимает нейросеть
                    bytes_data = uploaded_file.getvalue()
                    base64_image = base64.b64encode(bytes_data).decode('utf-8')
                    mime_type = uploaded_file.type
                    
                    # Промпт-инструкция для ИИ
                    prompt = """
                    Ты — опытный эксперт службы безопасности и медицинский юрист. Твоя задача — проанализировать медицинскую справку на картинке на предмет подделки или логических аномалий.
                    
                    Внимательно изучи:
                    1. Логику дат (совпадают ли периоды болезни, даты выдачи справки, нет ли нестыковок вроде "выдана воскресеньем" или задним числом).
                    2. Логику диагнозов и кодов (если есть коды болезней МКБ-10, соответствуют ли они тексту диагноза).
                    3. Структуру документа (все ли обязательные штампы на месте, клиника реальная или вымышленная, если видны реквизиты).
                    4. Визуальные артефакты (если заметен грубый фотомонтаж, разный шрифт цифр в датах, наложение текста поверх печати).
                    
                    Ответь строго на РУССКОМ языке. Структурируй свой ответ красиво по пунктам:
                    - 📋 Краткий вердикт (Насколько документ надежен в процентах от 0% до 100%)
                    - 🔍 Логический анализ текста и дат
                    - 🔬 Визуальный анализ бланка и печатей
                    - ⚠️ Подозрительные моменты (если обнаружены)
                    - 💡 Рекомендация для проверяющего (HR или деканата)
                    """
                    
                    # Запрос к Gemini API
                    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent?key={api_key}"
                    
                    payload = {
                        "contents": [
                            {
                                "parts": [
                                    {"text": prompt},
                                    {
                                        "inlineData": {
                                            "mimeType": mime_type,
                                            "data": base64_image
                                        }
                                    }
                                ]
                            }
                        ]
                    }
                    headers = {"Content-Type": "application/json"}
                    
                    # Отправляем данные
                    response = requests.post(url, json=payload, headers=headers)
                    
                    if response.status_code == 200:
                        result_json = response.json()
                        ai_text = result_json['contents'][0]['parts'][0]['text']
                        st.success("Анализ Blyk.io завершен!")
                        st.markdown(ai_text) # Выводим красивый ответ ИИ
                    else:
                        st.error(f"Ошибка API: {response.status_code}")
                        st.write(response.text)
                        
                except Exception as e:
                    st.error(f"Произошла ошибка при обработке: {e}")
