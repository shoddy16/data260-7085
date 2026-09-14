from typing import TypedDict
import argparse
import json

from pydantic import BaseModel, Field, field_validator
from langgraph.graph import StateGraph, START, END

try:
    from src.model_client import ModelClient
except ModuleNotFoundError:
    from model_client import ModelClient



class PlannerOutput(BaseModel):
    tags: list[str] = Field(min_length=3, max_length=3)
    summary: str

    @field_validator("tags")
    @classmethod
    def validate_tags(cls, tags):
        for tag in tags:
            if not isinstance(tag, str):
                raise ValueError("Each tag must be a string.")

            if len(tag) < 3 or len(tag) > 30:
                raise ValueError(
                    "Each tag must be between 3 and 30 characters."
                )

        return tags

    @field_validator("summary")
    @classmethod
    def validate_summary(cls, summary):
        if len(summary.split()) > 25:
            raise ValueError(
                "Summary must contain no more than 25 words."
            )

        return summary



class AgentState(TypedDict):
    title: str
    content: str
    task: str
    planner_proposal: dict
    reviewer_feedback: dict
    turn_count: int
    max_turns: int
    force_reviewer_failure: bool
    force_invalid_first: bool


def parse_json_response(raw_output: str) -> dict:
    text = raw_output.strip()

    if text.startswith("```"):
        lines = text.splitlines()

        if lines[0].startswith("```"):
            lines = lines[1:]

        if lines and lines[-1].strip() == "```":
            lines = lines[:-1]

        text = "\n".join(lines).strip()

    try:
        return json.loads(text)

    except json.JSONDecodeError:
        start = text.find("{")
        end = text.rfind("}")

        if start != -1 and end != -1:
            return json.loads(text[start:end + 1])

        raise


def planner_node(state: AgentState) -> dict:

    
    if (
        state.get("force_invalid_first", False)
        and state.get("turn_count", 0) == 0
    ):
        return {
            "planner_proposal": {
                "tags": ["x", "y"],
                "summary": (
                    "This is an intentionally invalid Planner output "
                    "with too many words so Pydantic validation will "
                    "fail and the graph will retry the Planner."
                ),
            },
            "reviewer_feedback": {},
            "force_invalid_first": False,
        }

    client = ModelClient()

    previous_feedback = state.get("reviewer_feedback", {})
    feedback_text = ""

    if previous_feedback:
        feedback_text = f"""
The previous Planner attempt had this reviewer feedback:

{json.dumps(previous_feedback, indent=2)}

Fix these problems in the new attempt.
"""

    prompt = f"""
You are the Planner agent for a local restaurant inspection application.

Title:
{state["title"]}

Content:
{state["content"]}

{feedback_text}

Create:
- exactly 3 topical tags
- each tag must be 3 to 30 characters
- a summary of no more than 25 words
- tags and summary must be based on the supplied input

Return ONLY one JSON object:

{{
  "tags": ["tag 1", "tag 2", "tag 3"],
  "summary": "short summary"
}}
"""

    response = client.complete(
        [
            (
                "system",
                "You are a careful Planner agent. Return valid JSON only."
            ),
            ("human", prompt),
        ]
    )

    raw_output = response.content

    try:
        raw_proposal = parse_json_response(raw_output)

        
        validated = PlannerOutput.model_validate(raw_proposal)

        proposal = validated.model_dump()

    except Exception as error:

        try:
            raw_proposal = parse_json_response(raw_output)

        except Exception:
            raw_proposal = {
                "tags": [],
                "summary": "",
            }

        proposal = {
            "tags": raw_proposal.get("tags", []),
            "summary": raw_proposal.get("summary", ""),
            "_validation_error": str(error),
        }

 
    return {
        "planner_proposal": proposal,
        "reviewer_feedback": {},
    }

def reviewer_node(state: AgentState) -> dict:

    proposal = state.get("planner_proposal", {})
    issues = []

 
    try:
        PlannerOutput.model_validate(proposal)

    except Exception as error:
        issues.append(
            "Pydantic validation failed: "
            + str(error)
        )

    if state.get("force_reviewer_failure", False):
        issues.append(
            "Temporary forced reviewer failure for graph loop demonstration."
        )

    approved = len(issues) == 0

    return {
        "reviewer_feedback": {
            "approved": approved,
            "issues": issues,
        }
    }


def supervisor_node(state: AgentState) -> dict:

    turn_count = state.get("turn_count", 0)

    
    if state.get("reviewer_feedback"):
        turn_count += 1

    return {
        "turn_count": turn_count,
    }

def router_logic(state: AgentState) -> str:

    planner_proposal = state.get("planner_proposal", {})
    reviewer_feedback = state.get("reviewer_feedback", {})

    turn_count = state.get("turn_count", 0)
    max_turns = state.get("max_turns", 10)


    if not planner_proposal:
        return "planner"

  
    if not reviewer_feedback:
        return "reviewer"

    if reviewer_feedback.get("approved", False):
        return END

    if turn_count >= max_turns:
        return END

  
    return "planner"



def build_graph():

    graph = StateGraph(AgentState)

    graph.add_node("supervisor", supervisor_node)
    graph.add_node("planner", planner_node)
    graph.add_node("reviewer", reviewer_node)

    graph.add_edge(START, "supervisor")

    graph.add_conditional_edges(
        "supervisor",
        router_logic,
        {
            "planner": "planner",
            "reviewer": "reviewer",
            END: END,
        },
    )

    graph.add_edge("planner", "supervisor")
    graph.add_edge("reviewer", "supervisor")

    return graph.compile()




def run_demo(
    title: str,
    content: str,
    max_turns: int = 10,
    force_reviewer_failure: bool = False,
    force_invalid_first: bool = False,
):

    graph = build_graph()

    initial_state: AgentState = {
        "title": title,
        "content": content,
        "task": "Create three topical tags and a short summary.",
        "planner_proposal": {},
        "reviewer_feedback": {},
        "turn_count": 0,
        "max_turns": max_turns,
        "force_reviewer_failure": force_reviewer_failure,
        "force_invalid_first": force_invalid_first,
    }

    print("\n========== LANGGRAPH STREAM ==========")

    for step in graph.stream(initial_state):

        print("\n--- GRAPH STEP ---")

        print(
            json.dumps(
                step,
                indent=2,
                default=str,
            )
        )

    print("\n========== GRAPH COMPLETE ==========")


def main():

    parser = argparse.ArgumentParser()

    parser.add_argument(
        "--title",
        default="Local Restaurant Inspection",
    )

    parser.add_argument(
        "--content",
        default=(
            "A local restaurant inspection checked kitchen conditions, "
            "food safety practices, sanitation, and compliance with "
            "restaurant inspection requirements."
        ),
    )

    parser.add_argument(
        "--max-turns",
        type=int,
        default=10,
    )

    parser.add_argument(
        "--force-reviewer-failure",
        action="store_true",
    )

    parser.add_argument(
        "--force-invalid-first",
        action="store_true",
    )

    args = parser.parse_args()

    run_demo(
        title=args.title,
        content=args.content,
        max_turns=args.max_turns,
        force_reviewer_failure=args.force_reviewer_failure,
        force_invalid_first=args.force_invalid_first,
    )


if __name__ == "__main__":
    main()