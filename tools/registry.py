from tools.apps import open_app
from tools.system import set_volume, mute_volume, unmute_volume
from tools.files import list_files, read_file
from tools.web import open_url, search_web
from tools.system_info import get_time, get_system_status
from tools.input import type_text, press_key, hotkey
from tools.memory import store_memory, retrieve_memory

# Master Registry of all available tools
TOOLS = {
    "open_app": open_app,
    "set_volume": set_volume,
    "mute": mute_volume,
    "unmute": unmute_volume,
    "list_files": list_files,
    "read_file": read_file,
    "open_url": open_url,
    "search_web": search_web,
    "get_time": get_time,
    "system_status": get_system_status,
    "type_text": type_text,
    "press_key": press_key,
    "hotkey": hotkey,
    "store_memory": store_memory,
    "retrieve_memory": retrieve_memory,
}

def execute_tool_safely(name, args):
    """
    Executes a tool and returns a standardized result dict.
    Returns: {'status': 'ok'|'error', 'result': ..., 'error': ...}
    """
    func = TOOLS.get(name)
    if not func:
        return {"status": "error", "error": f"Tool '{name}' not found"}
    
    try:
        # Execute the tool
        result = func(**args)
        
        # Normalize the result for the plan executor
        # Many existing tools return True/False or a string.
        if result is False:
            return {"status": "error", "error": "Tool returned False (failed)"}
        
        return {"status": "ok", "result": result}
        
    except Exception as e:
        return {"status": "error", "error": str(e)}

# Tool Definitions for System Prompt
TOOL_DEFINITIONS = """
Available Tools:

1. open_app(app_name: str)
   - Opens an application.

2. set_volume(level: int) / mute() / unmute()
   - Audio controls.

3. list_files(path: str) / read_file(path: str)
   - File system access.

4. open_url(url: str) / search_web(query: str)
   - Web browser and internet search.

5. get_time() / system_status()
   - System information.

6. type_text(text: str) / press_key(key: str) / hotkey(keys: list)
   - Keyboard simulation.

7. store_memory(text: str)
   - Saves a fact/preference to long-term memory.
   - USE FOR: User names, preferences, specific instructions to remember.

8. retrieve_memory(query: str)
   - Searches long-term memory.
   - USE FOR: Recalling user info when asked.
"""
