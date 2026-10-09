"""Run a genuine ten-message Ollama session without requiring MongoDB.

This produces an honest live-model artifact; MongoDB persistence is tested
separately when the MongoDB service is available.
"""

import json
from datetime import datetime, timezone
from pathlib import Path

from hw6_memory import ChatRequest, InMemoryStore, OllamaChatModel, chat_turn

ROOT = Path(__file__).resolve().parent
OUTPUT = ROOT / "reports" / "hw06" / "raw" / "live_ollama_session.json"
MESSAGES = [
    "What domain does this project support?",
    "Which local model is configured?",
    "What database stores HW6 memory?",
    "What is the API port?",
    "Why do we use a short-term window?",
    "What is an episodic fact?",
    "How often are session summaries triggered?",
    "What must the assistant not fabricate?",
    "What are the three memory collections?",
    "Summarize the architecture in one sentence.",
]

def main():
    store = InMemoryStore()
    model = OllamaChatModel()
    turns = []
    for index, message in enumerate(MESSAGES, 1):
        result = chat_turn(ChatRequest(user_id="live-demo", session_id="live-session", message=message), store, model, short_term_n=4, summarize_every=5)
        turns.append({"turn": index, "message": message, "reply": result["reply"], "metrics": result["metrics"]})
        print(f"TURN {index}: {message}\nREPLY: {result['reply']}\nMETRICS: {result['metrics']}\n")
    payload = {"model": model.model, "ollama_url": model.base_url, "started_at_utc": datetime.now(timezone.utc).isoformat(), "turn_count": len(turns), "turns": turns}
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    print(f"Saved {OUTPUT}")

if __name__ == "__main__": main()
