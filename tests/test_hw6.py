import unittest
from pathlib import Path

from hw6_memory import ChatRequest, DeterministicChatModel, InMemoryStore, assemble_prompt, chat_turn, local_embedding, retrieve_episodes
from file_memory import consolidate_memory, handle_command


class MemoryTests(unittest.TestCase):
    def test_chat_persists_window_episode_and_summary(self):
        store = InMemoryStore()
        for index in range(5):
            result = chat_turn(ChatRequest(user_id="u", session_id="s", message=f"Restaurant fact {index}"), store, DeterministicChatModel(), short_term_n=4, summarize_every=5)
        self.assertEqual(len(store.messages("u", "s")), 10)
        self.assertEqual(len(result["used"]["short_term"]), 4)
        self.assertEqual(len(store.summaries("u", "session")), 1)
        self.assertEqual(len(store.episodes("u")), 5)

    def test_embedding_retrieval_is_ranked(self):
        store = InMemoryStore()
        store.add_episode({"user_id": "u", "fact": "restaurant inspection sanitation", "embedding": local_embedding("restaurant inspection sanitation")})
        store.add_episode({"user_id": "u", "fact": "weather forecast", "embedding": local_embedding("weather forecast")})
        self.assertEqual(retrieve_episodes(store, "u", "restaurant inspection", 1)[0]["fact"], "restaurant inspection sanitation")

    def test_prompt_contains_all_memory_layers(self):
        prompt = assemble_prompt("current", "session", "lifetime", [{"role": "user", "content": "recent"}], [{"fact": "episode"}])
        for value in ("session", "lifetime", "recent", "episode", "current"):
            self.assertIn(value, prompt)


class FileMemoryTests(unittest.TestCase):
    def test_compaction_merges_duplicates_and_reports_contradictions(self):
        directory = Path(__file__).resolve().parents[1] / "reports" / "hw06"
        path = directory / "test_MEMORY.md"
        try:
            path.write_text("\n".join(["# Memory", "- Uses MySQL", "- Uses MongoDB", "- Uses MongoDB", "- Domain is restaurants"] * 12), encoding="utf-8")
            result = consolidate_memory(path)
            self.assertLess(result["after"], result["before"])
            self.assertTrue(result["contradictions_reviewed"])
            self.assertIn("Resolved contradictions", path.read_text(encoding="utf-8"))
        finally:
            path.unlink(missing_ok=True)

    def test_commands_are_explicit(self):
        directory = Path(__file__).resolve().parents[1] / "reports" / "hw06"
        agent = directory / "test_AGENT.md"; memory = directory / "test_MEMORY.md"
        try:
            agent.write_text("# Instructions\n- Use tests\n", encoding="utf-8"); memory.write_text("# Memory\n- One fact\n", encoding="utf-8")
            self.assertIn("Use tests", handle_command("/memory", agent_path=agent, memory_path=memory))
            self.assertIn("/compact", handle_command("/help", agent_path=agent, memory_path=memory))
            self.assertIn("before=", handle_command("/compact", agent_path=agent, memory_path=memory))
        finally:
            agent.unlink(missing_ok=True); memory.unlink(missing_ok=True)


if __name__ == "__main__": unittest.main()
