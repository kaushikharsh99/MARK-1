import os

def list_files(path="."):
    """
    Lists files in a directory.
    Args:
        path (str): The directory path. Defaults to current directory.
    """
    try:
        # Expand user path (e.g. ~)
        expanded_path = os.path.expanduser(path)
        if not os.path.exists(expanded_path):
            return f"❌ Path not found: {path}"
            
        files = os.listdir(expanded_path)
        # Limit to 50 files to prevent context flooding
        return files[:50]
    except Exception as e:
        return f"❌ Error listing files: {str(e)}"

def read_file(path):
    """
    Reads the content of a file.
    Args:
        path (str): The file path.
    """
    try:
        expanded_path = os.path.expanduser(path)
        if not os.path.exists(expanded_path):
            return f"❌ File not found: {path}"
            
        # Read text only, limit to 2000 chars for safety
        with open(expanded_path, 'r', encoding='utf-8', errors='ignore') as f:
            content = f.read(2000)
            if len(content) == 2000:
                content += "\n... (truncated)"
            return content
    except Exception as e:
        return f"❌ Error reading file: {str(e)}"

