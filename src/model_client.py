import os
from typing import Any

from langchain_ollama import ChatOllama


class ModelClient:
    """
    Reusable adapter for the local Ollama model.

    All model calls for Part 4 should go through complete().
    """

    def __init__(
        self,
        model: str | None = None,
        base_url: str | None = None,
        temperature: float = 0.0,
    ):
        self.model_name = model or os.environ.get(
            "OLLAMA_MODEL",
            "llama3.2:3b",
        )

        self.base_url = base_url or os.environ.get(
            "OLLAMA_URL",
            "http://localhost:11434",
        )

        self.temperature = temperature

        self.llm = ChatOllama(
            model=self.model_name,
            temperature=self.temperature,
            base_url=self.base_url,
        )

    def complete(
        self,
        messages: list[Any],
        tools: list[Any] | None = None,
    ) -> Any:
        """
        Send a conversation to the local model.

        The optional tools argument is accepted so the adapter
        has a stable interface for future tool-enabled calls.
        """

        if tools:
            model = self.llm.bind_tools(tools)
        else:
            model = self.llm

        return model.invoke(messages)