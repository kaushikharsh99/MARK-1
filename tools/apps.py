import subprocess
import shlex
from tools.app_scanner import find_app, scan_apps

def open_app(app_name):
    """
    Opens an application by name.
    Uses fuzzy matching against a system-wide app registry.
    Args:
        app_name (str): The name of the application to open (e.g., 'firefox', 'calculator').
    """
    try:
        print(f"🔍 Resolving app: '{app_name}'...")
        
        # 1. Try to find the app in the registry
        app_info = find_app(app_name)
        
        if app_info:
            exec_cmd = app_info['exec']
            print(f"✅ Found match: {app_info['name']} -> {exec_cmd}")
            subprocess.Popen(shlex.split(exec_cmd), start_new_session=True)
            return True
            
        # 2. Fallback: Try running exactly as provided (e.g. valid terminal commands)
        print(f"⚠️ No registry match. Trying direct execution: '{app_name}'")
        subprocess.Popen(shlex.split(app_name), start_new_session=True)
        return True

    except FileNotFoundError:
        print(f"❌ Tool Error: App '{app_name}' not found.")
        return False
    except Exception as e:
        print(f"❌ Tool Error: {e}")
        return False

# Function to manually refresh the registry
def refresh_app_registry():
    scan_apps()
    return "App registry refreshed."