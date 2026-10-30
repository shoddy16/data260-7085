import asyncio
import json
import os
import uuid

from hw8_config import INBOX, KAFKA_BOOTSTRAP_SERVERS
from pipeline import KafkaPipeline


def send_question(question: str, pipeline: KafkaPipeline | None = None) -> dict:
    return (pipeline or KafkaPipeline()).run_once(question, str(uuid.uuid4()))


async def send_question_live(question: str) -> str:
    from aiokafka import AIOKafkaProducer

    correlation_id = str(uuid.uuid4())
    producer = AIOKafkaProducer(bootstrap_servers=os.getenv("KAFKA_BOOTSTRAP_SERVERS", KAFKA_BOOTSTRAP_SERVERS))
    await producer.start()
    try:
        message = {"correlation_id": correlation_id, "question": question}
        await producer.send_and_wait(INBOX, json.dumps(message).encode("utf-8"))
        print(json.dumps(message))
        return correlation_id
    finally:
        await producer.stop()


if __name__ == "__main__":
    if os.getenv("HW8_LIVE_KAFKA") == "1":
        asyncio.run(send_question_live("Which restaurant inspections scored below 70?"))
    else:
        print(send_question("Which restaurant inspections scored below 70?"))
