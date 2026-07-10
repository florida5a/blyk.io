import streamlit as st
import requests
import base64
import re
from PIL import Image, ImageDraw
import io
import cv2
import numpy as np

# 1. Базовая настройка страницы
st.set_page_config(page_title="Blyk.io | ИИ-проверка", page_icon="👁️", layout="wide", initial_sidebar_state="collapsed")

# 2. Логика переключения тем (Светлая / Темная)
if "dark_mode" not in st.session_state:
    st.session_state.dark_mode = True # Темная тема по умолчанию

# Выводим тумблер в правый верхний угол
_, toggle_col = st.columns([8.5, 1.5])
with toggle_col:
    is_dark = st.toggle("🌙 Темный режим", value=st.session_state.dark_mode)
    st.session_state.dark_mode = is_dark

# 3. Цветовые палитры для тем
if st.session_state.dark_mode:
    bg_color = "#0b1120"          # Глубокий темный фон
    card_bg = "#1e293b"           # Фон карточек
    text_main = "#f8fafc"         # Основной текст (белый)
    text_muted = "#94a3b8"        # Второстепенный текст (серый)
    border_color = "rgba(255, 255, 255, 0.1)"
    title_gradient = "linear-gradient(135deg, #38bdf8 0%, #818cf8 100%)"
else:
    bg_color = "#f8fafc"          # Светлый фон
    card_bg = "#ffffff"           # Белые карточки
    text_main = "#0f172a"         # Темный текст
    text_muted = "#64748b"        # Второстепенный текст
    border_color = "rgba(0, 0, 0, 0.1)"
    title_gradient = "linear-gradient(135deg, #0284c7 0%, #4f46e5 100%)"

# 4. Внедрение динамического CSS (f-string позволяет подставлять переменные)
st.markdown(f"""
    <style>
    /* Скрываем элементы управления Streamlit */
    #MainMenu {{visibility: hidden;}}
    footer {{visibility: hidden;}}
    header {{visibility: hidden;}}
    
    /* Главный фон приложения */
    [data-testid="stAppViewContainer"] {{
        background-color: {bg_color};
        transition: background-color 0.4s ease;
    }}
    
    /* Настройка ширины и отступов */
    .block-container {{ 
        padding-top: 1rem !important; 
        max-width: 1200px; 
    }}
    
    /* Премиальный градиентный заголовок */
    .blyk-title {{
        font-family: 'Inter', -apple-system, sans-serif;
        font-size: 4.5rem;
        font-weight: 900;
        background: {title_gradient};
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        text-align: center; 
        margin-bottom: 0; 
        padding-bottom: 0; 
        letter-spacing: -2px;
    }}
    
    /* Подзаголовок */
    .blyk-subtitle {{
        font-family: 'Inter', -apple-system, sans-serif;
        font-size: 1.2rem; 
        color: {text_muted}; 
        text-align: center; 
        margin-top: -10px; 
        margin-bottom: 3rem; 
        font-weight: 400;
    }}
    
    /* Глобальный цвет текста */
    .stMarkdown p, .stMarkdown li {{
        color: {text_main} !important;
    }}
    h1, h2, h3, h4, h5 {{
        color: {text_main} !important;
    }}
    
    /* Стилизация зоны загрузки файлов */
    [data-testid="stFileUploadDropzone"] {{
        background-color: {card_bg};
        border: 2px dashed {border_color};
        border-radius: 16px;
        transition: all 0.3s ease;
    }}
    [data-testid="stFileUploadDropzone"]:hover {{
        border-color: #6366f1;
        background-color: rgba(99, 102, 241, 0.05);
    }}
    
    /* Главная кнопка */
    .stButton>button {{
        background: linear-gradient(135deg, #6366f1 0%, #8b5cf6 100%);
        color: white !important; 
        border: none; 
        border-radius: 12px; 
        padding: 0.8rem 2rem; 
        font-size: 1.1rem; 
        font-weight: 600; 
        width: 100%; 
        transition: all 0.3s ease; 
        box-shadow: 0 4px 15px rgba(99, 102, 241, 0.4);
    }}
    .stButton>button:hover {{ 
        transform: translateY(-2px); 
        box-shadow: 0 8px 25px rgba(99, 102, 241, 0.6); 
    }}
    
    /* Скругление изображений */
    img {{ 
        border-radius: 16px; 
        box-shadow: 0 10px 30px rgba(0,0,0,0.15); 
        border: 1px solid {border_color}; 
    }}
    
    /* Блоки с результатами (Alerts) */
    .stAlert {{ 
        border-radius: 12px !important; 
        border: 1px solid {border_color} !important; 
        background-color: {card_bg} !important;
    }}
    </style>
""", unsafe_allow_html=True)

# 5. Шапка интерфейса
st.markdown('<div class="blyk-title">👁️ Blyk.io</div>', unsafe_allow_html=True)
st.markdown('<div class="blyk-subtitle">Интеллектуальный анализ и верификация медицинских документов</div>', unsafe_allow_html=True)

# 6. Зона загрузки
uploaded_file = st.file_uploader("Перетащите скан или фото справки сюда", type=["jpg", "jpeg", "png"])

if uploaded_file is not None:
    st.markdown("<br>", unsafe_allow_html=True)
    
    # Сетка интерфейса
    col1, col2 = st.columns([4.5, 5.5], gap="large")
    
    # ЛЕВАЯ КОЛОНКА (Документ и цензура)
    with col1:
        image = Image.open(uploaded_file).convert("RGB")
        
        st.markdown("##### 🛡️ Настройки приватности (PII)")
        censor_toggle = st.checkbox("Включить авто-цензуру ФИО пациента", value=True)
        
        if censor_toggle:
            censor_range = st.slider("Отрегулируйте черную полосу (сверху-вниз в %)", 0, 100, (20, 35))
            draw = ImageDraw.Draw(image)
            w, h = image.size
            y0 = int(h * (censor_range[0] / 100))
            y1 = int(h * (censor_range[1] / 100))
            draw.rectangle([0, y0, w, y1], fill="#0f172a") # Глубокий сине-черный цвет цензуры
            st.caption("Данные под полосой не будут отправлены на сервер.")
            
        st.image(image, use_container_width=True)
        
    # ПРАВАЯ КОЛОНКА (Управление ИИ и Отчет)
    with col2:
        if "OPENROUTER_API_KEY" not in st.secrets:
            st.error("Системное уведомление: Добавьте API-ключ в настройки Secrets.")
        else:
            api_key = st.secrets["OPENROUTER_API_KEY"]
            
            st.markdown("### ⚡ Запуск верификации")
            st.write("ИИ проверит ГОСТ-реквизиты, логику, юридический статус и скрытые QR-коды.")
            st.markdown("<br>", unsafe_allow_html=True)
            
            if st.button("🚀 Анализировать документ"):
                with st.spinner("Blyk сканирует документ и ищет QR-коды..."):
                    try:
                        # QR Сканнер (OpenCV)
                        open_cv_image = np.array(image)
                        open_cv_image = open_cv_image[:, :, ::-1].copy()
                        
                        detector = cv2.QRCodeDetector()
                        data, vertices_array, binary_qrcode = detector.detectAndDecode(open_cv_image)
                        
                        if data:
                            qr_status = f"✅ Обнаружен скрытый QR-код! Он ведет на ссылку: {data}"
                        else:
                            qr_status = "⚠️ QR-код на бланке не обнаружен."

                        # Подготовка к отправке
                        buffered = io.BytesIO()
                        image.save(buffered, format="JPEG")
                        base64_image = base64.b64encode(buffered.getvalue()).decode('utf-8')
                        mime_type = "image/jpeg"
                        
                        # Запрос к нейросети
                        prompt = f"""
                        Ты — строгий автоматический алгоритм-верификатор медицинских справок РФ.
                        Твоя задача — оценить подлинность документа по визуальным признакам.
                        
                        ИНФОРМАЦИЯ ОТ QR-СКАНЕРА:
                        {qr_status}
                        
                        КРИТИЧЕСКОЕ ПРАВИЛО: Если слово скрыто цензурой — пиши "[Скрыто]".
                        ОБЯЗАТЕЛЬНО: Первая строка твоего ответа должна быть СТРОГО "НАДЕЖНОСТЬ: X", где X — число от 0 до 100.
                        
                        Отчет:
                        1. 📋 Наличие реквизитов (штампы, печати).
                        2. 🏢 Юридический статус (поиск ИНН/Названия + генерация ссылки на Rusprofile).
                        3. 📅 Анализ дат.
                        4. 👁️ Визуальные аномалии.
                        5. 🔗 QR-анализ.
                        6. ⚖️ Итоговый вердикт.
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
                                    
                                    st.markdown("<br>", unsafe_allow_html=True)
                                    with st.expander("📋 Скопировать отчет (MD)"):
                                        st.code(clean_text, language="markdown")
                                else:
                                    st.markdown(ai_text)
                            else:
                                st.error("Получен пустой ответ от серверов нейросети.")
                        else:
                            st.error(f"Ошибка API: {response.status_code}")
                            
                    except Exception as e:
                        st.error(f"Внутренняя ошибка: {e}")
