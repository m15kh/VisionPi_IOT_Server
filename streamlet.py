import streamlit as st
import speech_recognition as sr
import pyttsx3

# 1. ارسال فایل صوتی توسط کاربر
uploaded_file = st.file_uploader("فایل صوتی را آپلود کنید", type=["wav", "mp3"])

if uploaded_file is not None:
    # 2. تبدیل صوت به متن
    recognizer = sr.Recognizer()
    with sr.AudioFile(uploaded_file) as source:
        audio = recognizer.record(source)
    
    try:
        # تبدیل صوت به متن
        text = recognizer.recognize_google(audio, language="fa-IR")
        st.write("متن تبدیل شده:", text)

        # 3. تبدیل متن به صوت و پخش آن
        engine = pyttsx3.init()
        engine.setProperty('rate', 150)  # تنظیم سرعت صحبت
        engine.setProperty('voice', 'farsi')  # انتخاب صدای فارسی
        engine.save_to_file(text, 'output.mp3')  # تبدیل به فایل صوتی
        engine.runAndWait()
        
        st.audio('output.mp3', format="audio/mp3")
    
    except sr.UnknownValueError:
        st.error("متن قابل تشخیص نبود!")
    except sr.RequestError:
        st.error("خطا در درخواست به سرویس تبدیل صوت به متن!")
