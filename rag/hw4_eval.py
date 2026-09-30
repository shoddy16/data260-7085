import os
import sys
import json
import urllib.request
import urllib.error
from datetime import datetime

from rag.rag import (
    Embedder,
    load_collection,
)


# ============================================================
# CONFIGURATION
# ============================================================

OLLAMA_URL = "http://localhost:11434/api/generate"
OLLAMA_MODEL = "llama3.2:3b"

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RAW_DIR = os.path.join(BASE_DIR, "reports", "hw04", "raw")

DEFAULT_K = 3


# ============================================================
# TEST QUESTIONS
# ============================================================

QUESTIONS = {
    "Q1": {
        "question": "What is Snowflake?",
        "type": "single-chunk",
        "expected_behavior": "answer",
    },

    "Q2": {
        "question": "How does Snowflake separate storage and compute, and what are virtual warehouses?",
        "type": "multi-chunk",
        "expected_behavior": "answer",
    },

    "Q3": {
        "question": "How is Snowflake used in data warehousing and data pipelines?",
        "type": "cross-document",
        "expected_behavior": "answer",
    },

    "Q4": {
        "question": "What does a warehouse mean in this course?",
        "type": "ambiguous",
        "expected_behavior": "answer-or-clarify",
    },

    "Q5": {
        "question": "What is the professor's favorite programming language?",
        "type": "unanswerable",
        "expected_behavior": "refuse",
    },

    "Q6": {
        "question": "What is the weather in San Jose today?",
        "type": "unrelated",
        "expected_behavior": "refuse",
    },
}


# ============================================================
# OUTPUT HELPERS
# ============================================================

def ensure_raw_dir():
    os.makedirs(RAW_DIR, exist_ok=True)


def save_text(filename, text):
    ensure_raw_dir()

    path = os.path.join(RAW_DIR, filename)

    with open(path, "w", encoding="utf-8") as f:
        f.write(text)

    return path


# ============================================================
# OLLAMA
# ============================================================

def ollama_generate(prompt):
    payload = {
        "model": OLLAMA_MODEL,
        "prompt": prompt,
        "stream": False,
        "options": {
            "temperature": 0,
            "num_predict": 256
        },
        "keep_alive": "5m"
    }

    data = json.dumps(payload).encode("utf-8")

    request = urllib.request.Request(
        OLLAMA_URL,
        data=data,
        headers={
            "Content-Type": "application/json"
        },
        method="POST"
    )

    print("Generating with Ollama...")

    try:
        with urllib.request.urlopen(request, timeout=600) as response:
            result = json.loads(
                response.read().decode("utf-8")
            )

        answer = result.get("response", "").strip()

        if not answer:
            return "[Ollama returned an empty response.]"

        return answer

    except urllib.error.URLError as e:
        raise RuntimeError(
            "Could not connect to Ollama at "
            f"{OLLAMA_URL}\n"
            "Make sure Ollama is running."
        ) from e


# ============================================================
# RETRIEVAL
# ============================================================

def retrieve(embedder, collection, question, k):
    embedding = embedder.encode_one(question)

    results = collection.query(
        query_embeddings=[embedding],
        n_results=k
    )

    documents = results.get("documents", [[]])[0]
    metadatas = results.get("metadatas", [[]])[0]
    distances = results.get("distances", [[]])[0]

    retrieved = []

    for i in range(len(documents)):
        retrieved.append({
            "rank": i + 1,
            "text": documents[i],
            "source": metadatas[i].get("source", "unknown"),
            "chunk": metadatas[i].get("chunk_id", "unknown"),
            "distance": distances[i]
        })

    return retrieved


# ============================================================
# PRINT RETRIEVAL
# ============================================================

def print_retrieval(question, retrieved, k):
    print()
    print("=" * 80)
    print(f"RETRIEVAL | k={k}")
    print("=" * 80)
    print(f"QUESTION: {question}")

    for item in retrieved:
        print()
        print(f"Result {item['rank']}")
        print(f"Source: {item['source']}")
        print(f"Chunk: {item['chunk']}")
        print(f"Distance: {item['distance']}")
        print("-" * 80)
        print(item["text"])


# ============================================================
# NO RAG
# ============================================================

def no_rag(question):
    prompt = f"""
You are answering a question without access to course documents.

Question:
{question}

Answer the question as accurately as you can.
Do not claim that you saw course documents.
"""

    return ollama_generate(prompt)


# ============================================================
# BASIC RAG
# ============================================================

def basic_rag(question, retrieved):
    context_parts = []

    for item in retrieved:
        context_parts.append(
            f"""
SOURCE: {item['source']}
CHUNK: {item['chunk']}

{item['text']}
"""
        )

    context = "\n".join(context_parts)

    prompt = f"""
You are answering a question using retrieved course-document context.

Question:
{question}

Retrieved context:
{context}

Use the retrieved context to answer the question.
If the answer is not present in the retrieved context, say that the
information is not available in the retrieved context.
"""

    return ollama_generate(prompt)


# ============================================================
# CONTEXT-ENGINEERED RAG
# ============================================================

def remove_duplicate_chunks(retrieved):
    seen = set()
    cleaned = []

    for item in retrieved:
        text_key = " ".join(item["text"].lower().split())

        if text_key in seen:
            continue

        seen.add(text_key)
        cleaned.append(item)

    return cleaned


def build_context(retrieved):
    retrieved = remove_duplicate_chunks(retrieved)

    parts = []

    for number, item in enumerate(retrieved, start=1):
        parts.append(
            f"""
[Source {number}]
Document: {item['source']}
Chunk: {item['chunk']}

{item['text']}
"""
        )

    return "\n".join(parts)


def context_rag(question, retrieved):
    context = build_context(retrieved)

    prompt = f"""
You are a course-document question answering system.

You MUST follow these rules:

1. Answer ONLY using the supplied course-document context.
2. Do not use outside knowledge.
3. Do not invent facts.
4. Cite the source number(s) used in your answer.
5. If the supplied documents do not contain enough information to
   answer the question, respond EXACTLY with:

I cannot answer this question from the provided documents

6. Keep the answer concise and directly related to the question.

COURSE DOCUMENT CONTEXT
=======================

{context}

QUESTION
========

{question}

ANSWER:
"""

    return ollama_generate(prompt)


# ============================================================
# SINGLE EXPERIMENT
# ============================================================

def run_question(embedder, collection, qid, qdata, k):
    question = qdata["question"]

    print()
    print("#" * 90)
    print(f"{qid} | {qdata['type']} | k={k}")
    print("#" * 90)
    print(f"Question: {question}")

    retrieved = retrieve(
        embedder,
        collection,
        question,
        k
    )

    # --------------------------------------------------------
    # Retrieval evidence
    # --------------------------------------------------------

    print_retrieval(
        question,
        retrieved,
        k
    )

    # --------------------------------------------------------
    # No RAG
    # --------------------------------------------------------

    print()
    print("-" * 80)
    print("NO RAG")
    print("-" * 80)

    no_rag_answer = no_rag(question)

    print(no_rag_answer)

    # --------------------------------------------------------
    # Basic RAG
    # --------------------------------------------------------

    print()
    print("-" * 80)
    print("BASIC RAG")
    print("-" * 80)

    basic_answer = basic_rag(
        question,
        retrieved
    )

    print(basic_answer)

    # --------------------------------------------------------
    # Context engineered RAG
    # --------------------------------------------------------

    print()
    print("-" * 80)
    print("CONTEXT-ENGINEERED RAG")
    print("-" * 80)

    context_answer = context_rag(
        question,
        retrieved
    )

    print(context_answer)

    return {
        "question_id": qid,
        "question": question,
        "type": qdata["type"],
        "expected_behavior": qdata["expected_behavior"],
        "k": k,
        "retrieval": retrieved,
        "no_rag": no_rag_answer,
        "basic_rag": basic_answer,
        "context_rag": context_answer,
    }


# ============================================================
# RUN ALL QUESTIONS
# ============================================================

def run_all(embedder, collection, k=DEFAULT_K):
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

    all_results = []

    for qid, qdata in QUESTIONS.items():
        result = run_question(
            embedder,
            collection,
            qid,
            qdata,
            k
        )

        all_results.append(result)

    output = {
        "timestamp": timestamp,
        "model": OLLAMA_MODEL,
        "k": k,
        "results": all_results
    }

    ensure_raw_dir()

    json_path = os.path.join(
        RAW_DIR,
        f"hw4_results_k{k}_{timestamp}.json"
    )

    with open(
        json_path,
        "w",
        encoding="utf-8"
    ) as f:
        json.dump(
            output,
            f,
            indent=2,
            ensure_ascii=False
        )

    print()
    print("=" * 90)
    print("EXPERIMENT COMPLETE")
    print("=" * 90)
    print(f"Saved JSON: {json_path}")

    return all_results


# ============================================================
# K SWEEP
# ============================================================

def run_k_sweep(embedder, collection):
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

    sweep_results = []

    # Use Q1 for the required k comparison.
    qid = "Q1"
    qdata = QUESTIONS[qid]
    question = qdata["question"]

    print()
    print("=" * 90)
    print("K SWEEP")
    print("=" * 90)
    print(f"Question: {question}")

    for k in [1, 3, 5]:
        print()
        print("#" * 90)
        print(f"k = {k}")
        print("#" * 90)

        retrieved = retrieve(
            embedder,
            collection,
            question,
            k
        )

        print_retrieval(
            question,
            retrieved,
            k
        )

        answer = context_rag(
            question,
            retrieved
        )

        print()
        print("CONTEXT-RAG ANSWER")
        print("-" * 80)
        print(answer)

        sweep_results.append({
            "question": question,
            "k": k,
            "retrieval": retrieved,
            "answer": answer
        })

    output = {
        "timestamp": timestamp,
        "question": question,
        "model": OLLAMA_MODEL,
        "results": sweep_results
    }

    ensure_raw_dir()

    path = os.path.join(
        RAW_DIR,
        f"k_sweep_{timestamp}.json"
    )

    with open(
        path,
        "w",
        encoding="utf-8"
    ) as f:
        json.dump(
            output,
            f,
            indent=2,
            ensure_ascii=False
        )

    print()
    print("=" * 90)
    print("K SWEEP COMPLETE")
    print("=" * 90)
    print(f"Saved: {path}")


# ============================================================
# MAIN
# ============================================================

def main():
    if len(sys.argv) < 2:
        print()
        print("HW4 Evaluation")
        print("------------------------------")
        print("Run all Q1-Q6:")
        print("python rag/hw4_eval.py run")
        print()
        print("Run k=1,3,5 sweep:")
        print("python rag/hw4_eval.py sweep")
        print()
        print("Run one question:")
        print('python rag/hw4_eval.py q Q1')
        return

    command = sys.argv[1]

    print()
    print("STARTING HW4 EVALUATION")
    print("------------------------------")
    print(f"Ollama model: {OLLAMA_MODEL}")

    print()
    print("Loading embedding model...")

    embedder = Embedder()

    print()
    print("Loading existing Chroma index...")

    collection = load_collection()

    print("Existing Chroma index loaded.")
    print(f"Collection count: {collection.count()}")

    if command == "run":

        run_all(
            embedder,
            collection,
            k=DEFAULT_K
        )

    elif command == "sweep":

        run_k_sweep(
            embedder,
            collection
        )

    elif command == "q":

        if len(sys.argv) < 3:
            print("Missing question ID.")
            print("Example: python rag/hw4_eval.py q Q1")
            return

        qid = sys.argv[2].upper()

        if qid not in QUESTIONS:
            print(f"Unknown question: {qid}")
            print("Available questions:")
            print(", ".join(QUESTIONS.keys()))
            return

        result = run_question(
            embedder,
            collection,
            qid,
            QUESTIONS[qid],
            DEFAULT_K
        )

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

        path = os.path.join(
            RAW_DIR,
            f"{qid}_{timestamp}.json"
        )

        ensure_raw_dir()

        with open(
            path,
            "w",
            encoding="utf-8"
        ) as f:
            json.dump(
                result,
                f,
                indent=2,
                ensure_ascii=False
            )

        print()
        print(f"Saved: {path}")

    else:

        print(f"Unknown command: {command}")


if __name__ == "__main__":
    main()