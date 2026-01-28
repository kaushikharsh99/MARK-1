import sys

# Handling X11/Headless environments gracefully
try:
    import pyautogui
    # Fail-safe to prevent mouse from taking over if things go wrong
    pyautogui.FAILSAFE = True
    GUI_AVAILABLE = True
except Exception as e:
    print(f"⚠️ GUI Input tools disabled (Headless/No X11): {e}")
    pyautogui = None
    GUI_AVAILABLE = False

def type_text(text):
    """
    Types text using the keyboard.
    Args:
        text (str): The text to type.
    """
    if not GUI_AVAILABLE:
        print(f"❌ Tool Error: GUI unavailable (cannot type '{text}')")
        return False
        
    try:
        print(f"⌨️ Typing: {text}")
        pyautogui.write(text, interval=0.01)
        return True
    except Exception as e:
        print(f"❌ Tool Error (type_text): {e}")
        return False

def press_key(key):
    """
    Presses a single key.
    Args:
        key (str): The key to press (e.g., 'enter', 'esc', 'space').
    """
    if not GUI_AVAILABLE:
        print(f"❌ Tool Error: GUI unavailable (cannot press '{key}')")
        return False

    try:
        print(f"⌨️ Pressing key: {key}")
        pyautogui.press(key)
        return True
    except Exception as e:
        print(f"❌ Tool Error (press_key): {e}")
        return False

def hotkey(keys):
    """
    Presses a combination of keys.
    Args:
        keys (list): List of keys to press together (e.g., ['ctrl', 'c']).
    """
    if not GUI_AVAILABLE:
        print(f"❌ Tool Error: GUI unavailable (cannot hotkey '{keys}')")
        return False

    try:
        print(f"⌨️ Hotkey: {keys}")
        pyautogui.hotkey(*keys)
        return True
    except Exception as e:
        print(f"❌ Tool Error (hotkey): {e}")
        return False