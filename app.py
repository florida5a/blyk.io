import streamlit as st
import requests
import base64

# Настройка вкладки браузера
st.set_page_config(page_title="Blyk.io — ИИ-проверка справок", page_icon="👁️", layout="centered")

st.title("👁️ Blyk.io")
st.subheader("ИИ-рентген для медицинских справок")
st.write("Привет! Это рабочая система проверки медицинских документов на подлинность.")

st.divider()

uploaded_file = st.file_uploader(
    "Загрузите скан или фото справки (форма 095/у, 086/у и др.)", 
    type=["jpg", "jpeg", "png"]
)

if uploaded_file is not None:
    st.image(uploaded_file, caption="Загруженная справка", use_container_width=True)
    
    if "OPENROUTER_API_KEY" not in st.secrets:
        st.error("Ошибка: Ключ OPENROUTER_API_KEY не найден в настройках Secrets!")
    else:
        api_key = st.secrets["OPENROUTER_API_KEY"]
        
        if st.button("🚀 Запустить ИИ-анализ справки"):
            with st.spinner("Blyk изучает документ через независимый ИИ-модуль..."):
                try:
                    # Кодируем картинку в base64
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
                    
                    # Отправляем запрос на OpenRouter (используем бесплатную Vision-модель)
                    response = requests.post(
                        url="https://openrouter.ai/api/v1/chat/completions",
                        headers={
                            "Authorization": f"Bearer {api_key}",
                            "Content-Type": "application/json"
                        },
                        json={
                            "model": "meta-llama/llama-3.2-11b-vision-instruct:free",
                            "messages": [
                                {
                                    "role": "user",
                                    "content": [
                                        {"type": "text", "text": prompt},
                                        {
                                            "type": "image_url",
                                            "image_url": {
                                                "url": f"data:{mime_type};base64,{base64_image}"
                                            }
                                        }
                                    ]
                                }
                            ]
                        }
                    )
                    
                    if response.status_code == 200:
                        result_json = response.json()
                        ai_text = result_json['choices'][0]['message']['content']
                        st.success("Анализ Blyk.io завершен!")
                        st.markdown(ai_text)
                    else:
                        st.error(f"Ошибка OpenRouter: {response.status_code}")
                        st.write(response.text)
                        
                except Exception as e:
                    st.error(f"Произошла ошибка при обработке: {e}")
