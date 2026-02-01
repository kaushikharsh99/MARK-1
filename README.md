# J.A.R.V.I.S. (MARK-1)

**Just A Rather Very Intelligent System**

A locally hosted, voice-activated AI assistant for Linux, inspired by the Marvel Universe. J.A.R.V.I.S. is designed to be a calm, precise, and witty system intelligence that manages your computer, retrieves information, and assists with daily tasks.

## 🚀 Features

*   **Voice Activation:** Wake up J.A.R.V.I.S. with the hotword "Jarvis" (powered by Picovoice Porcupine).
*   **Speech Recognition:** High-accuracy local transcription using `faster-whisper`.
*   **Intelligence:** Powered by local LLMs via **Ollama** (default: `qwen2.5:3b-instruct`).
*   **Voice Output:** Fast, natural-sounding TTS using **Piper**.
*   **Personality Engine:** Dynamic emotion system (Neutral, Confident, Annoyed, Curious) that adapts to success/failure and user tone.
*   **Tools & Capabilities:**
    *   📂 **File System:** Read, write, list, and search files.
    *   🧠 **Memory:** Long-term memory storage and retrieval (ChromaDB).
    *   🌐 **Web:** Search the internet.
    *   👁️ **Vision:** Screen analysis and OCR capabilities.
    *   ⚙️ **System:** Monitor CPU/Battery, launch apps, and control system volume.
*   **Privacy First:** Designed to run locally.

## 🛠️ Prerequisites

1.  **Python 3.11+**
2.  **Ollama:** Installed and running.
    *   Pull the model: `ollama pull qwen2.5:3b-instruct`
3.  **Piper TTS:** The binary is expected in `./piper_bin/piper/piper`.
4.  **Picovoice Access Key:** Get a free key from the [Picovoice Console](https://console.picovoice.ai/).

## 📦 Installation

1.  **Clone the repository:**
    ```bash
    git clone https://github.com/kaushikharsh99/MARK-1.git
    cd MARK-1
    ```

2.  **Install Python Dependencies:**
    ```bash
    pip install -r requirements.txt
    # If requirements.txt is missing, manually install:
    pip install pvporcupine pvrecorder SpeechRecognition faster-whisper requests soundfile numpy python-dotenv chromadb mss pyautogui
    ```

3.  **Environment Setup:**
    Create a `.env` file in the root directory:
    ```env
    PORCUPINE_ACCESS_KEY=your_picovoice_access_key_here
    ```

4.  **Piper Setup:**
    Ensure the Piper TTS executable and voice model (`en_GB-alan-medium.onnx`) are correctly placed in the `piper_bin` and `voices` directories respectively.

## 🖥️ Usage

Run the main script:

```bash
python main.py
```

*   **Voice Mode:** Say "Jarvis" to wake him up.
*   **Text Mode:** Press `Enter` in the console to type commands silently.

## 📂 Project Structure

*   `main.py`: The core event loop (Wake -> Listen -> Think -> Act -> Speak).
*   `wake.py`: Hotword detection logic.
*   `tools/`: Directory containing all capability modules (Files, Web, Vision, etc.).
*   `memory_db/`: Local storage for long-term memory.
*   `voices/`: ONNX models for TTS.

## 🤝 Contributing

Feel free to open issues or submit pull requests to improve J.A.R.V.I.S.

## 📜 License

[MIT License](LICENSE)
