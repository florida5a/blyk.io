import streamlit as st
import requests
import base64
import re
from PIL import Image, ImageDraw
import io

# Настройка страницы (Широкий экран, скрываем сайдбары)
st.set_page_config(page_title="Blyk.io | ИИ-проверка", page_icon="👁️", layout="wide", initial_sidebar_state="collapsed")

# Премиальный CSS 
st.markdown("""
    <style>
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
    .block-container { padding-top: 3rem !important; max-width: 1200px; }
    .blyk-title {
        font-family: 'Inter', -apple-system, sans-serif;
        font-size: 4rem;
        font-weight: 900;
        background: linear-gradient(135deg, #00f2fe 0%, #4facfe 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        text-align: center; margin-bottom: 0; padding-bottom: 0; letter-spacing: -1px;
    }
    .blyk-subtitle {
        font-family: 'Inter', -apple-system, sans-serif;
        font-size: 1.2rem; color: #8892b0; text-align: center; margin-top: -10px; margin-bottom: 3rem; font-weight: 400;
    }
    .stButton>button {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white !important; border: none; border-radius: 12px; padding: 0.8rem 2rem; font-size: 1.1rem; font-weight: 600; width: 100%; transition: all 0.3s ease; box-shadow: 0 4px 15px rgba(118, 75, 162, 0.4);
    }
    .stButton>button:hover { transform: translateY(-2px); box-shadow: 0 8px 25px rgba(118, 75, 162, 0.7); border: none; }
    img { border-radius: 16px; box-shadow: 0 10px 30px rgba(0,0,0,0.3); border: 1px solid rgba(255,255,255,0.05); }
    .stAlert { border-radius: 12px !important; border: none !important; }
    </style>
""", unsafe_allow_html=True)

# Шапка
st.markdown('<div class="blyk-title">👁️ Blyk.io</div>', unsafe_allow_html=True)
st.markdown('<div class="blyk-subtitle">AI-рентген для проверки медицинских документов</div>', unsafe_allow_html=True)

# Зона загрузки
uploaded_file = st.file_uploader("Перетащите скан или фото справки сюда", type=["jpg", "jpeg", "png"])

if uploaded_file is not None:
    st.markdown("<br>", unsafe_allow_html=True)
    
    col1, col2 = st.columns([4.5, 5.5], gap="large")
    
    # Левая колонка: Фото и умная цензура
    with col1:
        # Открываем изображение через PIL
        image = Image.open(uploaded_file).convert("RGB")
        
        st.markdown("##### 🛡️ Защита данных (PII)")
        censor_toggle = st.checkbox("Включить авто-цензуру ФИО", value=True)
        
        if censor_toggle:
            # Ползунок для выбора зоны скрытия
            censor_range = st.slider("Настройте черную полосу (зона скрытия сверху-вниз в %)", 0, 100, (20, 35))
            
            # Рисуем черный прямоугольник на копии изображения
            draw = ImageDraw.Draw(image)
            w, h = image.size
            y0 = int(h * (censor_range[0] / 100))
            y1 = int(h * (censor_range[1] / 100))
            draw.rectangle([0, y0, w, y1], fill="black")
            st.caption("Отрегулируйте ползунок так, чтобы черная полоса закрыла ФИО пациента.")
            
        st.image(image, use_container_width=True)
        
    # Правая колонка: Анализ и результаты
    with col2:
        if "OPENROUTER_API_KEY" not in st.secrets:
            st.error("Системное уведомление: Добавьте API-ключ в настройки Secrets.")
        else:
            api_key = st.secrets["OPENROUTER_API_KEY"]
            
            st.markdown("### ⚡ Запуск верификации")
            st.write("ИИ проверит ГОСТ-реквизиты и логику документа (ФИО пациента не передаются на сервер).")
            st.markdown("<br>", unsafe_allow_html=True)
            
            if st.button("🚀 Анализировать документ"):
                with st.spinner("Blyk распознает печати и реквизиты..."):
                    try:
                        # Конвертируем цензурированное изображение обратно в base64 для ИИ
                        buffered = io.BytesIO()
                        image.save(buffered, format="JPEG")
                        base64_image = base64.b64encode(buffered.getvalue()).decode('utf-8')
                        mime_type = "image/jpeg"
                        
                        prompt = """
                        Ты — строгий автоматический алгоритм-верификатор медицинских справок РФ.
                        Твоя задача — оценить подлинность документа по визуальным признакам и извлечь юридические данные.
                        
                        КРИТИЧЕСКОЕ ПРАВИЛО: Если слово нечитаемо или скрыто черным цензурным блоком — пиши "[Скрыто]". Не придумывай слова!
                        
                        ОБЯЗАТЕЛЬНО: Первая строка твоего ответа должна быть СТРОГО "НАДЕЖНОСТЬ: X", где X — число от 0 до 100.
                        
                        Далее выведи строгий технический отчет:
                        1. 📋 Наличие реквизитов: (Перечисли найденные печати. По ГОСТу должны быть: прямоугольный штамп учреждения, треугольная печать, круглая печать врача).
                        2. 🏢 Юридический статус клиники: (Внимательно изучи печати. Найди ИНН или название. Если нашел, сформируй ссылку: [Проверить контрагента](https://www.rusprofile.ru/search?query=НАЗВАНИЕ_ИЛИ_ИНН)).
                        3. 📅 Анализ дат: (Есть ли логические ошибки? Совпадает ли дата выдачи с периодом болезни?).
                        4. 👁️ Визуальные аномалии: (Есть ли следы монтажа, разный цвет чернил).
                        5. ⚖️ Вердикт: (Краткий вывод).
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
                                    
                                    # Визуализация шкалы
                                    if score >= 80:
                                        st.success(f"✅ **Уровень доверия: {score}%** (Документ выглядит подлинным)")
                                    elif score >= 50:
                                        st.warning(f"⚠️ **Уровень доверия: {score}%** (Требуется ручная проверка)")
                                    else:
                                        st.error(f"🚨 **Уровень доверия: {score}%** (Высокий риск подделки!)")
                                        
                                    st.progress(score / 100)
                                    
                                    # Вывод красивого текста
                                    st.markdown(clean_text)
                                    
                                    # КНОПКА КОПИРОВАНИЯ В ОДИН КЛИК
                                    st.markdown("<br>", unsafe_allow_html=True)
                                    with st.expander("📋 Скопировать отчет в один клик"):
                                        st.code(clean_text, language="markdown")
                                        
                                else:
                                    st.markdown(ai_text)
                            else:
                                st.error("Получен пустой ответ от серверов нейросети.")
                        else:
                            st.error(f"Ошибка API: {response.status_code}")
                            
                    except Exception as e:
                        st.error(f"Внутренняя ошибка: {e}")
                        
