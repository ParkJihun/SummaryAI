import os
import streamlit as st
from datetime import datetime
import azure.cognitiveservices.speech as speechsdk
import openai
import threading

# Streamlit UI 설정
st.title("교회 설교 STT 및 요약 서비스")

# API Key 입력 (환경변수 활용 권장)
speech_key = "116aa0968d984023b92eaae4d952c0a6"
service_region = "koreacentral"
openai.api_key = "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"

# 오디오 파일 업로드
audio_file = st.file_uploader("오디오 파일을 업로드하세요 (wav 형식)", type=["wav"])

if audio_file:
    temp_audio_path = f"temp_{datetime.now().strftime('%Y%m%d_%H%M%S')}.wav"
    with open(temp_audio_path, "wb") as f:
        f.write(audio_file.read())
    
    st.success("오디오 파일 업로드 완료!")
    
    # STT 결과 저장 디렉토리 설정
    directory = "./stt_results"
    os.makedirs(directory, exist_ok=True)
    full_text_file = os.path.join(directory, f"{datetime.now().strftime('%Y%m%d_%H%M%S')}_Original.txt")

    # Azure STT 설정
    speech_config = speechsdk.SpeechConfig(subscription=speech_key, region=service_region)
    speech_config.speech_recognition_language = "ko-KR"
    audio_config = speechsdk.audio.AudioConfig(filename=temp_audio_path)
    speech_recognizer = speechsdk.SpeechRecognizer(speech_config, audio_config)

    # 종료 이벤트 객체 및 결과 리스트
    done_event = threading.Event()
    results = []
    chunk_size = 5

    def handle_final_result(evt):
        if evt.result.reason == speechsdk.ResultReason.RecognizedSpeech:
            results.append(evt.result.text)
            if len(results) >= chunk_size:
                with open(full_text_file, "a", encoding="utf-8") as file:
                    file.write("\n".join(results) + "\n")
                results.clear()
        elif evt.result.reason == speechsdk.ResultReason.Canceled:
            st.error("음성 인식이 취소되었습니다.")

    def on_session_stopped(evt):
        if results:
            with open(full_text_file, "a", encoding="utf-8") as file:
                file.write("\n".join(results) + "\n")
        speech_recognizer.stop_continuous_recognition_async().get()
        done_event.set()

    # 이벤트 핸들러 등록
    speech_recognizer.recognized.connect(handle_final_result)
    speech_recognizer.session_stopped.connect(on_session_stopped)
    
    # STT 시작 버튼
    if st.button("STT 변환 시작"):
        st.info("음성 변환 중...")
        speech_recognizer.start_continuous_recognition()
        done_event.wait()
        
        # STT 결과 확인
        with open(full_text_file, "r", encoding="utf-8") as file:
            full_text = file.read()
        st.text_area("STT 변환 결과", full_text, height=300)
        
        # 요약 기능
        def summarize_text_segment(segment):
            prompt_message = """아래의 텍스트는 교회 목사님의 말씀입니다.\n 성경말씀을 제외하고, 핵심 내용을 개조식 문장으로 요약해주세요."""
            
            messages = [
                {"role": "system", "content": prompt_message},
                {"role": "user", "content": segment}
            ]
            
            response = openai.ChatCompletion.create(
                model="gpt-4o",
                messages=messages,
                max_tokens=1024,
                temperature=0.5
            )
            
            return response.choices[0].message["content"].strip()
        
        def summarize_text(text, segment_length=3900):
            segments = [text[i:i + segment_length] for i in range(0, len(text), segment_length)]
            summarized_segments = [summarize_text_segment(segment) for segment in segments]
            return "\n".join(summarized_segments)
        
        if st.button("요약 시작"):
            st.info("요약 진행 중...")
            summarized_text = summarize_text(full_text)
            summary_file = os.path.join(directory, f"{datetime.now().strftime('%Y%m%d_%H%M%S')}_Summary.txt")
            with open(summary_file, "w", encoding="utf-8") as file:
                file.write(summarized_text)
            st.text_area("요약 결과", summarized_text, height=300)
            st.success(f"요약 완료! 파일 저장: {summary_file}")
