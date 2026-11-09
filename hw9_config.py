"""HW9 configuration derived from the assigned HW8 project."""

SID4 = 7085
PORT_BASE = 8085
HW9_PORT = 8086
PREFIX = "s7085"
SEED = 7085
VERIFY_SEED = 267085
DOMAIN_ID = 5
DOMAIN = "local restaurant inspections"
LOCAL_MODEL = "llama3.2:3b"
EMBEDDING_MODEL = "nomic-embed-text"
EMBEDDING_DIM = 768
OLLAMA_URL = "http://localhost:11434"
REDIS_URL = "redis://localhost:6379/0"
VIEW_KEY = f"{PREFIX}:views:restaurant"
CACHE_KEY = f"{PREFIX}:semantic_cache"
DATA_VERSION_KEY = f"{PREFIX}:data_version:restaurant"
DEFAULT_THRESHOLD = 0.85
