from sentence_transformers import SentenceTransformer
import chromadb
import os

# Initialize ChromaDB in a persistent directory
# This ensures memories survive restart
DB_PATH = os.path.join(os.getcwd(), "memory_db")
client = chromadb.PersistentClient(path=DB_PATH)

# Get or create the collection
collection = client.get_or_create_collection(name="jarvis_memory")

# Load embedding model (lightweight, runs on CPU/GPU)
# We load it lazily or globally. Global is fine for now.
print("🧠 Loading memory embedding model...")
embedder = SentenceTransformer("nomic-ai/nomic-embed-text-v1", trust_remote_code=True)
print("✅ Memory model loaded")

def store_memory(text):
    """
    Stores a fact or preference in long-term memory.
    Args:
        text (str): The information to remember (e.g., "The user lives in London").
    """
    try:
        # Generate embedding
        embedding = embedder.encode(text).tolist()
        
        # Simple ID generation (hash of text)
        mem_id = str(hash(text))
        
        collection.add(
            documents=[text],
            embeddings=[embedding],
            ids=[mem_id],
            metadatas=[{"timestamp": str(os.path.getmtime("."))}] # Dummy metadata
        )
        print(f"💾 Memory stored: {text}")
        return True
    except Exception as e:
        print(f"❌ Memory Error (store): {e}")
        return False

def retrieve_memory(query):
    """
    Retrieves relevant memories based on a query.
    Args:
        query (str): The search query (e.g., "Where does the user live?").
    """
    try:
        embedding = embedder.encode(query).tolist()
        
        results = collection.query(
            query_embeddings=[embedding],
            n_results=3  # Get top 3 most relevant memories
        )
        
        memories = results["documents"][0]
        if not memories:
            return "No relevant memories found."
            
        print(f"🔍 Memory retrieved: {memories}")
        return "\n".join(f"- {mem}" for mem in memories)
    except Exception as e:
        print(f"❌ Memory Error (retrieve): {e}")
        return "Error accessing memory."
