"""HW6 configuration shared by the MongoDB and file-memory systems."""

import os
from pathlib import Path

SID4 = 7085
PORT_BASE = 8785
PREFIX = "s7085"
SEED = 7085
VERIFY_SEED = 267085
DOMAIN_ID = 5

MONGO_URI = os.getenv("MONGO_URI", "mongodb://localhost:27017")
MONGO_DB = os.getenv("MONGO_DB", f"{PREFIX}_doc")
OLLAMA_URL = os.getenv("OLLAMA_URL", "http://localhost:11434")
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "llama3.2:3b")
SHORT_TERM_N = int(os.getenv("SHORT_TERM_N", "12"))
SUMMARIZE_EVERY_USER_MSGS = int(os.getenv("SUMMARIZE_EVERY_USER_MSGS", "5"))
EPISODIC_TOP_K = int(os.getenv("EPISODIC_TOP_K", "5"))
REPORT_DIR = Path(__file__).resolve().parent / "reports" / "hw06"
MEMORY_FILE = Path(__file__).resolve().parent / "MEMORY.md"
AGENT_FILE = Path(__file__).resolve().parent / "AGENT.md"
