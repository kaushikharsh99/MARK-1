import subprocess

def set_volume(level):
    """
    Sets the system volume to a specific percentage.
    Args:
        level (int): The volume level from 0 to 100.
    """
    try:
        level = max(0, min(100, int(level)))
        # Using pactl for PulseAudio/PipeWire which is standard on most modern Linux
        # Fallback to amixer if needed, but pactl is usually better for 'Master'
        subprocess.run(["pactl", "set-sink-volume", "@DEFAULT_SINK@", f"{level}%"], check=True)
        return True
    except Exception as e:
        print(f"❌ Tool Error (set_volume): {e}")
        return False

def mute_volume():
    """Mutes the system volume."""
    try:
        subprocess.run(["pactl", "set-sink-mute", "@DEFAULT_SINK@", "1"], check=True)
        return True
    except Exception as e:
        print(f"❌ Tool Error (mute_volume): {e}")
        return False

def unmute_volume():
    """Unmutes the system volume."""
    try:
        subprocess.run(["pactl", "set-sink-mute", "@DEFAULT_SINK@", "0"], check=True)
        return True
    except Exception as e:
        print(f"❌ Tool Error (unmute_volume): {e}")
        return False
