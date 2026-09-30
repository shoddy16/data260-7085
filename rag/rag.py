import os
import sys
import re
import shutil
import torch
import chromadb
from transformers import AutoTokenizer, AutoModel
import fitz

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DOCS_DIR = os.path.join(BASE_DIR, "rag_docs")
CHROMA_DIR = os.path.join(BASE_DIR, "chroma_db")

MODEL_NAME = "sentence-transformers/all-MiniLM-L6-v2"
COLLECTION_NAME = "hw4_rag"

CHUNK_SIZE = 500
CHUNK_OVERLAP = 50
BATCH_SIZE = 16

PDF_FILES = [
    "Week 1. Data System Overview.pdf",
    "Week 2. Data Warehouse Overview.pdf",
    "Week 3 Data Warehouse Development (S...).pdf",
    "Week 4 Advanced SQL.pdf",
    "Week 5 Data Pipelines (1).pdf",
]


class Embedder:
    def __init__(self):
        print("Loading tokenizer...")
        self.tokenizer = AutoTokenizer.from_pretrained(MODEL_NAME)

        print("Loading model...")
        self.model = AutoModel.from_pretrained(MODEL_NAME)

        self.model.eval()

        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        self.model.to(self.device)

    def encode(self, texts):
        texts = [str(x).strip() for x in texts]

        valid_texts = []
        valid_indexes = []

        for i, text in enumerate(texts):
            if text:
                valid_texts.append(text)
                valid_indexes.append(i)

        if not valid_texts:
            return []

        all_embeddings = []

        with torch.no_grad():
            for start in range(0, len(valid_texts), BATCH_SIZE):
                batch = valid_texts[start:start + BATCH_SIZE]

                inputs = self.tokenizer(
                    batch,
                    padding=True,
                    truncation=True,
                    max_length=512,
                    return_tensors="pt"
                )

                inputs = {
                    key: value.to(self.device)
                    for key, value in inputs.items()
                }

                outputs = self.model(**inputs)

                token_embeddings = outputs.last_hidden_state
                attention_mask = inputs["attention_mask"]

                mask = attention_mask.unsqueeze(-1).expand(
                    token_embeddings.size()
                ).float()

                summed = torch.sum(token_embeddings * mask, dim=1)
                counts = torch.clamp(mask.sum(dim=1), min=1e-9)

                embeddings = summed / counts

                embeddings = torch.nn.functional.normalize(
                    embeddings,
                    p=2,
                    dim=1
                )

                all_embeddings.extend(
                    embeddings.cpu().tolist()
                )

        result = [None] * len(texts)

        for embedding, index in zip(all_embeddings, valid_indexes):
            result[index] = embedding

        return result

    def encode_one(self, text):
        return self.encode([str(text)])[0]


def clean_text(text):
    text = text.replace("\x00", " ")
    text = re.sub(r"\s+", " ", text)
    return text.strip()


def extract_pdf_text(path):
    document = fitz.open(path)

    pages = []

    for page in document:
        text = page.get_text("text")

        if text:
            pages.append(text)

    document.close()

    return clean_text("\n".join(pages))


def chunk_text(text):
    words = text.split()

    chunks = []

    start = 0

    while start < len(words):
        end = min(start + CHUNK_SIZE, len(words))

        chunk = " ".join(words[start:end]).strip()

        if chunk:
            chunks.append(chunk)

        if end >= len(words):
            break

        start = end - CHUNK_OVERLAP

    return chunks


def get_pdf_files():
    files = []

    for filename in sorted(os.listdir(DOCS_DIR)):
        if filename.lower().endswith(".pdf"):
            files.append(os.path.join(DOCS_DIR, filename))

    return files

def build_index(embedder):
    print("Building Chroma index...")

    if os.path.exists(CHROMA_DIR):
        shutil.rmtree(CHROMA_DIR)

    client = chromadb.PersistentClient(
        path=CHROMA_DIR
    )

    collection = client.get_or_create_collection(
        name=COLLECTION_NAME,
        metadata={"hnsw:space": "cosine"}
    )

    pdf_files = get_pdf_files()

    if not pdf_files:
        raise RuntimeError(
            "No PDFs found in rag_docs."
        )

    total_chunks = 0

    for pdf_path in pdf_files:
        filename = os.path.basename(pdf_path)

        print(f"Processing: {filename}")

        text = extract_pdf_text(pdf_path)

        chunks = chunk_text(text)

        print(f"Chunks: {len(chunks)}")

        if not chunks:
            continue

        embeddings = embedder.encode(chunks)

        ids = []
        documents = []
        metadatas = []
        valid_embeddings = []

        for i, (chunk, embedding) in enumerate(
            zip(chunks, embeddings)
        ):
            if embedding is None:
                continue

            chunk_id = f"{filename}_{i}"

            ids.append(chunk_id)
            documents.append(chunk)

            metadatas.append({
                "source": filename,
                "chunk_id": i
            })

            valid_embeddings.append(embedding)

        collection.add(
            ids=ids,
            documents=documents,
            embeddings=valid_embeddings,
            metadatas=metadatas
        )

        total_chunks += len(documents)

        print(f"Indexed: {len(documents)}")

    print()
    print("INDEX COMPLETE")
    print("------------------------------")
    print(f"Documents: {len(pdf_files)}")
    print(f"Total chunks: {total_chunks}")
    print(f"Chunk size: {CHUNK_SIZE}")
    print(f"Chunk overlap: {CHUNK_OVERLAP}")
    print(f"Vector store: Chroma")
    print(f"Collection: {COLLECTION_NAME}")
    print(f"Embedding model: {MODEL_NAME}")
    print("------------------------------")

    return collection


def load_collection():
    client = chromadb.PersistentClient(
        path=CHROMA_DIR
    )

    return client.get_collection(
        name=COLLECTION_NAME
    )


def query_index(embedder, question, top_k=5):
    collection = load_collection()

    embedding = embedder.encode_one(question)

    results = collection.query(
        query_embeddings=[embedding],
        n_results=top_k
    )

    documents = results.get("documents", [[]])[0]
    metadatas = results.get("metadatas", [[]])[0]
    distances = results.get("distances", [[]])[0]

    print()
    print("QUERY")
    print("------------------------------")
    print(question)
    print()
    print("RESULTS")
    print("------------------------------")

    for i, document in enumerate(documents):
        metadata = metadatas[i]
        distance = distances[i]

        print()
        print(f"Result {i + 1}")
        print(f"Source: {metadata['source']}")
        print(f"Chunk: {metadata['chunk_id']}")
        print(f"Distance: {distance}")
        print(document[:1000])

    return results


def main():
    if len(sys.argv) < 2:
        print("Use:")
        print("python rag/rag.py index")
        print('python rag/rag.py query "your question"')
        return

    command = sys.argv[1]

    embedder = Embedder()

    if command == "index":
        build_index(embedder)

    elif command == "query":
        if len(sys.argv) < 3:
            print('Use: python rag/rag.py query "your question"')
            return

        question = " ".join(sys.argv[2:])

        query_index(
            embedder,
            question
        )

    else:
        print("Unknown command.")
        print("Use:")
        print("python rag/rag.py index")
        print('python rag/rag.py query "your question"')


if __name__ == "__main__":
    main()