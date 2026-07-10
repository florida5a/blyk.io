import streamlit as st
import requests
import base64
import re

# Настройка страницы (Широкий экран, скрываем сайдбары)
st.set_page_config(page_title="Blyk.io | ИИ-проверка", page_icon="👁️", layout="wide", initial_sidebar_state="collapsed")

# Премиальный CSS (Dribbble-style, адаптирован под темную тему)
st.markdown("""
    <style>
    /* Скрываем дефолтный мусор Streamlit */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
    
    /* Добавляем воздуха сверху */
    .block-container {
        padding-top: 3rem !important;
        max-width: 1200px;
    }
    
    /* Градиентный заголовок по центру */
    .blyk-title {
        font-family: 'Inter', -apple-system, sans-serif;
        font-size: 4rem;
        font-weight: 900;
        background: linear-gradient(135deg, #00f2fe 0%, #4facfe 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        text-align: center;
        margin-bottom: 0;
        padding-bottom: 0;
        letter-spacing: -1px;
    }
    
    /* Аккуратный подзаголовок */
    .blyk-subtitle {
        font-family: 'Inter', -apple-system, sans-serif;
        font-size: 1.2rem;
        color: #8892b0;
        text-align: center;
        margin-top: -10px;
        margin-bottom: 3rem;
        font-weight: 400;
    }
    
    /* Стилизация главной кнопки (Неоновое свечение) */
    .stButton>button {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white !important;
        border: none;
        border-radius: 12px;
        padding: 0.8rem 2rem;
        font-size: 1.1rem;
        font-weight: 600;
        width: 100%;
        transition: all 0.3s ease;
        box-shadow: 0 4px 15px rgba(118, 75, 162, 0.4);
    }
    .stButton>button:hover {
        transform: translateY(-2px);
        box-shadow: 0 8px 25px rgba(118, 75, 162, 0.7);
        border: none;
    }
    
    /* Скругление углов у картинок и легкая тень */
    img {
        border-radius: 16px;
        box-shadow: 0 10px 30px rgba(0,0,0,0.3);
        border: 1px solid rgba(255,255,255,0.05);
    }
    
    /* Кастомные плашки с результатами */
    .stAlert {
        border-radius: 12px !important;
        border: none !important;
    }
    </style>
""", unsafe_allow_html=True)

# Шапка сайта по центру
st.markdown('<div class="blyk-title">👁️ Blyk.io</div>', unsafe_allow_html=True)
st.markdown('<div class="blyk-subtitle">AI-рентген для проверки медицинских документов</div>', unsafe_allow_html=True)

# Зона загрузки
uploaded_file = st.file_uploader("Перетащите скан или фото справки сюда", type=["jpg", "jpeg", "png"])

if uploaded_file is not None:
    st.markdown("<br>", unsafe_allow_html=True) # Отступ
    
    # Разделяем на 2 колонки: 45% фото, 55% интерфейс анализа
    col1, col2 = st.columns([4.5, 5.5], gap="large")
    
    with col1:
        st.image(uploaded_file, use_container_width=True)
        
    with col2:
        if "OPENROUTER_API_KEY" not in st.secrets:
            st.error("Системное уведомление: Добавьте API-ключ в настройки Secrets.")
        else:
            api_key = st.secrets["OPENROUTER_API_KEY"]
            
            st.markdown("### ⚡ Запуск верификации")
            st.write("Строгий автоматический алгоритм-верификатор проверит документ по стандартам ГОСТ.")
            st.markdown("<br>", unsafe_allow_html=True)
            
            if st.button("🚀 Анализировать документ"):
                with st.spinner("Blyk ищет обязательные реквизиты..."):
                    try:
                        bytes_data = uploaded_file.getvalue()
                        base64_image = base64.b64encode(bytes_data).decode('utf-8')
                        mime_type = uploaded_file.type
                        
                        prompt = """
                        Ты — строгий автоматический алгоритм-верификатор медицинских справок РФ (форма 095/у, 086/у).
                        Твоя задача — жестко оценить подлинность документа ТОЛЬКО по визуальным признакам и стандартам ГОСТ.
                        
                        КРИТИЧЕСКОЕ ПРАВИЛО: Почерк врачей сложен. Если ты не можешь точно прочитать слово на 100%, КАТЕГОРИЧЕСКИ ЗАПРЕЩАЕТСЯ придумывать несуществующие слова, иероглифы или бессмысленные наборы букв. Просто пиши: "[Неразборчиво]".
                        
                        Обязательные элементы ГОСТ для справки (проверь их наличие на фото):
                        1. Прямоугольный штамп медицинского учреждения (обычно вверху слева).
                        2. Треугольная печать (для больничных листов/справок).
                        3. Круглая личная печать лечащего врача.
                        4. Подпись врача.
                        5. Четкие даты выдачи и периоды освобождения от занятий/работы.
                        
                        ОБЯЗАТЕЛЬНО: Первая строка твоего ответа должна быть СТРОГО "НАДЕЖНОСТЬ: X", где X — число от 0 до 100.
                        
                        Далее выведи строгий технический отчет:
                        1. 📋 Наличие реквизитов: (Перечисли, какие из 3 обязательных печатей и штампов найдены, а каких не хватает).
                        2. 📅 Анализ дат: (Есть ли логические ошибки? Совпадает ли дата выдачи с периодом болезни?).
                        3. 👁️ Визуальные аномалии: (Есть ли следы монтажа, разный цвет чернил, наложение текста поверх печатей).
                        4. ⚖️ Вердикт: (Краткий вывод для HR/Деканата, почему выставлен такой процент надежности).
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
