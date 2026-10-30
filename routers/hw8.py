from fastapi import APIRouter

from kafka_rpc import KafkaRPC

router = APIRouter(prefix="/hw8", tags=["hw8-kafka"])
rpc = KafkaRPC()


@router.get("/health")
async def health():
    return {"status": "ok", "service": "hw8-kafka-rpc"}


@router.post("/entity")
async def entity_operation(payload: dict):
    return await rpc.request(payload.get("operation", ""), payload.get("data", {}))
