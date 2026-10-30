"""Fixed HW8 configuration derived from SID4 7085."""

SID4 = 7085
PORT_BASE = 8085
PREFIX = "s7085"
SEED = 7085
VERIFY_SEED = 267085
DOMAIN_ID = 5
KAFKA_BOOTSTRAP_SERVERS = "localhost:9092"
ENTITY_REQUESTS = f"{PREFIX}_entity_requests"
ENTITY_RESPONSES = f"{PREFIX}_entity_responses"
INBOX = f"{PREFIX}_inbox"
TASKS = f"{PREFIX}_tasks"
DRAFTS = f"{PREFIX}_drafts"
FINAL = f"{PREFIX}_final"
DEAD_LETTER = f"{PREFIX}_dead_letter"
