import webbrowser
from ddgs import DDGS

def open_url(url):
    """
    Opens a URL in the default web browser.
    Args:
        url (str): The URL to open.
    """
    try:
        # Basic validation
        if not url.startswith(('http://', 'https://')):
            url = 'https://' + url
            
        print(f"🌐 Opening URL: {url}")
        webbrowser.open(url)
        return True
    except Exception as e:
        print(f"❌ Error opening URL: {e}")
        return False

def search_web(query):
    """
    Searches the web using DuckDuckGo.
    Args:
        query (str): The search query.
    """
    try:
        print(f"🔍 Searching web for: {query}")
        with DDGS() as ddgs:
            results = list(ddgs.text(query, max_results=3))
            
        if not results:
            return "No results found."
            
        # Format results nicely for the LLM
        formatted = ""
        for i, res in enumerate(results, 1):
            formatted += f"{i}. {res['title']}: {res['body']} ({res['href']})\n"
            
        return formatted.strip()
    except Exception as e:
        return f"❌ Search error: {str(e)}"