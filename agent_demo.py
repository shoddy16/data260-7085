import argparse
import json
import os

from langchain_ollama import ChatOllama
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser


def call_agent(model, system_prompt, task, history=""):
    prompt = ChatPromptTemplate.from_messages([
        ("system", "{system_prompt}"),
        (
            "human",
            """
Task:
{task}

Conversation so far:
{history}

Return ONLY one valid JSON object.
Do not use markdown or code fences.
"""
        ),
    ])

    chain = prompt | model | StrOutputParser()

    raw = chain.invoke({
        "system_prompt": system_prompt,
        "task": task,
        "history": history,
    })

    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        print("WARNING: Model returned invalid JSON:")
        print(raw)
        raise


def main():
    parser = argparse.ArgumentParser()

    parser.add_argument("--title", required=True)
    parser.add_argument("--content", required=True)
    parser.add_argument(
        "--model",
        default=os.environ.get("OLLAMA_MODEL", "llama3.2:3b")
    )
    parser.add_argument(
        "--temperature",
        type=float,
        default=0.0
    )

    args = parser.parse_args()

    # Connect to the local Ollama model
    model = ChatOllama(
        model=args.model,
        temperature=args.temperature,
        base_url="http://localhost:11434",
        format="json",
    )

    task = f"""
Given this title:

{args.title}

And this content:

{args.content}

Produce exactly 3 topical tags and a summary of no more than 25 words.
The tags and summary must be derived from the supplied title and content.
"""

    # =========================
    # PLANNER
    # =========================

    planner_prompt = """
You are the Planner agent.

Analyze the supplied title and content.

Create:
- exactly 3 topical tags
- a concise summary of no more than 25 words

The tags must be specific to the input.
Do not use generic tags such as "article", "information", or "content".

Return this JSON structure:

{
  "tags": ["tag 1", "tag 2", "tag 3"],
  "summary": "summary"
}
"""

    planner = call_agent(
        model,
        planner_prompt,
        task
    )

    print("\n========== PLANNER OUTPUT ==========")
    print(json.dumps(planner, indent=2))

    # =========================
    # REVIEWER
    # =========================

    reviewer_prompt = """
You are the Reviewer agent.

Review the Planner's proposed tags and summary.

Check:
1. There are exactly 3 tags.
2. The tags are topical and derived from the input.
3. The summary is no more than 25 words.
4. The summary accurately represents the input.
5. Avoid generic or irrelevant tags.

Return JSON:

{
  "approved": true,
  "tags": ["tag 1", "tag 2", "tag 3"],
  "summary": "summary",
  "issues": []
}

If something is wrong, correct it and explain the issue in "issues".
"""

    reviewer_history = json.dumps(planner)

    reviewer = call_agent(
        model,
        reviewer_prompt,
        task,
        reviewer_history
    )

    print("\n========== REVIEWER OUTPUT ==========")
    print(json.dumps(reviewer, indent=2))

    # =========================
    # FINALIZER
    # =========================

    finalizer_prompt = """
You are the Finalizer agent.

Use the original input and the Reviewer's result.

Produce the final publication output.

Requirements:
- exactly 3 topical tags
- summary of no more than 25 words
- tags must be derived from the input
- summary must accurately describe the input

Return ONLY:

{
  "tags": ["tag 1", "tag 2", "tag 3"],
  "summary": "summary"
}
"""

    finalizer_history = json.dumps({
        "planner": planner,
        "reviewer": reviewer,
    })

    final = call_agent(
        model,
        finalizer_prompt,
        task,
        finalizer_history
    )

    print("\n========== FINALIZED OUTPUT ==========")
    print(json.dumps(final, indent=2))


if __name__ == "__main__":
    main()