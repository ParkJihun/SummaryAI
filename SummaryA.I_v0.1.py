import os
import streamlit as st
import azure.cognitiveservices.speech as speechsdk
import openai
import urllib.request
import zipfile
from datetime import datetime
from pydub import AudioSegment

# Streamlit 기본 설정
st.title("📢 음성 파일 텍스트 변환 및 요약기")
st.write("M4A 또는 WAV 파일을 업로드하세요.")

# 📌 FFmpeg 자동 설치 (클라우드 환경 지원)
if not os.path.exists("ffmpeg"):
    st.write("🔽 FFmpeg 설치 중...")
    os.system("apt-get install ffmpeg -y")
    st.write("✅ FFmpeg 설치 완료!")

# 📌 FFmpeg 실행 경로 설정
AudioSegment.converter = "ffmpeg"

# 📌 Azure Speech to Text API 설정
speech_key = "116aa0968d984023b92eaae4d952c0a6"
service_region = "koreacentral"

# 📌 파일 업로드
uploaded_file = st.file_uploader("🎵 음성 파일을 업로드하세요", type=["m4a", "wav"])
if uploaded_file is not None:
    # 저장 경로 설정
    input_audio_path = f"temp_{datetime.now().strftime('%Y%m%d_%H%M%S')}.wav"

    # 📌 파일 저장
    with open(input_audio_path, "wb") as f:
        f.write(uploaded_file.getbuffer())
    st.success("✅ 파일 업로드 완료!")

    # 📌 Speech to Text 변환
    st.write("🎙️ 음성 인식 중...")
    
    # Azure 설정
    speech_config = speechsdk.SpeechConfig(subscription=speech_key, region=service_region)
    speech_config.speech_recognition_language = "ko-KR"
    audio_config = speechsdk.audio.AudioConfig(filename=input_audio_path)
    speech_recognizer = speechsdk.SpeechRecognizer(speech_config, audio_config)

    results = []
    def handle_final_result(evt):
        if evt.result.reason == speechsdk.ResultReason.RecognizedSpeech:
            results.append(evt.result.text)

    speech_recognizer.recognized.connect(handle_final_result)
    speech_recognizer.start_continuous_recognition()

    # 음성 인식이 완료될 때까지 대기
    import time
    time.sleep(10)  # 충분한 시간 대기

    speech_recognizer.stop_continuous_recognition()

    # 📌 인식된 텍스트 표시
    full_text = " ".join(results)
    st.subheader("📝 변환된 텍스트")
    st.write(full_text)

    # 📌 요약 (ChatGPT 사용)
    openai.api_key = "YOUR_OPENAI_API_KEY"  # OpenAI API 키 설정

    def summarize_text(text):
        response = openai.ChatCompletion.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": "음성 내용을 짧고 간결하게 요약해 주세요."},
                {"role": "user", "content": text}
            ]
        )
        return response["choices"][0]["message"]["content"]

    summarized_text = summarize_text(full_text)
    st.subheader("📌 요약 결과")
    st.write(summarized_text)

    # 📌 요약된 텍스트 파일 다운로드 링크 제공
    summary_file_path = "summary.txt"
    with open(summary_file_path, "w", encoding="utf-8") as f:
        f.write(summarized_text)

    st.download_button("⬇️ 요약된 텍스트 다운로드", open(summary_file_path, "rb"), file_name="summary.txt")
