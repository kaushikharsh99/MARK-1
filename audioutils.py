# audioutils.py
import numpy as np
from scipy.signal import butter, lfilter

def bandpass_filter(audio, sr):
    # High-pass @ 80 Hz
    b_hp, a_hp = butter(2, 80 / (sr / 2), btype="high")
    audio = lfilter(b_hp, a_hp, audio)

    # Low-pass @ 7500 Hz
    b_lp, a_lp = butter(2, 7500 / (sr / 2), btype="low")
    audio = lfilter(b_lp, a_lp, audio)

    return audio


def normalize(audio, target_rms=0.05):
    rms = np.sqrt(np.mean(audio ** 2))
    if rms > 0:
        audio = audio * (target_rms / rms)
    return audio


def preprocess_audio(audio, sr):
    audio = bandpass_filter(audio, sr)
    audio = normalize(audio)
    return audio
