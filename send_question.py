import uuid

from pipeline import KafkaPipeline


def send_question(question: str, pipeline: KafkaPipeline | None = None) -> dict:
    return (pipeline or KafkaPipeline()).run_once(question, str(uuid.uuid4()))


if __name__ == "__main__":
    print(send_question("Which restaurant inspections scored below 70?"))
