import streamlit as st
import requests
import base64
import re

# Настройка страницы (теперь ШИРОКИЙ экран для красивой верстки)
st.set_page_config(page_title="Blyk.io — ИИ-рентген справок", page_icon="👁️", layout="wide")

# Легкий кастомный дизайн заголовков
st.markdown("""
    <style>
    .main-header { font-size: 2.5rem; font-weight: 800; color: #1E3A8A; margin-bottom: -10px;}
    .sub-header { font-size: 1.2rem; color: #6B7280; margin-bottom: 20px;}
    </style>
""", unsafe_allow_html=True)

st.markdown('<div class="main-header">👁️ Blyk.io</div>', unsafe_allow_html=True)
st.markdown('<div class="sub-header">Умная система проверки медицинских документов</div>', unsafe_allow_html=True)
st.divider()

uploaded_file = st.file_uploader("Загрузите скан или фото справки (jpg, png)", type=["jpg", "jpeg", "png"])

if uploaded_file is not None:
    # ДЕЛИМ ЭКРАН НА ДВЕ КОЛОНКИ: 1 часть под фото, 1.5 части под текст
    col1, col2 = st.columns([1, 1.5])
    
    with col1:
        st.image(uploaded_file, caption="Исходный документ", use_container_width=True)
        
    with col2:
        if "OPENROUTER_API_KEY" not in st.secrets:
            st.error("Ошибка: Ключ OPENROUTER_API_KEY не найден в настройках Secrets!")
        else:
            api_key = st.secrets["OPENROUTER_API_KEY"]
            
            # Кнопка на всю ширину колонки
            if st.button("🚀 Запустить глубокий ИИ-анализ", use_container_width=True):
                with st.spinner("Blyk сканирует пиксели, печати и логику диагнозов..."):
                    try:
                        bytes_data = uploaded_file.getvalue()
                        base64_image = base64.b64encode(bytes_data).decode('utf-8')
                        mime_type = uploaded_file.type
                        
                        # УМНЫЙ ПРОМПТ: заставляем ИИ отдавать данные для парсинга
                        prompt = """
                        Ты — эксперт службы безопасности. Проанализируй медицинскую справку.
                        
                        ОБЯЗАТЕЛЬНО: Первая строка твоего ответа должна быть СТРОГО в формате "НАДЕЖНОСТЬ: X", где X — число от 0 до 100. Никаких других слов в первой строке!
                        
                        Далее со следующей строки распиши анализ:
                        1. 🔍 Логика текста и дат (есть ли нестыковки).
                        2. 🔬 Визуальный анализ бланка (печати, шрифты, следы фотошопа).
                        3. ⚠️ Подозрительные моменты.
                        4. 💡 Итоговая рекомендация.
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
                                            {
                                                "type": "image_url",
                                                "image_url": {"url": f"data:{mime_type};base64,{base64_image}"}
                                            }
                                        ]
                                    }
                                ]
                            }
                        )
                        
                        if response.status_code == 200:
                            result_json = response.json()
                            if 'choices' in result_json and len(result_json['choices']) > 0:
                                ai_text = result_json['choices'][0]['message']['content']
                                
                                # УМНАЯ ЛОГИКА: Пытаемся найти цифру оценки в ответе ИИ
                                match = re.search(r'НАДЕЖНОСТЬ:\s*(\d+)', ai_text, re.IGNORECASE)
                                
                                if match:
                                    score = int(match.group(1))
                                    # Убираем первую строку с цифрой из текста, чтобы не дублировать
                                    clean_text = re.sub(r'НАДЕЖНОСТЬ:.*\n', '', ai_text, flags=re.IGNORECASE).strip()
                                    
                                    st.subheader("Результат проверки")
                                    # Рисуем цветные шкалы в зависимости от оценки
                                    if score >= 80:
                                        st.success(f"✅ Индекс доверия: {score}% (Документ выглядит подлинным)")
                                        st.progress(score / 100)
                                    elif score >= 50:
                                        st.warning(f"⚠️ Индекс доверия: {score}% (Требует ручной проверки)")
                                        st.progress(score / 100)
                                    else:
                                        st.error(f"🚨 Индекс доверия: {score}% (Высокий риск подделки!)")
                                        st.progress(score / 100)
                                        
                                    st.markdown(clean_text)
                                else:
                                    # Если ИИ вдруг забыл написать цифру, выводим просто текст
                                    st.markdown(ai_text)
                            else:
                                st.error("Ответ от модели пришел пустым.")
                        else:
                            st.error(f"Ошибка сервера: {response.status_code}")
                            
                    except Exception as e:
                        st.error(f"Системная ошибка: {e}")
