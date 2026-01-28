import os
from dotenv import load_dotenv
import pvporcupine
from pvrecorder import PvRecorder
import subprocess

# LOAD ENV VARIABLES
load_dotenv()

ACCESS_KEY = os.getenv("PICOVOICE_ACCESS_KEY")

if not ACCESS_KEY:
    raise RuntimeError("PICOVOICE_ACCESS_KEY not found in environment")

KEYWORD_PATH = "Jarvis_en_linux_v4_0_0.ppn"

PIPER_EXE = "./piper_bin/piper/piper"
PIPER_MODEL = "voices/ryan-med/en_US-ryan-medium.onnx"


def speak_yes_boss():
    cmd = (
        f'echo "Yes boss" | {PIPER_EXE} '
        f'--model {PIPER_MODEL} --output_raw | '
        'aplay -r 22050 -f S16_LE -t raw -'
    )
    subprocess.run(cmd, shell=True, check=True)


def init_wake_word_engine():
    """Initializes and returns the Porcupine wake word engine."""
    return pvporcupine.create(
        access_key=ACCESS_KEY,
        keyword_paths=[KEYWORD_PATH]
    )


def wait_for_wake_word(porcupine_instance=None):
    """
    Waits for the wake word.
    Args:
        porcupine_instance: An optional pre-initialized Porcupine instance. 
                            If None, a new one is created and destroyed.
    """
    should_delete = False
    if porcupine_instance is None:
        porcupine = pvporcupine.create(
            access_key=ACCESS_KEY,
            keyword_paths=[KEYWORD_PATH]
        )
        should_delete = True
    else:
        porcupine = porcupine_instance

    recorder = PvRecorder(
        device_index=-1,
        frame_length=porcupine.frame_length
    )
    recorder.start()

    # print(f"Using device: {recorder.selected_device}") # Optional: reduce verbosity if loop is tight
    print("🟢 Listening for 'Jarvis'...")

    try:
        while True:
            pcm = recorder.read()
            if porcupine.process(pcm) >= 0:
                print("🟢 Wake word detected")
                speak_yes_boss()
                return
    finally:
        recorder.stop()
        recorder.delete()
        if should_delete:
            porcupine.delete()