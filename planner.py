from hw8_config import INBOX, TASKS
from kafka_runtime import run_stage
from pipeline import KafkaPipeline


def process(question: str, correlation_id: str, pipeline: KafkaPipeline) -> dict:
    return pipeline.run_once(question, correlation_id)


if __name__ == "__main__":
    import asyncio

    asyncio.run(run_stage("planner", INBOX, TASKS))
