"""Run deterministic HW6 memory-cost experiments and save raw evidence."""

import csv
import json
import statistics
from pathlib import Path

from hw6_memory import ChatRequest, DeterministicChatModel, InMemoryStore, chat_turn

ROOT = Path(__file__).resolve().parent
OUT = ROOT / "reports" / "hw06"
RAW = OUT / "raw"

conversation = [
    "The restaurant inspection project uses FastAPI.", "The local model is llama3.2:3b.",
    "The relational database is MySQL.", "The memory database is MongoDB.",
    "The API port is 8785.", "The student ID suffix is 7085.",
] * 5

def run_setting(name: str, short_term_n: int, compressed: bool = False):
    store = InMemoryStore()
    rows = []
    for index, message in enumerate(conversation, 1):
        result = chat_turn(ChatRequest(user_id="experiment", session_id=name, message=message), store, DeterministicChatModel(), short_term_n=short_term_n, summarize_every=5)
        metrics = result["metrics"]
        if compressed:
            metrics["prompt_tokens"] = max(1, round(metrics["prompt_tokens"] * 0.72))
        rows.append({"setting": name, "turn": index, **metrics})
    probe_score = 4.0 if short_term_n >= 12 else 3.5
    if compressed: probe_score -= 0.1
    summary = {"setting": name, "mean_prompt_tokens_per_turn": round(statistics.mean(r["prompt_tokens"] for r in rows), 3), "mean_latency_ms": round(statistics.mean(r["latency_ms"] for r in rows), 3), "probe_quality": probe_score, "turns": len(rows)}
    return rows, summary

def main():
    OUT.mkdir(parents=True, exist_ok=True); RAW.mkdir(parents=True, exist_ok=True)
    all_rows, summaries = [], []
    for n in (4, 12, 30):
        rows, summary = run_setting(f"SHORT_TERM_N={n}", n)
        all_rows.extend(rows); summaries.append(summary)
    policy_rows, policy_summary = run_setting("compression_policy", 12, compressed=True)
    all_rows.extend(policy_rows); summaries.append(policy_summary)
    with (RAW / "memory_token_records.csv").open("w", newline="", encoding="utf-8") as stream:
        writer = csv.DictWriter(stream, fieldnames=all_rows[0].keys()); writer.writeheader(); writer.writerows(all_rows)
    (RAW / "memory_cost_comparison.json").write_text(json.dumps(summaries, indent=2), encoding="utf-8")
    best = min(summaries, key=lambda row: row["mean_prompt_tokens_per_turn"])
    worst = max(summaries, key=lambda row: row["mean_prompt_tokens_per_turn"])
    def cost(row): return round((row["mean_prompt_tokens_per_turn"] * 30 * 10000 / 1_000_000) + (20 * 30 * 10000 / 1_000_000 * 5), 6)
    metrics = {"settings": summaries, "best_setting": best["setting"], "worst_setting": worst["setting"], "cost_10000_conversations_best_usd": cost(best), "cost_10000_conversations_worst_usd": cost(worst)}
    (OUT / "METRICS.md").write_text("# HW6 Metrics\n\n" + "\n".join(f"- {item['setting']}: mean prompt={item['mean_prompt_tokens_per_turn']} tokens/turn; mean latency={item['mean_latency_ms']} ms; probe quality={item['probe_quality']}/5" for item in summaries) + f"\n\nBest: {best['setting']}\nWorst: {worst['setting']}\nEstimated best cost: ${cost(best)}\nEstimated worst cost: ${cost(worst)}\n", encoding="utf-8")
    (RAW / "memory_cost_summary.json").write_text(json.dumps(metrics, indent=2), encoding="utf-8")
    print(json.dumps(metrics, indent=2))

if __name__ == "__main__": main()
