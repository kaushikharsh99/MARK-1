import pvporcupine
from pvrecorder import PvRecorder
import os
import subprocess
import whisper
import numpy as np
import soundfile as sf
import tempfile
import time
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Get your AccessKey from .env
ACCESS_KEY = os.getenv("PICOVOICE_ACCESS_KEY")

if not ACCESS_KEY:
    print("Error: PICOVOICE_ACCESS_KEY not found in .env file.")
    exit(1)

# Initialize Whisper model
print("Loading Whisper model...")
model = whisper.load_model("base")
print("Whisper model loaded.")

def speak(text):
    model_path = "voices/ryan-med/en_US-ryan-medium.onnx"
    # Ensure the model file exists
    if not os.path.exists(model_path):
        print(f"Error: Piper model not found at {model_path}")
        return

    try:
        # Echo text into piper and play audio using aplayer (or similar)
        # Using the downloaded piper executable
        piper_exe = "./piper_bin/piper/piper"
        if not os.path.exists(piper_exe):
             print(f"Error: Piper executable not found at {piper_exe}")
             return

        cmd = f'echo "{text}" | {piper_exe} --model {model_path} --output_raw | aplay -r 22050 -f S16_LE -t raw -'
        subprocess.run(cmd, shell=True, check=True)
    except subprocess.CalledProcessError as e:
        print(f"Error running piper: {e}")
    except Exception as e:
        print(f"An error occurred: {e}")

def listen_for_command(recorder, duration_sec=5):
    print("Listening for command...")
    frames = []
    
    # Calculate number of frames to read
    # recorder.frame_length is usually 512
    # recorder.sample_rate is usually 16000
    num_frames = int((recorder.sample_rate / recorder.frame_length) * duration_sec)
    
    for _ in range(num_frames):
        pcm = recorder.read()
        frames.extend(pcm)
        
    print("Processing command...")
    
    # Save to temp wav file
    with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as f:
        temp_wav_path = f.name
        
    # Convert to numpy array and save
    audio_data = np.array(frames, dtype=np.int16)
    sf.write(temp_wav_path, audio_data, recorder.sample_rate)
    
    # Transcribe
    result = model.transcribe(temp_wav_path)
    text = result["text"].strip()
    
    print(f"User said: {text}")
    
    # Cleanup
    os.remove(temp_wav_path)
    return text

def main():
    keyword_path = 'Jarvis_en_linux_v4_0_0.ppn'
    
    if not os.path.exists(keyword_path):
        # Check for .pnn as well just in case of a typo
        if os.path.exists('jarvis.pnn'):
            keyword_path = 'jarvis.pnn'
        else:
            print(f"Error: Custom model file '{keyword_path}' not found in the current directory.")
            print("Please ensure you have placed your Porcupine model file here.")
            return

    try:
        # Initialize Porcupine with the custom keyword file
        porcupine = pvporcupine.create(
            access_key=ACCESS_KEY,
            keyword_paths=[keyword_path]
        )

        recorder = PvRecorder(device_index=-1, frame_length=porcupine.frame_length)
        recorder.start()

        print(f"Using device: {recorder.selected_device}")
        print("Listening for 'Jarvis'...")

        while True:
            pcm = recorder.read()
            keyword_index = porcupine.process(pcm)

            if keyword_index >= 0:
                print("yes boss")
                speak("Yes Boss")
                
                # Listen for command immediately after
                command_text = listen_for_command(recorder)
                if command_text:
                    print(f"Command detected: {command_text}")
                    # Here you can add logic to handle the command
                else:
                    print("No speech detected.")

    except pvporcupine.PorcupineInvalidArgumentError as e:
        print(f"Invalid AccessKey or parameters: {e}")
    except KeyboardInterrupt:
        print("\nStopping...")
    finally:
        if 'porcupine' in locals():
            porcupine.delete()
        if 'recorder' in locals():
            recorder.stop()
            recorder.delete()

if __name__ == "__main__":
    main()