import os
import json
import glob
from rapidfuzz import process, fuzz

# Locations where Linux stores .desktop files
APP_DIRS = [
    "/usr/share/applications",
    "/usr/local/share/applications",
    os.path.expanduser("~/.local/share/applications"),
    "/var/lib/flatpak/exports/share/applications",
    "/snap/bin"  # For snap apps (handled differently, but good to check)
]

REGISTRY_FILE = "apps_registry.json"

def scan_apps():
    """
    Scans system directories for .desktop files and builds a registry.
    Returns: List of app dictionaries.
    """
    apps = []
    seen_names = set()

    print("🔎 Scanning for installed applications...")

    for directory in APP_DIRS:
        if not os.path.exists(directory):
            continue

        # Scan .desktop files
        desktop_files = glob.glob(os.path.join(directory, "*.desktop"))
        
        for filepath in desktop_files:
            try:
                with open(filepath, "r", errors="ignore") as f:
                    name = None
                    exec_cmd = None
                    icon = None
                    no_display = False

                    for line in f:
                        line = line.strip()
                        if line.startswith("Name=") and not name:
                            name = line.split("=", 1)[1]
                        elif line.startswith("Exec=") and not exec_cmd:
                            exec_cmd = line.split("=", 1)[1]
                            # Clean up exec command (remove %u, %F, etc.)
                            exec_cmd = exec_cmd.split("%")[0].strip()
                            exec_cmd = exec_cmd.strip('"')
                        elif line.startswith("NoDisplay=true"):
                            no_display = True
                        elif line.startswith("Icon="):
                            icon = line.split("=", 1)[1]

                    # Filter out hidden/system apps
                    if name and exec_cmd and not no_display:
                        if name.lower() not in seen_names:
                            apps.append({
                                "name": name,
                                "exec": exec_cmd,
                                "icon": icon,
                                "path": filepath
                            })
                            seen_names.add(name.lower())

            except Exception as e:
                print(f"⚠️ Error reading {filepath}: {e}")

    print(f"✅ Found {len(apps)} applications.")
    
    # Save to JSON
    with open(REGISTRY_FILE, "w") as f:
        json.dump(apps, f, indent=2)
    
    return apps

def load_registry():
    """Loads the app registry from JSON, scanning if it doesn't exist."""
    if not os.path.exists(REGISTRY_FILE):
        return scan_apps()
    
    with open(REGISTRY_FILE, "r") as f:
        return json.load(f)

def find_app(query):
    """
    Fuzzy searches for an app in the registry.
    Args:
        query (str): The app name to find (e.g., "code", "browser").
    Returns:
        dict: The best matching app object or None.
    """
    registry = load_registry()
    names = [app["name"] for app in registry]
    
    # Fuzzy match
    match = process.extractOne(query, names, scorer=fuzz.token_set_ratio)
    
    if match:
        name, score, idx = match
        if score > 60:  # Threshold
            return registry[idx]
    
    return None

if __name__ == "__main__":
    # If run directly, force a scan
    scan_apps()
