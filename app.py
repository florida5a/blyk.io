import streamlit as st
import requests
import base64
import re

# 1. Настройка страницы (Широкий экран, скрываем сайдбары по умолчанию)
st.set_page_config(page_title="Blyk.io | ИИ-проверка", page_icon="👁️", layout="wide", initial_sidebar_state="collapsed")

# 2. Инъекция современного CSS-дизайна
st.markdown("""
    <style>
    /* Скрываем дефолтные элементы Streamlit */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
    
    /* Настройка главного контейнера (добавляем воздуха) */
    .block-container {
        padding-top: 2rem;
        max-width: 1200px;
    }
    
    /* Стилизация заголовков */
    .blyk-title {
        font-family: 'Inter', sans-serif;
        font-size: 3rem;
        font-weight: 900;
        color: #0f172a;
        margin-bottom: 0px;
        padding-bottom: 0px;
    }
    .blyk-subtitle {
        font-family: 'Inter', sans-serif;
        font-size: 1.1rem;
        color: #64748b;
        margin-top: -10px;
        margin-bottom: 30px;
    }
    
    /* Стилизация главной кнопки */
    .stButton>button {
        background: linear-gradient(135deg, #2563eb 0%, #4f46e5 100%);
        color: white;
        border: none;
        border-radius: 10px;
        padding: 0.75rem 2rem;
        font-size: 1.1rem;
        font-weight: 600;
        width: 100%;
        transition: transform 0.2s, box-shadow 0.2s;
    }
    .stButton>button:hover {
        transform: translateY(-2px);
        box-shadow: 0 10px 20px -10px rgba(37, 99, 235, 0.5);
        color: white;
        border: none;
    }
    
    /* Скругление углов у загруженных изображений */
    img {
        border-radius: 12px;
        border: 1px solid #e2e8f0;
    }
    </style>
""", unsafe_allow_html=True)

# 3. Шапка сайта
st.markdown('<div class="blyk-title">👁️ Blyk.io</div>', unsafe_allow_html=True)
st.markdown('<div class="blyk-subtitle">Анализ медицинских документов на базе ИИ</div>', unsafe_allow_html=True)

# 4. Основной интерфейс
uploaded_file = st.file_uploader("Перетащите скан или фото справки сюда", type=["jpg", "jpeg", "png"])

if uploaded_file is not None:
    # Разделяем на 2 колонки: 40% фото, 60% интерфейс анализа
    col1, col2 = st.columns([4, 6], gap="large")
    
    with col1:
        st.image(uploaded_file, caption="Исходный файл", use_container_width=True)
        
    with col2:
        if "OPENROUTER_API_KEY" not in st.secrets:
            st.error("Системное уведомление: Добавьте API-ключ в настройки Secrets.")
        else:
            api_key = st.secrets["OPENROUTER_API_KEY"]
            
            st.markdown("### Запуск верификации")
            st.write("Нейросеть проверит логику дат, диагнозы, штампы и выявит возможные визуальные артефакты.")
            
            if st.button("🚀 Анализировать документ"):
                with st.spinner("Идет сканирование..."):
                    try:
                        bytes_data = uploaded_file.getvalue()
                        base64_image = base64.b64encode(bytes_data).decode('utf-8')
                        mime_type = uploaded_file.type
                        
                        prompt = """
                        Ты — эксперт службы безопасности. Проанализируй медицинскую справку.
                        
                        ОБЯЗАТЕЛЬНО: Первая строка твоего ответа должна быть СТРОГО в формате "НАДЕЖНОСТЬ: X", где X — число от 0 до 100. Никаких других слов в первой строке!
                        
                        Далее со следующей строки распиши анализ:
                        1. 🔍 Логика текста и дат.
                        2. 🔬 Визуальный анализ бланка.
                        3. ⚠️ Подозрительные моменты.
                        4. 💡 Рекомендация.
                        """
                        
                        response = requests.post(
                            url="https://openrouter.ai/api/v1/chat/completions",
                            headers={
                                "Authorization": f"Bearer {api_key}",
                                "Content-Type": "application/json"
                            },
                            json={
                                "model": "openrouter/free",
                                "messages": [
                                    {
                                        "role": "user",
                                        "content": [
                                            {"type": "text", "text": prompt},
                                            {"type": "image_url", "image_url": {"url": f"data:{mime_type};base64,{base64_image}"}}
                                        ]
                                    }
                                ]
                            }
                        )
                        
                        if response.status_code == 200:
                            result_json = response.json()
                            if 'choices' in result_json and len(result_json['choices']) > 0:
                                ai_text = result_json['choices'][0]['message']['content']
                                match = re.search(r'НАДЕЖНОСТЬ:\s*(\d+)', ai_text, re.IGNORECASE)
                                
                                st.divider()
                                
                                if match:
                                    score = int(match.group(1))
                                    clean_text = re.sub(r'НАДЕЖНОСТЬ:.*\n', '', ai_text, flags=re.IGNORECASE).strip()
                                    
                                    if score >= 80:
                                        st.success(f"✅ **Уровень доверия: {score}%** (Документ выглядит подлинным)")
                                    elif score >= 50:
                                        st.warning(f"⚠️ **Уровень доверия: {score}%** (Требуется ручная проверка)")
                                    else:
                                        st.error(f"🚨 **Уровень доверия: {score}%** (Высокий риск подделки!)")
                                        
                                    st.progress(score / 100)
                                    st.markdown(clean_text)
                                else:
                                    st.markdown(ai_text)
                            else:
                                st.error("Получен пустой ответ от серверов нейросети.")
                        else:
                            st.error(f"Ошибка API: {response.status_code}")
                            
                    except Exception as e:
                        st.error(f"Внутренняя ошибка: {e}")
