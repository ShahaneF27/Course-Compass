"""Configuration settings for Course Compass."""
import os
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables
# Try to find .env file in project root or backend directory
BASE_DIR = Path(__file__).parent.parent.parent
BACKEND_DIR = BASE_DIR / "backend"

# Try loading .env from project root first, then backend directory
env_paths = [BASE_DIR / ".env", BACKEND_DIR / ".env"]
for env_path in env_paths:
    if env_path.exists():
        load_dotenv(dotenv_path=env_path, override=True)
        print(f"[INFO] Loaded .env from {env_path}")
        break
else:
    # Fallback to default behavior (look in current directory)
    load_dotenv()
    print("[WARNING] Using default .env loading (may not find API keys)")

# Data paths
DATA_RAW_PATH = BACKEND_DIR / os.getenv("DATA_RAW_PATH", "data/raw")
DATA_INDEX_PATH = BACKEND_DIR / os.getenv("DATA_INDEX_PATH", "data/index")
DOCS_JSONL_PATH = DATA_INDEX_PATH / "docs.jsonl"
CHROMA_PATH = DATA_INDEX_PATH / "chroma"

# API Configuration
API_HOST = os.getenv("API_HOST", "0.0.0.0")
API_PORT = int(os.getenv("API_PORT", 8000))

# Embedding Model
EMBEDDING_MODEL = os.getenv("EMBEDDING_MODEL", "all-MiniLM-L6-v2")

# ChromaDB Configuration
COLLECTION_NAME = os.getenv("COLLECTION_NAME", "canvas_chunks")

# Chunking Configuration
CHUNK_SIZE = 1200  # Increased to preserve tables intact
CHUNK_OVERLAP = 200  # Increased overlap for better context

# Retrieval Configuration
TOP_K = 8  # Retrieve top 8 chunks for better context coverage
MAX_SOURCES = 3  # Return max 3 sources to user
LOW_CONFIDENCE_THRESHOLD = 0.25  # Lowered from 0.5 - temporary for testing
MAX_CONTEXT_CHARS = 12000  # Cap context at 12k chars to speed up Gemini responses

# Google Gemini API Configuration
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")
GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-2.0-flash")  # Fast, free model
GEMINI_MAX_TOKENS = int(os.getenv("GEMINI_MAX_TOKENS", 1024))

# Ensure directories exist
DATA_RAW_PATH.mkdir(parents=True, exist_ok=True)
DATA_INDEX_PATH.mkdir(parents=True, exist_ok=True)
CHROMA_PATH.mkdir(parents=True, exist_ok=True)

