import argparse
import json
from pathlib import Path

from src.model_client import ModelClient


def get_usage(response):
    """
    Extract token usage from a LangChain response.
    """
    usage = getattr(response, "usage_metadata", None)

    if not usage:
        return {
            "input_tokens": 0,
            "output_tokens": 0,
            "total_tokens": 0,
        }

    return {
        "input_tokens": int(usage.get("input_tokens", 0)),
        "output_tokens": int(usage.get("output_tokens", 0)),
        "total_tokens": int(usage.get("total_tokens", 0)),
    }


def print_usage(usage):
    print("\n--- TOKEN USAGE ---")
    print(f"Input tokens:  {usage['input_tokens']}")
    print(f"Output tokens: {usage['output_tokens']}")
    print(f"Total tokens:  {usage['total_tokens']}")


def print_stats(history, turn_count, total_input, total_output):
    serialized_history = json.dumps(
        history,
        ensure_ascii=False,
    )

    print("\n========== /stats ==========")
    print(f"Turn count: {turn_count}")
    print(f"Cumulative input tokens: {total_input}")
    print(f"Cumulative output tokens: {total_output}")
    print(f"Serialized conversation-history length: {len(serialized_history)} characters")
    print("============================")


def run_review(client, file_path, message):
    agent_path = Path("AGENT.md")
    file_path = Path(file_path)

    if not agent_path.exists():
        raise FileNotFoundError("AGENT.md was not found.")

    if not file_path.exists():
        raise FileNotFoundError(
            f"Submitted file not found: {file_path}"
        )

    agent_instructions = agent_path.read_text(
        encoding="utf-8-sig"
    )

    submitted_code = file_path.read_text(
        encoding="utf-8-sig"
    )

    response = client.complete(
        [
            {
                "role": "system",
                "content": (
                    "You are a careful code reviewer. "
                    "Follow the supplied AGENT.md instructions exactly."
                ),
            },
            {
                "role": "user",
                "content": f"""
AGENT.md instructions:

{agent_instructions}

Submitted file: {file_path}

Submitted code:

{submitted_code}

Task:

{message}

Follow AGENT.md exactly.
Review ONLY the submitted file.
Return bullet points only.
""",
            },
        ]
    )

    usage = get_usage(response)

    print(response.content)
    print_usage(usage)


def interactive_chat(client):
    history = []

    turn_count = 0
    cumulative_input = 0
    cumulative_output = 0

    print("\n========== HW1 CLIENT ==========")
    print(f"Model: {client.model_name}")
    print("Type /stats to view statistics.")
    print("Type /exit to quit.")
    print("================================")

    while True:
        try:
            user_input = input("\nYou: ")
        except (EOFError, KeyboardInterrupt):
            print("\nExiting...")
            break

        if user_input.strip().lower() == "/exit":
            break

        if user_input.strip().lower() == "/stats":
            print_stats(
                history,
                turn_count,
                cumulative_input,
                cumulative_output,
            )
            continue

        if not user_input.strip():
            continue

        history.append(
            {
                "role": "user",
                "content": user_input,
            }
        )

        response = client.complete(history)

        history.append(
            {
                "role": "assistant",
                "content": response.content,
            }
        )

        turn_count += 1

        usage = get_usage(response)

        cumulative_input += usage["input_tokens"]
        cumulative_output += usage["output_tokens"]

        print(f"\nAssistant: {response.content}")
        print_usage(usage)

    print("\n========== FINAL TOTALS ==========")
    print(f"Turn count: {turn_count}")
    print(f"Cumulative input tokens: {cumulative_input}")
    print(f"Cumulative output tokens: {cumulative_output}")
    print("==================================")


def main():
    parser = argparse.ArgumentParser(
        description="DATA 260 HW1 model client"
    )

    parser.add_argument(
        "--message",
        default=None,
        help="One-shot message to send to the model.",
    )

    parser.add_argument(
        "--model",
        default=None,
        help="Ollama model name.",
    )

    parser.add_argument(
        "--file",
        default=None,
        help="Optional file to review using AGENT.md.",
    )

    args = parser.parse_args()

    client = ModelClient(model=args.model)

    if args.file:
        message = args.message or (
            "Review this file for correctness and maintainability."
        )

        run_review(
            client,
            args.file,
            message,
        )

    elif args.message:
        response = client.complete(
            [
                {
                    "role": "user",
                    "content": args.message,
                }
            ]
        )

        print(
            json.dumps(
                {
                    "model": client.model_name,
                    "response": response.content,
                },
                indent=2,
            )
        )

        print_usage(get_usage(response))

    else:
        interactive_chat(client)


if __name__ == "__main__":
    main()