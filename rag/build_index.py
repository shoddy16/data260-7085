from transformers import AutoTokenizer, AutoModel

MODEL_NAME = "sentence-transformers/all-MiniLM-L6-v2"

print("STARTING NEW FILE")

tokenizer = AutoTokenizer.from_pretrained(MODEL_NAME)
model = AutoModel.from_pretrained(MODEL_NAME)

text = "hello world"

encoded = tokenizer(
    text,
    return_tensors="pt",
    padding=True,
    truncation=True
)

print("TOKENIZER WORKS")
print(encoded["input_ids"])

with __import__("torch").no_grad():
    output = model(**encoded)

print("MODEL WORKS")
print(output.last_hidden_state.shape)