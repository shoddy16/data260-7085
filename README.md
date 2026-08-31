# DATA 260 Homework 1

Repository: `data260-7085`

## Configuration

- SID4: 7085
- PORT_BASE: 8785
- PREFIX: s7085
- SEED: 7085
- VERIFY_SEED: 267085
- DOMAIN_ID: 5
- Domain: Local restaurant inspections
- Python: 3.12
- Local model: `llama3.2:3b`

## Environment Setup

Create and activate the virtual environment:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1


Install the Python dependencies:

pip install langchain-ollama langchain-core

Make sure Ollama is running and the model is available:

ollama list

The project uses the local Ollama server at:

http://localhost:11434

Part 1 — Web Application

Main files:

index.html
script.js
DOMAIN_SCHEMA.md

The application can also be built and run using the included Dockerfile.

Part 2 — Agentic AI

The agent pipeline is implemented in:

agent_demo.py

It uses a Planner → Reviewer → Finalizer flow and produces three topical
tags and a summary of no more than 25 words.

Example:

python agent_demo.py --title "Restaurant Inspection Report" --content "A local restaurant inspection evaluates food safety, sanitation, hygiene, and compliance with public health requirements."
Part 3 — Non-Determinism

The fixed input is:

reports/hw01/cases/nondeterminism_input.json

The experiment runs the same input 20 times at temperature 0.7 and
20 times at temperature 0.0.

Run it with:

python run_experiment.py

Raw results are saved in:

reports/hw01/raw/

The results and analysis are documented in:

reports/hw01/METRICS.md
Part 4 — Model Client

The reusable model adapter is:

src/model_client.py

The command-line client is:

hw1_client.py

Test a basic model call:

python hw1_client.py --message "Reply with one short sentence explaining what a restaurant inspection is."

Test the AGENT.md code review:

python hw1_client.py --message "Review this code for correctness and maintainability." --file review_sample.py

For the interactive client:

python hw1_client.py

During the conversation, /stats shows the current turn count,
cumulative token counts, and serialized conversation-history length.

Use /exit to finish and display the final totals.

Verification

Run the HW1 self-check:

python verify_hw1.py

The result is saved to:

reports/hw01/verification.json

The current self-check passes all 26 checks.

HW1 Files

The main HW1 artifacts are in:

reports/hw01/

including:

RUN_LOG.txt
METRICS.md
AI_USE.md
verification.json
report.pdf

Raw experiment data is under:

reports/hw01/raw/
Part 4 — Conceptual Questions
Why is prior conversation context resent with every turn?

The model needs the previous messages to understand what has already been
discussed. The client therefore sends the conversation history with each
new request.

How is a system prompt different from a user message?

A system prompt gives the model instructions about its behavior, while a
user message contains the actual request or task.

Why do input tokens grow over a conversation?

Previous user and assistant messages are included in later requests, so
the amount of input context increases as the conversation continues.

What eventually limits that growth?

The model's context window limits how much conversation history can be
included in a request.

Reproducibility

Run all commands from the repository root with the virtual environment
activated. Ollama must be running locally with the selected model available.

The fixed experiment input and raw results are preserved in
reports/hw01/ so the reported results can be checked against the original
runs.