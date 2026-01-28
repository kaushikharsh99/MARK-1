import os
import time
import speech_recognition as sr
from faster_whisper import WhisperModel
import requests
import tempfile
import subprocess
import soundfile as sf
import numpy as np

from wake import wait_for_wake_word, init_wake_word_engine
from audioutils import preprocess_audio   # 👈 YOUR NEW FILE

# ---------------- CONFIG ----------------

SAMPLE_RATE = 16000

OLLAMA_MODEL = "qwen2.5:3b-instruct"
OLLAMA_URL = "http://localhost:11434/api/generate"

SYSTEM_PROMPT = (
    "You are Jarvis. Reply concisely, conversationally, and confidently. "
    "Do not mention being an AI or a program."
)

PIPER_EXE = "./piper_bin/piper/piper"
PIPER_MODEL = "voices/ryan-med/en_US-ryan-medium.onnx"

# ---------------- AUDIO ----------------

def listen_for_command(recognizer, source, timeout=None):
    print("🎙️ Listening for command...", end="\r")
    try:
        audio = recognizer.listen(
            source,
            timeout=timeout,
            phrase_time_limit=None
        )
        print(" " * 40, end="\r")
        return audio
    except sr.WaitTimeoutError:
        print(" " * 40, end="\r")
        raise

# ---------------- STT ----------------

def transcribe(audio_data, model):
    # Convert SpeechRecognition audio to numpy float32
    pcm = np.frombuffer(audio_data.get_raw_data(), dtype=np.int16).astype(np.float32)
    pcm /= 32768.0  # int16 → float32

    # 🔹 APPLY LIGHT PREPROCESSING HERE
    pcm = preprocess_audio(pcm, SAMPLE_RATE)

    # Write temp WAV
    with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as f:
        sf.write(f.name, pcm, SAMPLE_RATE)
        wav_path = f.name

    try:
        # Use faster-whisper with beam search
        segments, info = model.transcribe(
            wav_path,
            beam_size=5,
            vad_filter=False  # IMPORTANT: SpeechRecognition already segmented
        )

        text = " ".join(seg.text for seg in segments).strip()

        # Guard against common hallucinations
        hallucinations = {
            "you", "thank you", "thanks",
            "subtitles by", "amara.org", "mbc"
        }
        if text.lower().strip(".,!?") in hallucinations:
            return ""

        return text

    finally:
        if os.path.exists(wav_path):
            os.remove(wav_path)

# ---------------- LLM ----------------

def ask_llm(text):
    payload = {
        "model": OLLAMA_MODEL,
        "prompt": text,
        "system": SYSTEM_PROMPT,
        "stream": False
    }
    try:
        r = requests.post(OLLAMA_URL, json=payload, timeout=60)
        r.raise_for_status()
        return r.json()["response"].strip()
    except requests.exceptions.RequestException as e:
        print(f"❌ LLM Error: {e}")
        return "I'm having trouble thinking right now."

# ---------------- PIPER ----------------

def speak(text):
    print("🗣️ Jarvis:", text)
    cmd = (
        f'echo "{text}" | {PIPER_EXE} '
        f'--model {PIPER_MODEL} --output_raw | '
        'aplay -r 22050 -f S16_LE -t raw -'
    )
    subprocess.run(cmd, shell=True, check=True)

# ---------------- MAIN LOOP ----------------

def main():
    print("🧠 Loading models...")

    # Load Faster-Whisper ONCE
    try:
        whisper_model = WhisperModel(
            "small.en",
            device="cuda",
            compute_type="float16"
        )
        print("✅ Faster-Whisper loaded on CUDA")
    except Exception:
        print("⚠️ CUDA failed, falling back to CPU")
        whisper_model = WhisperModel(
            "small.en",
            device="cpu",
            compute_type="int8"
        )
        print("✅ Faster-Whisper loaded on CPU")

    # Wake word engine
    try:
        wake_model = init_wake_word_engine()
        print("✅ Wake word engine ready")
    except Exception as e:
        print(f"❌ Wake word init failed: {e}")
        return

    recognizer = sr.Recognizer()

    # ---- SpeechRecognition tuning (IMPORTANT) ----
    recognizer.energy_threshold = 200
    recognizer.dynamic_energy_threshold = True
    recognizer.dynamic_energy_adjustment_damping = 0.15
    recognizer.pause_threshold = 2.0
    recognizer.non_speaking_duration = 0.5

    INACTIVITY_LIMIT = 300  # seconds

    print("🧠 Jarvis main loop started")

    try:
        while True:
            wait_for_wake_word(wake_model)

            print("🟢 Active Chat Mode Enabled")

            with sr.Microphone(sample_rate=SAMPLE_RATE) as source:
                print("🎙️ Calibrating ambient noise...")
                recognizer.adjust_for_ambient_noise(source, duration=2.0)
                print(f"✅ Energy threshold: {recognizer.energy_threshold}")

                last_activity = time.time()

                while True:
                    if time.time() - last_activity > INACTIVITY_LIMIT:
                        print("💤 Inactivity timeout")
                        speak("I am going to sleep now.")
                        break

                    try:
                        audio = listen_for_command(recognizer, source, timeout=5)
                        text = transcribe(audio, whisper_model)

                        if not text:
                            continue

                        print("👤 You:", text)
                        last_activity = time.time()

                        reply = ask_llm(text)
                        speak(reply)

                        last_activity = time.time()

                    except sr.WaitTimeoutError:
                        continue
                    except Exception as e:
                        print(f"❌ Active loop error: {e}")

    except KeyboardInterrupt:
        print("\nStopping Jarvis...")
    finally:
        wake_model.delete()
        print("🛑 Clean shutdown")

if __name__ == "__main__":
    main()
