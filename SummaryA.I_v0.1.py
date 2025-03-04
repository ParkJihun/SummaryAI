import os
import streamlit as st
import azure.cognitiveservices.speech as speechsdk
import openai
import ffmpeg
from datetime import datetime
from pydub import AudioSegment

# Streamlit UI
st.title("📢 음성 파일 텍스트 변환 및 요약기")

# 📌 FFmpeg 자동 설치 (Streamlit Cloud 환경)
if not os.path.exists("ffmpeg"):
    os.system("apt-get install ffmpeg -y")

# 📌 FFmpeg 실행 경로 설정
AudioSegment.converter = "ffmpeg"

# 📌 Azure Speech to Text API 설정
speech_key = "116aa0968d984023b92eaae4d952c0a6"
service_region = "koreacentral"

# 📌 파일 업로드
uploaded_file = st.file_uploader("🎵 음성 파일을 업로드하세요", type=["m4a", "wav"])
if uploaded_file is not None:
    input_audio_path = f"temp_{datetime.now().strftime('%Y%m%d_%H%M%S')}.wav"
    
    # 📌 업로드한 파일을 FFmpeg로 변환 (16kHz PCM WAV)
    converted_audio_path = "converted_audio.wav"
    
    with open(input_audio_path, "wb") as f:
        f.write(uploaded_file.getbuffer())
    
    st.write("🎵 음성 파일을 16kHz WAV로 변환 중...")
    
    try:
        audio = AudioSegment.from_file(input_audio_path)
        audio = audio.set_frame_rate(16000).set_channels(1).set_sample_width(2)  # 16kHz, 모노, 16bit PCM
        audio.export(converted_audio_path, format="wav")
        st.success("✅ 변환 완료!")
    except Exception as e:
        st.error(f"오디오 변환 실패: {e}")
        st.stop()

    # 📌 Azure Speech-to-Text 처리
    st.write("🎙️ 음성 인식 중...")
    
    # Azure 설정
    speech_config = speechsdk.SpeechConfig(subscription=speech_key, region=service_region)
    speech_config.speech_recognition_language = "ko-KR"
    audio_config = speechsdk.audio.AudioConfig(filename=converted_audio_path)
    speech_recognizer = speechsdk.SpeechRecognizer(speech_config, audio_config)

    results = []
    def handle_final_result(evt):
        if evt.result.reason == speechsdk.ResultReason.RecognizedSpeech:
            results.append(evt.result.text)

    speech_recognizer.recognized.connect(handle_final_result)
    speech_recognizer.start_continuous_recognition()

    import time
    time.sleep(10)  # 인식이 끝날 때까지 대기
    speech_recognizer.stop_continuous_recognition()

    # 📌 인식된 텍스트 표시
    full_text = " ".join(results)
    st.subheader("📝 변환된 텍스트")
    st.write(full_text)

    # 📌 ChatGPT 요약
    openai.api_key = "YOUR_OPENAI_API_KEY"
    
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

    # 📌 요약된 텍스트 다운로드
    summary_file_path = "summary.txt"
    with open(summary_file_path, "w", encoding="utf-8") as f:
        f.write(summarized_text)

    st.download_button("⬇️ 요약된 텍스트 다운로드", open(summary_file_path, "rb"), file_name="summary.txt")
